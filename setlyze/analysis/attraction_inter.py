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
import threading
import itertools
import time
from sqlite3 import dbapi2 as sqlite

import gobject

import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.locale

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

class Begin(object):
    """Make all the preparations for analysis 2.2:
        * Let the user make the first locations selection.
        * Let the user make the first species selection.
        * Let the user make the second locations selection.
        * Let the user make the second species selection.

    When done, start the analysis.

    Design Part: 1.5.1
    """

    def __init__(self):
        self.last_window = None
        self.previous_window = None

        # Create log message.
        logging.info("Beginning %s" % setlyze.locale.text('analysis2.2'))

        # Bind handles to application signals.
        self.handle_application_signals()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)

        # Reset the save slot.
        setlyze.std.sender.set_property('save-slot', 0)

        # Emit the signal that an analysis has started.
        #setlyze.std.sender.set_property('save_slot', 0)
        setlyze.std.sender.emit('beginning-analysis')

    def __del__(self):
        logging.info("Leaving %s" % setlyze.locale.text('analysis2.2'))

    def handle_application_signals(self):
        """Respond to signals emitted by the application."""

        # This analysis has just started.
        self.handler1 = setlyze.std.sender.connect('beginning-analysis',
            self.on_select_locations)

        # The user pressed the X button of a locations/species
        # selection window.
        self.handler2 = setlyze.std.sender.connect('selection-dialog-closed',
            self.on_analysis_closed)

        # User pressed the Back button in the locations selection window.
        self.handler3 = setlyze.std.sender.connect('locations-dialog-back',
            self.on_locations_back)

        # User pressed the Back button in the species selection window.
        self.handler4 = setlyze.std.sender.connect('species-dialog-back',
            self.on_species_back)

        # The user selected locations have been saved.
        self.handler5 = setlyze.std.sender.connect('locations-selection-saved',
            self.on_locations_saved)

        # The user selected species have been saved.
        self.handler6 = setlyze.std.sender.connect('species-selection-saved',
            self.on_species_saved)

        # Display the report after the analysis has finished.
        self.handler7 = setlyze.std.sender.connect('analysis-finished',
            self.on_display_report)

        # The report window was closed.
        self.handler8 = setlyze.std.sender.connect('report-dialog-closed',
            self.on_analysis_closed)

    def on_analysis_closed(self, obj=None):
        """Show the main window and destroy the handler connections."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.destroy_handler_connections()

    def destroy_handler_connections(self):
        """
        Disconnect all signal connections with signal handlers created
        by this analysis.
        """
        setlyze.std.sender.disconnect(self.handler1)
        setlyze.std.sender.disconnect(self.handler2)
        setlyze.std.sender.disconnect(self.handler3)
        setlyze.std.sender.disconnect(self.handler4)
        setlyze.std.sender.disconnect(self.handler5)
        setlyze.std.sender.disconnect(self.handler6)
        setlyze.std.sender.disconnect(self.handler7)
        setlyze.std.sender.disconnect(self.handler8)

    def on_locations_saved(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            self.on_select_species()
            return
        elif save_slot == 1:
            self.on_select_species()
            return

    def on_species_saved(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            sender.set_property('save-slot', 1)
            self.on_select_locations()
            return
        elif save_slot == 1:
            self.on_start_analysis()
            return

    def on_locations_back(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            self.on_analysis_closed()
            return
        elif save_slot == 1:
            sender.set_property('save-slot', 0)
            self.on_select_species()
            return

    def on_species_back(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            self.on_select_locations()
            return
        elif save_slot == 1:
            self.on_select_locations()
            return

    def on_select_locations(self, sender=None, data=None):
        """Display the window for selecting the locations."""

        # Find out to which selection slot this locations selection
        # should be saved.
        save_slot = setlyze.std.sender.get_property('save-slot')

        # Display the species selection window.
        select = setlyze.gui.SelectLocations(width=370, slot=save_slot)
        select.set_title(setlyze.locale.text('analysis2.2'))

        # Change the header text.
        if save_slot == 0:
            select.set_header("First Locations Selection")
            select.set_description(setlyze.locale.text('select-locations') + "\n" +
                setlyze.locale.text('option-change-source') + "\n\n" +
                setlyze.locale.text('selection-tips')
                )
        elif save_slot == 1:
            select.set_header("Second Locations Selection")
            select.set_description( setlyze.locale.text('select-locations') + "\n\n" +
                setlyze.locale.text('selection-tips')
                )

            # This button should not be pressed now, so hide it.
            select.button_chg_source.hide()

    def on_select_species(self, sender=None, data=None):
        """Display the window for selecting the species."""

        # Find out to which selection slot this species selection
        # should be saved.
        save_slot = setlyze.std.sender.get_property('save-slot')

        # Display the species selection window.
        select = setlyze.gui.SelectSpecies(width=500, slot=save_slot)
        select.set_title(setlyze.locale.text('analysis2.2'))
        select.set_description( setlyze.locale.text('select-locations') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

        # Change the header text.
        if save_slot == 0:
            select.set_header("First Species Selection")
        elif save_slot == 1:
            select.set_header("Second Species Selection")

        # This button should not be pressed now, so hide it.
        select.button_chg_source.hide()

    def on_start_analysis(self, sender=None):
        """Start the analysis."""

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Performing Analysis",
            description=setlyze.locale.text('analysis-running'))
        setlyze.config.cfg.set('progress-dialog', pd)

        # Perform analysis...
        t = Start()
        t.start()

    def on_display_report(self, sender):
        """
        Display the report in a window.

        Design Part: 1.68
        """
        report = setlyze.config.cfg.get('analysis-report')
        setlyze.gui.DisplayReport(report)

class Start(threading.Thread):
    """
    Perform all the calculations for analysis 2.2.

    Design Part: 1.5.2
    """

    def __init__(self):
        super(Start, self).__init__()

        self.dbfile = setlyze.config.cfg.get('db-file')

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis2.2'))

        # Emit the signal that an analysis has started.
        setlyze.std.sender.emit('analysis-started')

    def __del__(self):
        logging.info("%s was completed!" % setlyze.locale.text('analysis2.2'))

    def run(self):
        """
        Call the necessary methods for the analysis in the right order:
            * For the first species selection:
                * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
                  :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
                * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
                  :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
                * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
            * For the second species selection:
                * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
                  :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
                * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
                  :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
                * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
            * :meth:`calculate_distances_inter`
            * :meth:`calculate_distances_inter_expected`
            * :meth:`generate_report`

        Design Part: 1.60
        """

        # Add a short delay. This gives the progress dialog time to
        # display properly.
        time.sleep(0.5)

        # The total number of times we update the progress dialog during
        # the analysis.
        self.total_steps = 11.0

        # Make an object that facilitates access to the database.
        db = setlyze.database.get_database_accessor()

        # SELECTION 1

        # Update progress dialog.
        setlyze.std.update_progress_dialog(1/self.total_steps, "Creating first table with species spots...")
        # Get the record IDs that match the selections.
        locations_selection1 = setlyze.config.cfg.get('locations-selection', slot=0)
        species_selection1 = setlyze.config.cfg.get('species-selection', slot=0)
        rec_ids1 = db.get_record_ids(locations_selection1, species_selection1)
        # Update progress dialog.
        logging.info("\tTotal records that match the first species+locations selection: %d" % len(rec_ids1))

        # Create log message.
        logging.info("\t\tCreating first table with species spots...")
        # Make a spots table for both species selections.
        db.set_species_spots(rec_ids1, slot=0)

        # Update progress dialog.
        setlyze.std.update_progress_dialog(2/self.total_steps, "Making plate IDs in species spots table unique...")
        # Create log message.
        logging.info("\t\tMaking plate IDs in species spots table unique...")
        # Make the plate IDs unique.
        n_plates_unique = db.make_plates_unique(slot=0)
        # Create log message.
        logging.info("\t\t  %d records remaining." % (n_plates_unique))

        # SELECTION 2

        # Update progress dialog.
        setlyze.std.update_progress_dialog(3/self.total_steps, "Creating second table with species spots...")
        # Get the record IDs that match the selections.
        locations_selection2 = setlyze.config.cfg.get('locations-selection', slot=1)
        species_selection2 = setlyze.config.cfg.get('species-selection', slot=1)
        rec_ids2 = db.get_record_ids(locations_selection2, species_selection2)
        # Create log message.
        logging.info("\tTotal records that match the second species+locations selection: %d" % len(rec_ids2))

        # Create log message.
        logging.info("\t\tCreating second table with species spots...")
        # Make a spots table for both species selections.
        db.set_species_spots(rec_ids2, slot=1)

        # Update progress dialog.
        setlyze.std.update_progress_dialog(4/self.total_steps, "Making plate IDs in species spots table unique...")
        # Create log message.
        logging.info("\t\tMaking plate IDs in species spots table unique...")
        # Make the plate IDs unique.
        n_plates_unique = db.make_plates_unique(slot=1)
        # Create log message.
        logging.info("\t\t  %d records remaining." % (n_plates_unique))

        # GENERAL

        # Create log message.
        logging.info("\tSaving the positive spot totals for each plate...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(5/self.total_steps, "Saving the positive spot totals for each plate...")
        # Save the positive spot totals for each plate to the database.
        db.fill_plate_spot_totals_table('species_spots_1','species_spots_2')

        # Update progress dialog.
        setlyze.std.update_progress_dialog(6/self.total_steps, "Calculating the inter-specific distances for the selected species...")
        # Create log message.
        logging.info("\tCalculating the inter-specific distances for the selected species...")
        # Calculate the observed spot distances.
        self.calculate_distances_inter()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(7/self.total_steps, "Calculating the expected distances for the selected species...")
        # Create log message.
        logging.info("\tCalculating the expected distances for the selected species...")
        # Generate random spots.
        self.calculate_distances_inter_expected()

        # Create log message.
        logging.info("\tGenerating the analysis report...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(8/self.total_steps, "Generating the analysis report...")
        # Generate the report.
        self.generate_report()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(11/self.total_steps, "")

        # Emit the signal that the analysis has finished.
        # Note that the signal will be sent from a separate thread,
        # so we must use gobject.idle_add.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')

    def calculate_distances_inter(self):
        """
        Calculate the inter-specific distances for each plate (present
        in two tables) and save the distances to
        local_database.spot_distances_observed.

        Design Part: 1.27
        """
        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_observed table before we use it
        # again.
        cursor.execute("DELETE FROM spot_distances_observed")
        connection.commit()

        # Get all records from both spots tables where the plate IDs
        # match.
        # Each returned record has this format:
        # id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|rec_sur24|rec_sur25|id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|rec_sur24|rec_sur25
        cursor.execute( "SELECT s1.*, s2.* FROM species_spots_1 as s1 "
                        "INNER JOIN species_spots_2 as s2 "
                        "ON s1.rec_pla_id=s2.rec_pla_id"
                        )

        for record in cursor:
            record1 = record[2:27]
            record2 = record[29:54]

            # Get all possible positive spot combinations between the
            # two records.
            # If both records don't contain at least one positive spot,
            # the combos list will be empty, and nothing will be
            # calculated.
            combos = setlyze.std.get_spot_combinations_from_record(record1,record2)

            # Get all spot combination pairs.
            for spot1,spot2 in combos:
                # Use each spot combination to calculate the difference
                # per spot combination.
                # h = horizontal difference.
                # v = vertical difference.
                h,v = setlyze.std.get_spot_position_difference(spot1,spot2)

                # Use the differences to get the corresponding spot
                # distance from the spot_distances table.
                cursor2.execute( "SELECT distance "
                                 "FROM spot_distances "
                                 "WHERE delta_x = ? "
                                 "AND delta_y = ?",
                                 (h,v))
                distance = cursor2.fetchone()
                distance = distance[0]

                # Save the observed spot distances to the database.
                cursor2.execute( "INSERT INTO spot_distances_observed "
                                 "VALUES (null,?,?)",
                                 (record[0], distance)
                                )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

    def calculate_distances_inter_expected(self):
        """
        Calculate the expected distances based on the observed
        inter-specific distances (2.12) and save these to a table in the
        local database (2.13).

        Design Part: 1.69
        """

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_expected table before we use it
        # again.
        cursor.execute("DELETE FROM spot_distances_expected")
        connection.commit()

        # Get the number of positive spots for each plate. This
        # will serve as a template for the random spots.
        cursor.execute( "SELECT pla_id, n_spots_a, n_spots_b "
                        "FROM plate_spot_totals"
                        )

        for plate_id, n_spots_a, n_spots_b in cursor:
            # Use that number of spots to generate the same number of
            # random positive spots for both records.
            random_spots1 = setlyze.std.get_random_for_plate(n_spots_a)
            random_spots2 = setlyze.std.get_random_for_plate(n_spots_b)

            # Get all possible combinations between the two sets of
            # random spots.
            combos = itertools.product(random_spots1,random_spots2)

            # Get all spot combination pairs.
            for spot1,spot2 in combos:
                # Use each spot combination to calculate the difference
                # per spot combination.
                # h = horizontal difference.
                # v = vertical difference.
                h,v = setlyze.std.get_spot_position_difference(spot1,spot2)

                # Use the differences to get the corresponding spot
                # distance from the spot_distances table.
                cursor2.execute( "SELECT distance "
                                 "FROM spot_distances "
                                 "WHERE delta_x = ? "
                                 "AND delta_y = ?",
                                 (h,v)
                                 )
                distance = cursor2.fetchone()
                distance = distance[0]

                # Save the observed spot distances to the database.
                cursor2.execute( "INSERT INTO spot_distances_expected "
                                 "VALUES (null,?,?)",
                                 (plate_id, distance)
                                )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

    def generate_report(self):
        """
        Generate the analysis report and display the report in a dialog.

        Design Part: 1.15
        """
        report = setlyze.std.ReportGenerator()
        report.set_analysis('attraction_inter')
        report.set_location_selections()
        report.set_specie_selections()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(9/self.total_steps, "Generating the analysis report...")

        report.set_spot_distances_observed()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(10/self.total_steps, "Generating the analysis report...")

        report.set_spot_distances_expected()

        # Create a global link to the report.
        setlyze.config.cfg.set('analysis-report', report.get_report())
