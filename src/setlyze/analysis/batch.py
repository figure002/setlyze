#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, 2011, GiMaRIS <info@gimaris.com>
#
#  This file is part of SETLyze - A tool for analyzing the settlement
#  of species on SETL plates.
#
#  SETLyze is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SETLyze is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This module performs existing analyses in batch.

The selected analysis is repeated for a selection of species. If all species
are selected by the user, the analysis is repeated for each species and the
results are displayed in a single report.
"""

import sys
import logging
import math
import threading
import time
from sqlite3 import dbapi2 as sqlite

import gobject
import pygtk
pygtk.require('2.0')
import gtk

import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.std
import setlyze.report
import setlyze.analysis.common
import setlyze.analysis.spot_preference

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/01/28"

class Begin(setlyze.analysis.common.PrepareAnalysis):
    """Make the preparations for batch analysis:

    1. Let the user select an analysis.
    2. Show a list of all localities and let the user perform a localities
       selection.
    3. Show a list of all species that match the locations selection and
       let the user perform a species selection.
    4. Run the analysis for all species in batch.
    5. Show the analysis report to the user.
    """

    def __init__(self):
        super(Begin, self).__init__()

        self.analysis = None

        # Create log message.
        logging.info("Beginning batch analysis")

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)
        setlyze.config.cfg.set('plate-areas-definition', None)

        # Emit the signal that we are beginning with an analysis.
        setlyze.std.sender.emit('beginning-analysis')

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            # This analysis has just started.
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_select_analysis),

            # The batch analysis selection window back button was clicked.
            'select-batch-analysis-window-back': setlyze.std.sender.connect('select-batch-analysis-window-back', self.on_analysis_closed),

            # The batch analysis was selected.
            'batch-analysis-selected': setlyze.std.sender.connect('batch-analysis-selected', self.on_analysis_selected),

            # The user pressed the X button of a locations/species
            # selection window.
            'selection-dialog-closed': setlyze.std.sender.connect('selection-dialog-closed', self.on_analysis_closed),

            # The user pressed the X button of a define spots window.
            'define-areas-dialog-closed': setlyze.std.sender.connect('define-areas-dialog-closed', self.on_analysis_closed),

            # User pressed the Back button in the locations selection window.
            'locations-dialog-back': setlyze.std.sender.connect('locations-dialog-back', self.on_select_analysis),

            # User pressed the Back button in the species selection window.
            'species-dialog-back': setlyze.std.sender.connect('species-dialog-back', self.on_select_locations),

            # User pressed the Back button in the define spots window.
            'define-areas-dialog-back': setlyze.std.sender.connect('define-areas-dialog-back', self.on_select_species),

            # The user selected locations have been saved.
            'locations-selection-saved': setlyze.std.sender.connect('locations-selection-saved', self.on_select_species),

            # The user selected species have been saved.
            'species-selection-saved': setlyze.std.sender.connect('species-selection-saved', self.on_define_plate_areas),

            # The spots have been defined by the user.
            'plate-areas-defined': setlyze.std.sender.connect('plate-areas-defined', self.on_start_analysis),

            # The report window was closed.
            'report-dialog-closed': setlyze.std.sender.connect('report-dialog-closed', self.on_analysis_closed),

            # The analysis was aborted.
            'analysis-aborted': setlyze.std.sender.connect('analysis-aborted', self.on_analysis_aborted),

            # Display the report after the analysis has finished.
            'analysis-finished': setlyze.std.sender.connect('analysis-finished', self.on_display_report),

            # Cancel button
            'analysis-canceled': setlyze.std.sender.connect('analysis-canceled', self.on_cancel_button),

            # Progress dialog closed
            'progress-dialog-closed': setlyze.std.sender.connect('progress-dialog-closed', self.on_analysis_closed),
        }

    def on_analysis_aborted(self, sender):
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="No species were found")
        dialog.format_secondary_text(setlyze.locale.text('empty-plate-areas'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def on_cancel_button(self, sender):
        """Callback function for the Cancel button.

        * Close the progress dialog.
        * Stop the worker progress.
        * Show an info dialog.
        * Show the main window.
        """
        # Destroy the progress dialog.
        if self.pdialog_handler:
            self.pdialog_handler.pdialog.destroy()

        # Stop all analysis threads.
        self.stop_all_threads()

        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis canceled")
        dialog.format_secondary_text(setlyze.locale.text('cancel-pressed'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Go back to the main window.
        self.on_analysis_closed()

    def on_select_analysis(self, sender=None, data=None):
        """Display the window for selecting the locations."""
        setlyze.gui.SelectBatchAnalysis()

    def on_analysis_selected(self, sender, analysis):
        """Prepare the selected analysis for batch mode."""
        # Set the selected analysis.
        self.analysis = analysis

        # Select the locations.
        self.on_select_locations()

    def on_select_locations(self, sender=None, data=None):
        """Display the window for selecting the locations."""
        select = setlyze.gui.SelectLocations(width=370, slot=0)
        select.set_title(setlyze.locale.text('analysis1'))
        select.set_description(setlyze.locale.text('select-locations') + "\n\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

    def on_select_species(self, sender=None, data=None):
        """Display the window for selecting the species."""
        select = setlyze.gui.SelectSpecies(width=500, slot=0)
        select.set_title(setlyze.locale.text('analysis1'))
        select.set_description(setlyze.locale.text('select-species') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

        # This button should not be pressed now, so hide it.
        select.button_chg_source.hide()

    def on_define_plate_areas(self, sender=None, data=None):
        """Display the window for defining the plate areas."""
        spots = setlyze.gui.DefinePlateAreas()
        spots.set_title(setlyze.locale.text('analysis1'))

    def on_start_analysis(self, sender=None, data=None):
        """Start the analysis."""
        self.start_time = time.time()

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Performing analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        self.pdialog_handler = setlyze.std.ProgressDialogHandler(pd)
        self.pdialog_handler.autoclose = False

        # Select the analysis.
        if self.analysis == 'spot_preference':
            self.batch_run_spot_preference()
        elif self.analysis == 'attraction_intra':
            return
        elif self.analysis == 'attraction_inter':
            return
        elif self.analysis == 'relations':
            return

    def batch_run_spot_preference(self):
        """Run analysis Spot Preference in batch mode.

        Repeat the analysis for each species separately.
        """
        locations = setlyze.config.cfg.get('locations-selection', slot=0)
        species = setlyze.config.cfg.get('species-selection', slot=0)
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps(
            (setlyze.analysis.spot_preference.PROGRESS_STEPS +
            setlyze.config.cfg.get('test-repeats')) * len(species)
            )

        for sp in species:
            # Create a new analysis thread.
            t = setlyze.analysis.spot_preference.Worker(self.lock, locations,
                [sp], areas_definition)
            t.set_pdialog_handler(self.pdialog_handler)

            # Add it to the list of threads.
            self.threads.append(t)

            # Start the thread.
            t.start()

    def on_display_report(self, sender):
        """Display the report in a window.

        Design Part: 1.68
        """
        #report = setlyze.config.cfg.get('analysis-report')
        #setlyze.gui.DisplayReport(report)
        logging.info( "Running time: %f" % (time.time() - self.start_time) )
