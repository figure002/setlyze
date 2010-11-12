#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
#
#  This file is part of SETLyze - A tool for analyzing SETL data.
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

import logging
import math
import threading
import time
from sqlite3 import dbapi2 as sqlite

import pygtk
pygtk.require('2.0')
import gtk

import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.std

__author__ = "Jonathan den Boer, Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

class Begin(object):
    """Make all the preparations for analysis 1:
        * Let the user select the locations.
        * Let the user select the species.
        * Let the user define the plate areas.

    When done, start the analysis.

    Design Part: 1.3.1
    """

    def __init__(self):
        # Create log message.
        logging.info("Beginning %s" % setlyze.locale.text('analysis1'))

        # Bind handles to application signals.
        self.handle_application_signals()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)
        setlyze.config.cfg.set('plate-areas-definition', None)

        # Emit the signal that we are beginning with an analysis.
        setlyze.std.sender.emit('beginning-analysis')

    def __del__(self):
        logging.info("Leaving %s" % setlyze.locale.text('analysis1'))

    def handle_application_signals(self):
        """Respond to signals emitted by the application."""

        # This analysis has just started.
        self.handler1 = setlyze.std.sender.connect('beginning-analysis',
            self.on_select_locations)

        # The user pressed the X button of a locations/species
        # selection window.
        self.handler2 = setlyze.std.sender.connect('selection-dialog-closed',
            self.on_window_closed)

        # The user pressed the X button of a define spots window.
        self.handler3 = setlyze.std.sender.connect('define-areas-dialog-closed',
            self.on_window_closed)

        # User pressed the Back button in the locations selection window.
        self.handler4 = setlyze.std.sender.connect('locations-dialog-back',
            self.on_window_closed)

        # User pressed the Back button in the species selection window.
        self.handler5 = setlyze.std.sender.connect('species-dialog-back',
            self.on_select_locations)

        # User pressed the Back button in the define spots window.
        self.handler6 = setlyze.std.sender.connect('define-areas-dialog-back',
            self.on_select_species)

        # The user selected locations have been saved.
        self.handler7 = setlyze.std.sender.connect('locations-selection-saved',
            self.on_select_species)

        # The user selected species have been saved.
        self.handler8 = setlyze.std.sender.connect('species-selection-saved',
            self.on_define_plate_areas)

        # The spots have been defined by the user.
        self.handler9 = setlyze.std.sender.connect('plate-areas-defined',
            self.on_start_analysis)

        # The report window was closed.
        self.handler10 = setlyze.std.sender.connect('report-dialog-closed',
            self.on_window_closed)

        # The analysis was finished.
        self.handler11 = setlyze.std.sender.connect('analysis-aborted',
            self.on_analysis_aborted)

        # Display the report after the progress dialog for the analysis
        # was closed. Warning: A progress dialog will also close when
        # the user decided to switch to a new data source in the
        # locations selection window, so block this handler until the
        # analysis has started.
        self.handler12 = setlyze.std.sender.connect('progress-dialog-closed',
            self.on_display_report)
        # Block handler 12.
        setlyze.std.sender.handler_block(self.handler12)

        # Things to do when the analysis has started.
        self.handler13 = setlyze.std.sender.connect('analysis-started',
            self.on_analysis_started)

    def on_analysis_started(self, sender):
        """Handle events that need to happen when the analysis has
        started.
        """

        # Unblock handler 12.
        sender.handler_unblock(self.handler12)

    def destroy_handler_connections(self):
        """Disconnect all signal connections with signal handlers
        created by this analysis.
        """
        setlyze.std.sender.disconnect(self.handler1)
        setlyze.std.sender.disconnect(self.handler2)
        setlyze.std.sender.disconnect(self.handler3)
        setlyze.std.sender.disconnect(self.handler4)
        setlyze.std.sender.disconnect(self.handler5)
        setlyze.std.sender.disconnect(self.handler6)
        setlyze.std.sender.disconnect(self.handler7)
        setlyze.std.sender.disconnect(self.handler8)
        setlyze.std.sender.disconnect(self.handler9)
        setlyze.std.sender.disconnect(self.handler10)
        setlyze.std.sender.disconnect(self.handler11)
        setlyze.std.sender.disconnect(self.handler12)
        setlyze.std.sender.disconnect(self.handler13)

    def on_analysis_aborted(self, sender):
        setlyze.config.cfg.get('progress-dialog').destroy_silent()

        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Empty plate areas")
        dialog.format_secondary_text("Got nothing to do, because "
            "all the plate areas totals were zero. "
            "You might have more luck if you select more locations "
            "next time. The current analysis will abort.")
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            dialog.destroy()

            # Go back to the main window.
            self.on_window_closed()

    def on_window_closed(self, sender=None, data=None):
        """Show the main window and destroy the handler connections."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.destroy_handler_connections()

    def on_select_locations(self, sender=None, data=None):
        """Display the window for selecting the locations."""
        select = setlyze.gui.SelectLocations(width=370, slot=0)
        select.set_title(setlyze.locale.text('analysis1'))
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
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

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Performing analysis",
            description=setlyze.locale.text('analysis-running'))
        setlyze.config.cfg.set('progress-dialog', pd)

        # Perform analysis...
        t = Start()
        t.run()

    def on_display_report(self, sender):
        """Display the report in a window.

        Design Part: 1.68
        """
        report = setlyze.config.cfg.get('analysis-report')
        setlyze.gui.DisplayReport(report)

class Start(threading.Thread):
    """Perform the calculations for analysis 1 "Spot Preference".

    Design Part: 1.3.2
    """

    def __init__(self):
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.total_species = None
        self.mean = None
        self.areas_totals_observed = None # Observed species totals per plate area (Design Part: 2.25)
        self.areas_totals_expected = None # Expected species totals per plate area (Design Part: 2.26)
        self.area2chisquare = None
        self.chisquare = None

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis1'))

        # Emit the signal that an analysis has started.
        setlyze.std.sender.emit('analysis-started')

    def __del__(self):
        logging.info("%s was completed!" % setlyze.locale.text('analysis1'))

    def run(self):
        """Call the necessary methods for the analysis in the right order
        and do some data checks:
            * :meth:`get_areas_totals_observed`
            * Check if all plate areas totals are zero. If so, abort.
            * :meth:`get_areas_totals_expected`
            * :meth:`chi_square_tester`
            * :meth:`generate_report`

        Design Part: 1.58
        """

        # Add a short delay. This gives the progress dialog time to
        # display properly.
        time.sleep(0.5)

        # The total number of times we decide to update the progress
        # dialog.
        total_steps = 5.0

        setlyze.std.update_progress_dialog(1/total_steps,
            "Calculating observed species totals per plate area...")

        # Calculate the species totals.
        self.areas_totals_observed = self.get_areas_totals_observed()
        logging.info("\tObserved species totals: %s" % self.areas_totals_observed)

        # Make sure that spot area totals are not all zero. If so, abort
        # the analysis, because we can't devide by zero (unless you're
        # Chuck Norris of course).
        areas_total = 0
        for area_total in self.areas_totals_observed.itervalues():
            areas_total += area_total

        if areas_total == 0:
            logging.info("\tAll plate areas totals are zero. Aborting.")
            setlyze.std.sender.emit('analysis-aborted')
            return

        setlyze.std.update_progress_dialog(2/total_steps,
            "Calculating expected species totals per plate area...")

        # Calculate the expected totals.
        self.areas_totals_expected = self.get_areas_totals_expected()
        logging.info("\tExpected species totals: %s" % self.areas_totals_expected)

        setlyze.std.update_progress_dialog(3/total_steps,
            "Performing Chi-square test...")

        # Perform Chi-square test.
        self.chi_square_tester(self.areas_totals_observed, self.areas_totals_expected)

        setlyze.std.update_progress_dialog(4/total_steps,
            "Generating the analysis report...")

        # Generate the report.
        self.generate_report()

        setlyze.std.update_progress_dialog(5/total_steps,
            "")

        # Emit the signal that the analysis has finished.
        setlyze.std.sender.emit('analysis-finished')

    def get_areas_totals_observed(self):
        """
        Return the observed totals for a specie for each plate area.

        Design Part: 1.62
        """
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')
        locations_selection = setlyze.config.cfg.get('locations-selection', slot=0)
        species_selection = setlyze.config.cfg.get('species-selection', slot=0)

        # From spot name to spot surface IDs (used in the database).
        spotname2surid = {  'A': (1,5,21,25),
                            'B': (2,3,4,6,10,11,15,16,20,22,23,24),
                            'C': (7,8,9,12,14,17,18,19),
                            'D': (13) }

        # Matrix of which surface IDs belong to which area.
        area2surid = {  'area1': [],
                        'area2': [],
                        'area3': [],
                        'area4': [] }

        for area, spot_names in areas_definition.iteritems():
            # Get all spot names of an area.
            for spot_name in spot_names:
                # Get all surface IDs that belong to those spot names.
                items = spotname2surid[spot_name]

                # Combine all the surface IDs for an area.
                if isinstance(items, tuple):
                    area2surid[area].extend(items)
                else:
                    area2surid[area].append(items)

        # Remove empty areas.
        remove = []
        for area, surids in area2surid.iteritems():
            if len(surids) == 0:
                remove.append(area)
        for area in remove:
            del area2surid[area]

        # Make an object that facilitates access to the database.
        accessdb = setlyze.database.AccessDB()
        db = accessdb.db

        # Get the record IDs that match the locations and species
        # selection.
        rec_ids = db.get_record_ids(locations_selection, species_selection)

        # Get all 25 spot booleans from each record that matches the
        # list of record IDs.
        # TODO: Instead of loading all record spots in a variable, it's
        # better to save the matching records to a new table
        # in the local database (if data-source is SETL) and then select
        # one row at a time from the local database. This way we can
        # prevent large amounts of records from being saved in a variable.
        records = db.get_spots(rec_ids)

        # Make a log message.
        logging.info("\tTotal records that match the species+locations selection: %d"
            % len(records))

        # Dictionary which will contain the species total for each area.
        areas_totals_observed = {   'area1': 0,
                            'area2': 0,
                            'area3': 0,
                            'area4': 0 }

        # Fill the totals table.
        for record in records:
            # Begin with spot 1 (up to 25).
            spot = 1
            # A list of areas that should be skipped for this record.
            #skip_areas = []
            # Check for each spot in the record row if the specie is
            # present. 'present' == True, if the specie is present on
            # that spot.
            for precence in record:
                # In case the 'present' boolean is False, just continue
                # with the next spot.
                if not precence:
                    continue
                # If we pass here, the boolean is True.
                # Walk through each area in the area2surid dictionary.
                # And also get the surface IDs for that area.
                for area, surids in area2surid.iteritems():
                    # We don't want to count the same record more than
                    # once for an area.
                    #if area in skip_areas:
                    #    continue
                    # Check if the current spot ID belongs to that
                    # area.
                    if spot in surids:
                        # If so, add 1 to the species total of that
                        # area.
                        areas_totals_observed[area] += 1
                        # Next time we find a spot for this area, skip
                        # it, as we don't want to count the same record
                        # more than once for an area.
                        #skip_areas.append(area)
                        # Once a match was found, that same spot ID
                        # can't belong to another area. So continue with
                        # the next spot for this record row.
                        break
                spot += 1

        # Remove the areas that were earlier removed, as these areas
        # were empty, and shouldn't be included for the calculations
        # later on.
        for area in remove:
            del areas_totals_observed[area]

        return areas_totals_observed

    def get_areas_totals_expected(self):
        """
        Return the expected totals for a specie for each plate area.

        Design Part: 1.63
        """
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')

        # The spot names, and how many times they occur on a plate.
        spot_multiplies = {'A':4, 'B':12, 'C':8, 'D':1}

        # Calculate what each spot area should be multiplied with, as
        # the spot areas can be combinations of spots.
        multiply_rules = { 'area1': 0, 'area2': 0, 'area3': 0, 'area4': 0 }
        for area, spot_names in areas_definition.iteritems():
            for spot_name in spot_names:
                multiply_rules[area] += spot_multiplies[spot_name]

        # Make log message.
        logging.info("\tMultiply rules: %s" % multiply_rules)

        # Calculate the sum of area totals.
        areas_total = 0
        for area_total in self.areas_totals_observed.itervalues():
            areas_total += area_total

        # Calculate the mean value for the spots.
        spot_mean = areas_total / 25.0

        # Calculate the expected values and put them in the expected
        # totals table.
        areas_totals_expected = {}
        for area in self.areas_totals_observed.iterkeys():
            areas_totals_expected[area] = spot_mean * multiply_rules[area]

        return areas_totals_expected

    def chi_square_tester(self, areas_totals_observed, areas_totals_expected):
        """
        Perform the Chi-square test on the observed and expected values.

        Design Part: 1.64
        """

        # Huh?
        P1 = 11.34
        P25 = 9.35
        P5 = 7.81
        DoF = 3

        # Calculate Chi-square value for each spot area.
        self.area2chisquare = {}
        for area, observed in self.areas_totals_observed.iteritems():
            expected = self.areas_totals_expected[area]
            self.area2chisquare[area] = ( math.pow((observed-expected),2) ) / expected

        # Make log message.
        logging.info("\tChi-square per spot area: %s" % self.area2chisquare)

        # Calculate Chi-square.
        self.chisquare = 0
        for area_chi in self.area2chisquare.itervalues():
            self.chisquare += area_chi

        # Make log message.
        logging.info("\tChi-square: %s" % self.chisquare)

    def generate_report(self):
        """
        Generate the analysis report and display the report in a dialog.

        Design Part: 1.13
        """
        report = setlyze.std.ReportGenerator()
        report.set_analysis('spot_preference')
        report.set_location_selections()
        report.set_specie_selections()
        report.set_plate_areas_definition()
        report.set_area_totals_observed(self.areas_totals_observed)
        report.set_area_totals_expected(self.areas_totals_expected)

        # Create global a link to the report.
        setlyze.config.cfg.set('analysis-report', report.get_report())


