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

"""This module performs analysis 2 "Attraction within species". This analysis
can be broken down in the following steps:

1. Show a list of all localities and let the user perform a localities
   selection.

2. Show a list of all species that match the locations selection and
   let the user perform a species selection.

3. Get all SETL records that match the localities+species selection and
   save these to table "species_spots_1" in the local database.

4. Merge records with the same plate ID in the species spots table to
   make the plate IDs unique.

5. Calculate the intra-specific spot distances from the records in the
   species spots table and save the distances to table
   "spot_distances_observed" in the local database.

6. Calculate expected intra-specific spot distances by generating
   random spots and save the distances to table
   "spot_distances_expected" in the local database.

7. Calculate the significance in difference between the observed and
   expected spot distances. Two tests of significance are performed:
   the Wilcoxon rank-sum test and the Chi-squared test.

8. Generate the analysis report.

9. Show the analysis report to the user.

"""

import os
import logging
import itertools
import time

import gobject

import setlyze.analysis.common
import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.std
import setlyze.report

__author__ = ("Jonathan den Boer, Serrano Pereira, Adam van Adrichem, "
    "Fedde Schaeffer")
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.1.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

# The number of progress steps for this analysis.
PROGRESS_STEPS = 8

class Begin(setlyze.analysis.common.PrepareAnalysis):
    """Make the preparations for analysis 2:

    1. Show a list of all localities and let the user perform a localities
       selection.

    2. Show a list of all species that match the locations selection and
       let the user perform a species selection.

    3. Start the analysis.

    4. Show the analysis report to the user.

    Design Part: 1.4.1
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Beginning analysis ”Attraction within species”")

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)

        # Emit the signal that we are beginning with an analysis.
        setlyze.std.sender.emit('beginning-analysis')

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            # This analysis has just started.
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_select_locations),
            # The user pressed the X button of a locations/species selection window.
            'selection-dialog-closed': setlyze.std.sender.connect('selection-dialog-closed', self.on_analysis_closed),
            # User pressed the Back button in the locations selection window.
            'locations-dialog-back': setlyze.std.sender.connect('locations-dialog-back', self.on_analysis_closed),
            # User pressed the Back button in the species selection window.
            'species-dialog-back': setlyze.std.sender.connect('species-dialog-back', self.on_select_locations),
            # The user selected locations have been saved.
            'locations-selection-saved': setlyze.std.sender.connect('locations-selection-saved', self.on_select_species),
            # The user selected species have been saved.
            'species-selection-saved': setlyze.std.sender.connect('species-selection-saved', self.on_start_analysis),
            # The report window was closed.
            'report-dialog-closed': setlyze.std.sender.connect('report-dialog-closed', self.on_analysis_closed),
            # Cancel button pressed.
            'analysis-canceled': setlyze.std.sender.connect('analysis-canceled', self.on_cancel_button),
            # Progress dialog closed
            'progress-dialog-closed': setlyze.std.sender.connect('progress-dialog-closed', self.on_cancel_button),
            # A thread pool job was completed.
            'thread-pool-job-completed': setlyze.std.sender.connect('thread-pool-job-completed', self.on_thread_pool_job_completed),
            # The thread pool has finished processing all jobs.
            'thread-pool-finished': setlyze.std.sender.connect('thread-pool-finished', self.on_thread_pool_finished),
        }

    def on_select_locations(self, obj=None, data=None):
        """Display the window for selecting the locations."""
        select = setlyze.gui.SelectLocations(slot=0)
        select.set_title(setlyze.locale.text('analysis2'))
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

    def on_select_species(self, obj=None, data=None):
        """Display the window for selecting the species."""
        select = setlyze.gui.SelectSpecies(width=600, slot=0)
        select.set_title(setlyze.locale.text('analysis2'))
        select.set_description(setlyze.locale.text('select-species') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

        # This button should not be pressed now, so hide it.
        select.button_chg_source.hide()

    def on_start_analysis(self, sender=None, data=None):
        """Start the analysis."""
        locations = setlyze.config.cfg.get('locations-selection', slot=0)
        species = setlyze.config.cfg.get('species-selection', slot=0)

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing Analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)

        # Set the total number of times we decide to update the progress dialog.
        pdialog_handler.set_total_steps(
            PROGRESS_STEPS + self.n_repeats
        )

        # Create a thread pool with a single thread.
        self.pool = setlyze.analysis.common.Pool(
            size=1,
            pdialog_handler=pdialog_handler
        )

        # Add the job to the pool.
        self.pool.add_job(Analysis, self.lock, locations, species)

        # Start all threads in the pool.
        self.pool.start()

class BeginBatch(Begin):
    """Make the preparations for batch analysis:

    1. Show a list of all localities and let the user perform a localities
       selection.

    2. Show a list of all species that match the locations selection and
       let the user perform a species selection.

    3. Start the analysis in batch mode.

    4. Show the analysis report to the user.
    """

    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")

        # Print elapsed time after each sub-analysis.
        self.signal_handlers['analysis-finished'] = setlyze.std.sender.connect('analysis-finished', self.print_elapsed_time)

    def on_start_analysis(self, sender=None, data=None):
        """Run the analysis in batch mode.

        Repeat the analysis for each species separately.
        """
        locations = setlyze.config.cfg.get('locations-selection', slot=0)
        species = setlyze.config.cfg.get('species-selection', slot=0)
        self.start_time = time.time()

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing Analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)

        # Set the total number of times we decide to update the progress dialog.
        pdialog_handler.set_total_steps((PROGRESS_STEPS + self.n_repeats) *
            len(species))

        # Create a thread pool.
        self.pool = setlyze.analysis.common.Pool(
            size=self.thread_pool_size,
            pdialog_handler=pdialog_handler
        )

        # Add jobs to the thread pool.
        logging.info("Adding %d jobs to the queue" % len(species))
        for sp in species:
            self.pool.add_job(Analysis, self.lock, locations, sp)

        # Start all threads in the thread pool.
        self.pool.start()

    def print_elapsed_time(self, sender):
        """Print elapsed time since start of the analysis."""
        logging.info("Time elapsed: %.2f seconds" % (time.time() - self.start_time))

    def summarize_results(self, results):
        """Join results from multiple analyses to a single report.

        Creates a dictionary in the following format ::

            {
                'attr': {
                    'columns': ('Species', 'n (plates)', 'Wilcoxon 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', 'Chi sq 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24')
                },
                'results': [
                    ['Obelia dichotoma', 143, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n', 's', 's', 's', 's', 's', 's', 's', 's', 's', 's', 'n', 's', 'n', 's', 's', 's', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n'],
                    ['Obelia geniculata', 62, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'r', 'n', None, 'n', 'r', None, None, None, None, None, None, None, None, 's', 's', 'n', 's', 'n', 'n', 'n', 's', 's', None, 's', 's', 's', None, 's', 's', None, None, None, None, None, None, None, None],
                    ...
                ]
            }
        """
        report = {
            'attr': {'columns': ('Species','n (plates)','Wilcoxon 2-24','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','Chi sq 2-24','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24')},
            'results': []
        }
        for result in results:
            species_selection = [s for s in result.species_selections[0].values()]
            species = species_selection[0]['name_latin']
            wilcoxon = result.statistics['wilcoxon_spots_repeats'][0]
            chi_squared = result.statistics['chi_squared_spots'][0]

            # Figure out for which positive spots number the result was
            # significant. A result is considered significant if 95% of the
            # tests for a plate area were significant.
            positive_spots = [-24,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
            bools = []
            for spots in positive_spots:
                stats = wilcoxon['results'].get(spots, None)
                if stats:
                    significant = float(stats['n_significant']) / wilcoxon['attr']['repeats'] >= 0.95
                    if significant:
                        # Significant: attraction or repulsion.
                        if stats['n_attraction'] > stats['n_repulsion']:
                            bools.append('a')
                        else:
                            bools.append('r')
                    else:
                        # Not significant.
                        bools.append('n')
                else:
                    # No data.
                    bools.append(None)

            # At the booleans for the Chi squared tests.
            for spots in positive_spots:
                stats = chi_squared['results'].get(spots, None)
                if stats:
                    significant = stats['p_value'] < self.alpha_level
                    if significant:
                        bools.append('s')
                    else:
                        bools.append('n')
                else:
                    # No data.
                    bools.append(None)

            # Only add the row to the report if one item in the row was
            # significant.
            for b in bools:
                if b:
                    row = [species, wilcoxon['attr']['n_plates']]
                    row.extend(bools)
                    report['results'].append(row)
                    break

        return report

    def on_thread_pool_finished(self, sender=None):
        """Display the results."""
        # Check if there are any reports to display. If not, leave.
        if len(self.results) == 0:
            self.on_analysis_closed()
            return

        # Create a summary from all results.
        summary = self.summarize_results(self.results)

        # Create a report object from the dictionary.
        report = setlyze.report.Report()
        report.set_statistics('positive_spots_summary', summary)

        # Display the report.
        w = setlyze.gui.Report(report, "Results: Batch summary for Attraction within Species")
        w.set_size_request(700, 500)

class Analysis(setlyze.analysis.common.AnalysisWorker):
    """Perform the calculations for analysis 2.

    1. Get all SETL records that match the localities+species selection and
       save these to a separate "species spots table" in the local database.

    2. Merge records with the same plate ID in the species spots table to
       make the plate IDs unique.

    3. Calculate the intra-specific spot distances from the records in the
       species spots table.

    4. Calculate expected intra-specific spot distances by generating
       random spots.

    5. Calculate the significance in difference between the observed and
       expected spot distances. Two tests of significance are performed:
       the Wilcoxon rank-sum test and the Chi-squared test.

    6. Generate the analysis report.

    Design Part: 1.4.2
    """

    def __init__(self, lock, locations_selection, species_selection):
        super(Analysis, self).__init__(lock)

        self.locations_selection = locations_selection
        self.species_selection = species_selection
        self.statistics = {
            'wilcoxon_spots': {'attr': None, 'results':{}},
            'chi_squared_spots': {'attr': None, 'results':{}},
            'wilcoxon_spots_repeats': {'attr': None, 'results':{}}
        }

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis2'))

        # Emit the signal that an analysis has started.
        setlyze.std.sender.emit('analysis-started')

    def get_total_steps(self):
        """Return the number of progress steps for this analysis.

        This equals to the total number of times we decide to update the
        progress dialog for a single analysis.

        Module constant `PROGRESS_STEPS` has to be set in the analysis module.
        """
        return PROGRESS_STEPS + self.n_repeats

    def run(self):
        """Call the necessary methods for the analysis in the right order:
            * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
              :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
            * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
              :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
            * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
            * :meth:`~setlyze.database.AccessDBGeneric.fill_plate_spot_totals_table`
            * :meth:`calculate_distances_intra`
            * :meth:`repeat_test`
            * :meth:`calculate_significance`
            * :meth:`generate_report`

        Design Part: 1.59
        """

        # Add a short delay. This gives the progress dialog time to
        # display properly.
        time.sleep(0.5)

        if not self.stopped():
            # Make an object that facilitates access to the database.
            self.db = setlyze.database.get_database_accessor()

            # Create temporary tables.
            self.db.create_table_species_spots_1()
            self.db.create_table_plate_spot_totals()
            self.db.create_table_spot_distances_observed()
            self.db.create_table_spot_distances_expected()
            self.db.conn.commit()

            # Get the record IDs that match the localities+species selection.
            rec_ids = self.db.get_record_ids(self.locations_selection, self.species_selection)
            # Create log message.
            logging.info("\tTotal records that match the species+locations selection: %d" % len(rec_ids))

            # Create log message.
            logging.info("\tCreating table with species spots...")
            # Update progress dialog.
            self.pdialog_handler.increase("Creating table with species spots...")
            # Make a spots table for the selected species.
            self.db.set_species_spots(rec_ids, slot=0)

        if not self.stopped():
            # Create log message.
            logging.info("\tMaking plate IDs in species spots table unique...")
            # Update progress dialog.
            self.pdialog_handler.increase("Making plate IDs in species spots table unique...")
            # Make the plate IDs unique.
            n_plates_unique = self.db.make_plates_unique(slot=0)
            # Create log message.
            logging.info("\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # Create log message.
            logging.info("\tSaving the positive spot totals for each plate...")
            # Update progress dialog.
            self.pdialog_handler.increase("Saving the positive spot totals for each plate...")
            # Save the positive spot totals for each plate to the database.
            self.affected, skipped = self.db.fill_plate_spot_totals_table('species_spots_1')
            # Create log message.
            logging.info("\tSkipping %d records with too few positive spots." % skipped)
            logging.info("\t  %d records remaining." % self.affected)

            # Create log message.
            logging.info("\tCalculating the intra-specific distances for the selected species...")
            # Update progress dialog.
            self.pdialog_handler.increase("Calculating the intra-specific distances for the selected species...")
            # Calculate the observed spot distances.
            self.calculate_distances_intra()

        if not self.stopped():
            # Create log message.
            logging.info("\tPerforming statistical tests with %d repeats..." %
                self.n_repeats)
            # Update progress dialog.
            self.pdialog_handler.increase("Performing statistical tests with %s repeats..." %
                self.n_repeats)
            # Perform the repeats for the statistical tests. This will repeatedly
            # calculate the expected totals, so we'll use the expected values
            # of the last repeat for the non-repeated tests.
            self.repeat_test(self.n_repeats)

        if not self.stopped():
            # Create log message.
            logging.info("\tPerforming statistical tests...")
            # Update progress dialog.
            self.pdialog_handler.increase("Performing statistical tests...")
            # Performing the statistical tests. The expected values for the last
            # repeat is used for this test.
            self.calculate_significance()

        # If the cancel button is pressed don't finish this function.
        if self.stopped():
            logging.info("Analysis aborted by user")

            # Exit gracefully.
            self.on_exit()
            return

        # Update progress dialog.
        self.pdialog_handler.increase("Generating the analysis report...")
        # Generate the report.
        self.generate_report()

        # Update progress dialog.
        self.pdialog_handler.increase("")

        # Emit the signal that the analysis has finished.
        # Note that the signal will be sent from a separate thread,
        # so we must use gobject.idle_add.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')
        logging.info("%s was completed!" % setlyze.locale.text('analysis2'))

        # Exit gracefully.
        self.on_exit()

    def calculate_distances_intra(self):
        """Calculate the intra-specific spot distances for each plate
        in the species_spots table and save the distances to the
        spot_distances_observed table in the local database.

        Design Part: 1.22
        """

        # Make a connection with the local database.
        connection = self.db.conn
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

                # Use the h/v differences to calculate the corresponding spot
                # distance.
                distance = setlyze.std.distance(h,v)

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

    def calculate_distances_intra_expected(self):
        """Calculate the expected spot distances based on the observed
        spot distances and save these to the spot_distances_expected
        table in the local database.

        Design Part: 1.23
        """

        # Make a connection with the local database.
        connection = self.db.conn
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

                # Use the h/v differences to calculate the corresponding spot
                # distance.
                distance = setlyze.std.distance(h,v)

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

    def calculate_significance(self):
        """Perform statistical tests to check if the differences between
        the means of the two sets of distances are statistically
        significant.

        We perform two statistical tests:

        1. The unpaired Wilcoxon rank sum test. We use unpaired
           because the two sets of distances are unrelated
           (:ref:`Dalgaard <ref-dalgaard>`). In other words,
           a distance n in 'observed' is unrelated to distance n in
           'expected' (where n is an item number in the lists).

        2. The Chi-squared test for given probabilities
           (:ref:`Millar <ref-dalgaard>`,
           :ref:`Dalgaard <ref-millar>`). The probabilities
           for all spot distances have been pre-calcualted. So the
           observed probabilities are compared with the pre-calculated
           probabilities.

        Based on the results of the tests we can decide which
        hypothesis we can assume to be true.

        Null hypothesis
            The species in question doesn't attract or repel itself.

        Alternative hypothesis
            The species in question attracts (mean observed < mean
            expected) or repels (mean observed > mean expected) itself.

        The decision is based on the p-value calculated by the test:

        P >= alpha level
            Assume that the null hypothesis is true.

        P < alpha level
            Assume that the alternative hypothesis is true.

        The default value for the alpha level is 0.05 (5%). In biology
        we usually assume that differences are significant if P has
        a value less than 5% (:ref:`Millar <ref-dalgaard>`).

        A high number of positive spots on a plate will naturally lead
        to a high p-value (not significant). These plates will
        negatively affect the result of statistical test. To account
        for this, the tests are performed on groups of plates. Instead of
        doing one test on all plates, we group the plates based on the
        number of positive spots they contain.

        Both tests are performed on each group. Plates of group 1 and 25
        are not tested. We skip group 1 because it is not possible to
        calculate spot distances for plates with just one positive spot.
        Plates of group 25 are ignored because this will always result
        in a p-value of 1 as a result of equal observed and expected
        spot distances.

        Both tests are also performed on groups 2-24 taken together.

        Design Part: 1.24
        """

        # Perform the tests for records that have a specific number of
        # positive spots. The tests are performed separately for each
        # number in the list. Numbers starting with "-" means all records
        # with positive spots up to that number.
        spot_totals = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,
            23,24,-24]

        for n_spots in spot_totals:
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_distances_matching_spots_total(
                'spot_distances_observed', n_spots)
            expected = self.db.get_distances_matching_spots_total(
                'spot_distances_expected', n_spots)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Get the number of plates found that match the current
            # number of positive spots.
            n_plates = self.db.matching_plates_total

            # Perform a consistency check. The number of observed and
            # expected spot distances must always be the same.
            count_observed = len(observed)
            count_expected = len(expected)
            if count_observed != count_expected:
                raise ValueError("Number of observed and expected values "
                    "are not equal. This indicates an error in the algorithm.")

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this spots number if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Save the significance result.
            if not self.statistics['wilcoxon_spots_repeats']['attr']:
                self.statistics['wilcoxon_spots_repeats']['attr'] = {
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'repeats': self.n_repeats,
                    'n_plates': self.affected,
                }

            if not self.statistics['wilcoxon_spots']['attr']:
                self.statistics['wilcoxon_spots']['attr'] = {
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                }

            self.statistics['wilcoxon_spots']['results'][n_spots] = {
                'n_plates': n_plates,
                'n_values': count_observed,
                'p_value': sig_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
                #'conf_int_start': sig_result['conf.int'][0],
                #'conf_int_end': sig_result['conf.int'][1],
            }

            # Get the probability for each spot distance. Required for
            # the Chi-squared test.
            spot_dist_to_prob = setlyze.config.cfg.get('spot-dist-to-prob-intra')

            # Get the frequencies for the observed distances. These
            # are required for the Chi-squared test.
            observed_freq = setlyze.std.distance_frequency(observed, 'intra')

            # Also perform Chi-squared test.
            sig_result = setlyze.std.chisq_test(observed_freq.values(),
                p = spot_dist_to_prob.values())

            # Save the significance result.
            if not self.statistics['chi_squared_spots']['attr']:
                self.statistics['chi_squared_spots']['attr'] = {
                    'method': sig_result['method'],
                    'n_plates': self.affected,
                }

            self.statistics['chi_squared_spots']['results'][n_spots] = {
                'n_plates': n_plates,
                'n_values': count_observed,
                'chi_squared': sig_result['statistic']['X-squared'],
                'p_value': sig_result['p.value'],
                'df': sig_result['parameter']['df'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
            }

    def calculate_significance_for_repeats(self):
        """This method does the same Wilcoxon test from :meth:`calculate_significance`,
        but instead is designed to be called repeatedly, saving the results
        of the repeated test. This method doesn't save the detailed
        results of the Wilcoxon test, but just saves whether the p-value
        was significant, and whether it was attraction or repulsion for the
        different numbers of positive spots.

        Repeation of the Wilcoxon test is necessary, as the expected values
        are calculated randomly. The test needs to be repeated many times
        if you want to draw a solid conclusion from the results.

        The number of times this method is called depends on the configuration
        setting "test-repeats".

        Design Part: 1.102
        """

        spot_totals = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,
            23,24,-24]

        for n_spots in spot_totals:
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_distances_matching_spots_total(
                'spot_distances_observed', n_spots)
            expected = self.db.get_distances_matching_spots_total(
                'spot_distances_expected', n_spots)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Perform a consistency check. The number of observed and
            # expected spot distances must always be the same.
            count_observed = len(observed)
            count_expected = len(expected)
            if count_observed != count_expected:
                raise ValueError("Number of observed and expected spot "
                    "distances are not equal. This indicates a bug "
                    "in the application.")

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this spots number if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Check if this spots number is present in the statistics variable.
            # If not, create it.
            if n_spots not in self.statistics['wilcoxon_spots_repeats']['results']:
                self.statistics['wilcoxon_spots_repeats']['results'][n_spots] = {
                    'n_plates': self.db.matching_plates_total,
                    'n_values': count_observed,
                    'n_significant': 0,
                    'n_attraction': 0,
                    'n_repulsion': 0
                }

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Save basic results for this repeated test.
            # Check if the result was significant (7P-value < alpha-level).
            p_value = float(sig_result['p.value'])
            if p_value < self.alpha_level and p_value != 'nan':
                # If so, increase significant counter with one.
                self.statistics['wilcoxon_spots_repeats']['results'][n_spots]['n_significant'] += 1

                # If significant, also check if there is preference or
                # rejection for this plate area.
                if mean_observed < mean_expected:
                    # Increase attracion counter with one.
                    self.statistics['wilcoxon_spots_repeats']['results'][n_spots]['n_attraction'] += 1
                else:
                    # Increase repulsion counter with one.
                    self.statistics['wilcoxon_spots_repeats']['results'][n_spots]['n_repulsion'] += 1

    def repeat_test(self, number):
        """Repeats the siginificance test `number` times. The significance
        test is performed by :meth:`calculate_significance_for_repeats`.

        Each time before :meth:`calculate_significance_for_repeats` is called,
        :meth:`calculate_distances_intra_expected` is called to re-calculate the
        expected values (which are random).

        Design Part: 1.103
        """

        for i in range(number):
            if self.stopped():
                return

            # Update the progess bar.
            self.pdialog_handler.increase()

            # The expected spot distances are random. So the expected values
            # differ a little on each repeat.
            self.calculate_distances_intra_expected()

            # And then we calculate the siginificance for each repeat.
            self.calculate_significance_for_repeats()

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.14
        """
        self.result.set_analysis("Attraction within Species")
        self.result.set_location_selections([self.locations_selection])
        self.result.set_species_selections([self.species_selection])
        #self.result.set_spot_distances_observed()
        #self.result.set_spot_distances_expected()
        self.result.set_statistics('wilcoxon_spots', self.statistics['wilcoxon_spots'])
        self.result.set_statistics('wilcoxon_spots_repeats', self.statistics['wilcoxon_spots_repeats'])
        self.result.set_statistics('chi_squared_spots', self.statistics['chi_squared_spots'])
