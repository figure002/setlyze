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

import os
import logging
import math
import itertools
import threading
import time
from sqlite3 import dbapi2 as sqlite

import gobject

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
    """
    Make all the preparations for analysis 2.1:
        * Let the user select the locations.
        * Let the user select the species.

    When done, start the analysis.

    Design Part: 1.4.1
    """

    def __init__(self):
        # Create log message.
        logging.info("Beginning %s" % setlyze.locale.text('analysis2.1'))

        # Bind handles to application signals.
        self.handle_application_signals()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)

        # Emit the signal that we are beginning with an analysis.
        setlyze.std.sender.emit('beginning-analysis')

    def __del__(self):
        logging.info("Leaving %s" % setlyze.locale.text('analysis2.1'))

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
            self.on_analysis_closed)

        # User pressed the Back button in the species selection window.
        self.handler4 = setlyze.std.sender.connect('species-dialog-back',
            self.on_select_locations)

        # The user selected locations have been saved.
        self.handler5 = setlyze.std.sender.connect('locations-selection-saved',
            self.on_select_species)

        # The user selected species have been saved.
        self.handler6 = setlyze.std.sender.connect('species-selection-saved',
            self.start_analysis)

        # The report window was closed.
        self.handler7 = setlyze.std.sender.connect('report-dialog-closed',
            self.on_analysis_closed)

        # Display the report after the analysis has finished.
        self.handler8 = setlyze.std.sender.connect('analysis-finished',
            self.on_display_report)

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

    def on_analysis_closed(self, obj=None, data=None):
        """Show the main window and destroy the handler connections."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.destroy_handler_connections()

    def on_select_locations(self, obj=None, data=None):
        """Display the window for selecting the locations."""
        select = setlyze.gui.SelectLocations(width=370, slot=0)
        select.set_title(setlyze.locale.text('analysis2.1'))
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

    def on_select_species(self, obj=None, data=None):
        """Display the window for selecting the species."""
        select = setlyze.gui.SelectSpecies(width=500, slot=0)
        select.set_title(setlyze.locale.text('analysis2.1'))
        select.set_description(setlyze.locale.text('select-species') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

        # This button should not be pressed now, so hide it.
        select.button_chg_source.hide()

    def start_analysis(self, obj=None, data=None):
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
    Perform all the calculations for analysis 2.1.

    Design Part: 1.4.2
    """

    def __init__(self):
        super(Start, self).__init__()

        # Path to the local database file.
        self.dbfile = setlyze.config.cfg.get('db-file')
        # Dictionary for the statistic test results.
        self.statistics = {'normality':[], # Design Part: 2.36
                        'significance':[]} # Design Part: 2.37

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis2.1'))

        # Emit the signal that an analysis has started.
        setlyze.std.sender.emit('analysis-started')

    def __del__(self):
        logging.info("%s was completed!" % setlyze.locale.text('analysis2.1'))

    def run(self):
        """
        Call the necessary methods for the analysis in the right order:
            * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
              :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
            * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
              :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
            * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
            * :meth:`calculate_distances_intra`
            * :meth:`calculate_distances_intra_expected`
            * :meth:`generate_report`

        Design Part: 1.59
        """

        # Add a short delay. This gives the progress dialog time to
        # display properly.
        time.sleep(0.5)

        # The total number of times we update the progress dialog during
        # the analysis.
        self.total_steps = 10.0

        # Make an object that facilitates access to the database.
        self.db = setlyze.database.get_database_accessor()

        # Get the record IDs that match the selections.
        locations_selection = setlyze.config.cfg.get('locations-selection', slot=0)
        species_selection = setlyze.config.cfg.get('species-selection', slot=0)
        rec_ids = self.db.get_record_ids(locations_selection, species_selection)
        # Create log message.
        logging.info("\tTotal records that match the species+locations selection: %d" % len(rec_ids))

        # Create log message.
        logging.info("\tCreating table with species spots...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(1/self.total_steps, "Creating table with species spots...")
        # Make a spots table for the selected species.
        self.db.set_species_spots(rec_ids, slot=0)

        # Create log message.
        logging.info("\tMaking plate IDs in species spots table unique...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(2/self.total_steps, "Making plate IDs in species spots table unique...")
        # Make the plate IDs unique.
        n_plates_unique = self.db.make_plates_unique(slot=0)
        # Create log message.
        logging.info("\t  %d records remaining." % (n_plates_unique))

        # Create log message.
        logging.info("\tSaving the positive spot totals for each plate...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(3/self.total_steps, "Saving the positive spot totals for each plate...")
        # Save the positive spot totals for each plate to the database.
        skipped = self.db.fill_plate_spot_totals_table('species_spots_1')
        # Create log message.
        logging.info("\tSkipping %d records with too few positive spots." % skipped)
        logging.info("\t  %d records remaining." % (n_plates_unique - skipped))

        # Create log message.
        logging.info("\tCalculating the intra-specific distances for the selected specie...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(4/self.total_steps, "Calculating the intra-specific distances for the selected specie...")
        # Calculate the observed spot distances.
        self.calculate_distances_intra()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(5/self.total_steps, "Calculating the expected distances for the selected specie...")
        # Create log message.
        logging.info("\tCalculating the expected distances for the selected specie...")
        # Generate random spots.
        self.calculate_distances_intra_expected()

        # Create log message.
        logging.info("\tPerforming statistical tests...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(6/self.total_steps, "Performing statistical tests...")
        # Performing the significance test.
        self.calculate_significance()

        # Create log message.
        logging.info("\tGenerating the analysis report...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(7/self.total_steps, "Generating the analysis report...")
        # Generate the report.
        self.generate_report()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(10/self.total_steps, "", autoclose=True)

        # Emit the signal that the analysis has finished.
        # Note that the signal will be sent from a separate thread,
        # so we must use gobject.idle_add.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')

    def calculate_distances_intra(self):
        """
        Calculate the intra-specific distances for each plate in the
        species_spots table and save the distances to a table in
        the local database.

        Design Part: 1.22
        """

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_observed table before we use it
        # again.
        cursor.execute("DELETE FROM spot_distances_observed")
        connection.commit()

        # Get all records from the table.
        cursor.execute( "SELECT rec_pla_id,"
                        "rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM species_spots_1")

        for record in cursor:
            # Get all possible positive spot combinations for each
            # plate.
            # If the record contains less than 2 positive spots, the
            # combos list will be empty, and nothing will be calculated.
            combos = setlyze.std.get_spot_combinations_from_record(record[1:])

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

    def calculate_distances_intra_expected(self):
        """
        Calculate the expected distances based on the observed distances
        and save these to a table in the local database.

        Design Part: 1.23
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
        cursor.execute( "SELECT pla_id, n_spots_a "
                        "FROM plate_spot_totals"
                        )

        for plate_id, n_spots in cursor:
            # Use that number of spots to generate the same number of
            # random spots.
            random_spots = setlyze.std.get_random_for_plate(n_spots)

            # Get all possible combinations for the spots.
            combos = itertools.combinations(random_spots, 2)

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

    def calculate_significance(self):
        """Perform statistical tests to check if the differences between
        the means of the two sets of distances are statistically
        significant.

        First we do a normality test on the observed distances. Based on
        this result, we will either use the t-test (normality true) or
        the Wilcoxon test (normality false).

        We perform an unpaired two-sample T-test. We use unpaired
        because the two sets of distances are unrelated. In other words,
        a distance n in 'observed' is unrelated to distance n in
        'expected' (where n is an item number in the lists).

        Null hypothesis:
            The means of the two sets of distances are
            equal. The specie in question doesn't attract or repel itself.
        Alternative hypothesis:
            The means of the two sets of distances
            are not equal. The specie in question attracts (mean
            observed < mean expected) or repels (mean observed >
            mean expected) itself.

        The decision is based on the P-value calculated by the test:
        P >= alpha level: Null hypothesis.
        P < alpha level: Alternative hypothesis.

        The default value for the alpha level is 0.05 (5%).
        The default value for the confidence level is 0.95 (95%).

        A high number of positive spots on a plate will of course lead
        to a high P-value. These plates will negatively affect the
        result of statistical test. To account for this, the tests
        are performed multiple times. Instead of doing one test on all
        plates, we group the plates based on the number of positive spots
        they contain. This results in 24 groups (2 to 25 spots). And we
        perform the test on each of these groups.

        References:
        1. N. Millar, Biology statistics made simple using Excel, School Science Review, December 2001, 83(303).
        2. P. Dalgaard, Introductory Statistics with R, DOI: 10.1007 / 978-0-387-79054-1_1.

        Design Part: 1.24
        """

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        for n_spots in range(2,27):
            # Of course, there are just 25 spots, so when we reach 26,
            # set n_spots to -25 (meaning, take all spots up to 25).
            if n_spots == 26:
                n_spots = -25

            # Get both sets of distances from plates per total spot numbers.
            self.db.get_distances_matching_spots_total(cursor, 'spot_distances_observed', n_spots)
            self.db.get_distances_matching_spots_total(cursor2, 'spot_distances_expected', n_spots)

            # Create lists for the distances so we can use it for the R
            # functions.
            observed = [x[0] for x in cursor]
            expected = [x[0] for x in cursor2]

            # A minimum of 3 observed distances is required for the
            # normality test. So skip this spots number if it's less.
            count_observed = len(observed)
            if count_observed < 3:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.average(observed)
            mean_expected = setlyze.std.average(expected)

            # Get the number of plates found that match the current
            # number of positive spots.
            if n_spots < 0:
                # If spots_n is a negative number, get all distances
                # up to the absolute number. So if we find -5, get all
                # distances up to 5.
                cursor.execute( "SELECT COUNT(pla_id) "
                                "FROM plate_spot_totals "
                                "WHERE n_spots_a <= ?", [abs(n_spots)])
                n_plates = cursor.fetchone()[0]
            else:
                # If it's a positive number, just get the plates that
                # match that spots number.
                cursor.execute( "SELECT COUNT(pla_id) "
                                "FROM plate_spot_totals "
                                "WHERE n_spots_a = ?", [n_spots])
                n_plates = cursor.fetchone()[0]

            # Perform the normality test.
            normality_result = setlyze.std.shapiro_test(observed)

            # Save the normality result.
            result = {}
            result['attr'] = {
                'n_positive_spots': n_spots,
                'method': normality_result['method'],
                'n': count_observed,
                }
            result['items'] = {
                'p_value': normality_result['p.value'],
                'w': normality_result['statistic']['W'],
                }
            self.statistics['normality'].append(result)

            # Decide which significance test to use based on the
            # result of the normality test. If P-value > alpha, then
            # normality is True.
            if normality_result['p.value'] > setlyze.config.cfg.get('normality-alpha'):
                # Perform the Welch two sample T-test, which assumes
                # the data has a normal distribution.
                sig_result = setlyze.std.t_test(observed, expected,
                    alternative="two.sided", paired=False,
                    conf_level=setlyze.config.cfg.get('significance-confidence'))

                # Save the significance result.
                result = {}
                result['attr'] = {
                    'n_positive_spots': n_spots,
                    'n_plates': n_plates,
                    'n': count_observed,
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': setlyze.config.cfg.get('significance-confidence'),
                    'paired': False,
                    }
                result['items'] = {
                    'p_value': sig_result['p.value'],
                    't': sig_result['statistic']['t'],
                    'mean_observed': sig_result['estimate']['mean of x'],
                    'mean_expected': sig_result['estimate']['mean of y'],
                    'df': sig_result['parameter']['df'],
                    'conf_int_start': sig_result['conf.int'][0],
                    'conf_int_end': sig_result['conf.int'][1],
                    }
            else:
                # Perform two sample Wilcoxon tests.
                sig_result = setlyze.std.wilcox_test(observed, expected,
                    alternative = "two.sided", paired = False,
                    conf_level = setlyze.config.cfg.get('significance-confidence'),
                    conf_int = True)

                # Save the significance result.
                result = {}
                result['attr'] = {
                    'n_positive_spots': n_spots,
                    'n_plates': n_plates,
                    'n': count_observed,
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': setlyze.config.cfg.get('significance-confidence'),
                    'paired': False,
                    }
                result['items'] = {
                    'p_value': sig_result['p.value'],
                    'mean_observed': mean_observed,
                    'mean_expected': mean_expected,
                    'conf_int_start': sig_result['conf.int'][0],
                    'conf_int_end': sig_result['conf.int'][1],
                    }

            # Append the result to the list of results.
            self.statistics['significance'].append(result)

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

    def generate_report(self):
        """Generate the analysis report and display the report in a
        dialog.

        Design Part: 1.14
        """
        report = setlyze.std.ReportGenerator()
        report.set_analysis('attraction_intra')
        report.set_location_selections()
        report.set_specie_selections()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(8/self.total_steps, "Generating the analysis report...")

        report.set_spot_distances_observed()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(9/self.total_steps, "Generating the analysis report...")

        report.set_spot_distances_expected()

        report.set_statistics_normality(self.statistics['normality'])
        report.set_statistics_significance(self.statistics['significance'])

        # Create a global link to the report.
        setlyze.config.cfg.set('analysis-report', report.get_report())



