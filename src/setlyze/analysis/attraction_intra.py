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

"""This module performs analysis *Attraction within Species*.

This analysis determines whether a marine species attracts or repels
individuals of its own kind.

Two statistical tests are performed:

* Chi-squared test for given probabilities
* Wilcoxon rank sum test with continuity correction

First the analysis is prepared with :class:`Begin`, or with :class:`BeginBatch`
in batch mode. Finally the analysis is performed with :class:`Analysis`.

"""

import os
import logging
import itertools
import time
import math
import multiprocessing

import gtk

from setlyze.analysis.common import calculatestar,ProcessGateway,PrepareAnalysis,AnalysisWorker
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

class Begin(PrepareAnalysis):
    """Make the preparations for the analysis.

    The preparations can be broken down in the following steps:

        1. Show a list of all locations and let the user select from which
           locations to select species.
        2. Show a list of all species that match the locations selection and
           let the user select a species on which to perform the analysis. If
           multiple species are selected they are treated as a single species.
        3. Start the analysis with :class:`Analysis`.
        4. Display the results.

    Design Part: 1.4.1
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Beginning analysis Attraction within Species")

        # Bind handles to application signals.
        self.set_signal_handlers()

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
            'species-selection-saved': setlyze.std.sender.connect('species-selection-saved', self.on_species_selection_saved),
            # The report window was closed.
            'report-dialog-closed': setlyze.std.sender.connect('report-dialog-closed', self.on_analysis_closed),
            # Cancel button pressed.
            'analysis-canceled': setlyze.std.sender.connect('analysis-canceled', self.on_cancel_button),
            # The process pool has finished.
            'pool-finished': setlyze.std.sender.connect('pool-finished', self.on_display_results),
            # There were no results.
            'no-results': setlyze.std.sender.connect('no-results', self.on_no_results),
            # Request to repeat the analysis.
            'repeat-analysis': setlyze.std.sender.connect('repeat-analysis', self.on_repeat_analysis),
            # Request to save the individual reports for a batch analysis.
            'save-individual-reports': setlyze.std.sender.connect('save-individual-reports', self.on_save_individual_reports),
        }

    def on_select_locations(self, sender, slot=None):
        """Display the locations selection dialog.

        The "species-dialog-back" signal provides the save slot `slot`.
        """
        select = setlyze.gui.SelectLocations(slot=0)
        select.set_title(setlyze.locale.text('analysis-attraction-intra'))
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
        )

    def on_select_species(self, sender, locations_selection=None, slot=None):
        """Display the species selection dialog.

        The "locations-selection-saved" signal provides the locations selection
        `locations_selection` and the save slot `slot`.
        """
        if locations_selection:
            self.locations_selection = locations_selection
        select = setlyze.gui.SelectSpecies(self.locations_selection, width=600)
        select.set_title(setlyze.locale.text('analysis-attraction-intra'))
        select.set_description(setlyze.locale.text('select-species') + "\n\n" +
            setlyze.locale.text('selection-tips')
        )
        select.maximize()

    def on_species_selection_saved(self, sender, selection, slot):
        """Set the species selection `selection` and start the analysis.

        The "species-selection-saved" signal provides the species selection
        `species_selection` and the save slot `slot`.
        """
        self.species_selection = selection
        self.on_start_analysis(self.locations_selection, self.species_selection)

    def on_repeat_analysis(self, sender):
        """Repeat the analysis with modified options."""
        dialog = setlyze.gui.RepeatAnalysis()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            # Update the analysis options.
            self.set_analysis_options()
            # Repeat the analysis.
            self.on_start_analysis(self.locations_selection, self.species_selection)
        dialog.destroy()

    def on_start_analysis(self, locations, species):
        """Start the analysis.

        Starts the analysis with the locations selection `locations` and the
        species selection `species`.
        """
        # Create a progress dialog and a handler.
        self.pdialog, self.pdialog_handler = self.get_progress_dialog()

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps(PROGRESS_STEPS + self.n_repeats)

        # Create a progress task executor.
        gw = ProcessGateway()
        gw.set_pdialog_handler(self.pdialog_handler)
        gw.start()

        # Create a process pool with a single worker.
        self.pool = multiprocessing.Pool(1)

        # Create a list with the job.
        jobs = [(Analysis, (locations, species, gw.queue))]

        # Add the job to the pool.
        self.pool.map_async(calculatestar, jobs, callback=self.on_pool_finished)

class BeginBatch(Begin):
    """Make the preparations for the analysis in batch mode.

    This class inherits from :class:`Begin`. The preparations can be broken
    down in the following steps:

        1. Show a list of all locations and let the user select from which
           locations to select species.
        2. Show a list of all species that match the locations selection and
           let the user select a species on which to perform the analysis. If
           multiple species are selected the analysis will be repeated for each
           species.
        3. Repeat the analysis with :class:`Analysis` for each selected species.
        4. Obtain the results from all analyses and create a summary report.
        5. Display the batch report.
    """

    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")
        self.report_prefix = "attraction_intra_"

    def on_start_analysis(self, locations, species):
        """Run the analysis for each of the selected species.

        Starts the analysis with the locations selection `locations` and the
        species selection `species`.

        Creates a pool of worker processes. A job is set for each species that
        was selected. The jobs are then added to the pool for execution. If
        multiple workers were created, analyses will run in parallel. When
        the results are ready, :meth:`~setlyze.analysis.common.PrepareAnalysis.on_pool_finished`
        is applied to it.
        """
        self.start_time = time.time()

        # Create a progress dialog and a handler.
        self.pdialog, self.pdialog_handler = self.get_progress_dialog()

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps((PROGRESS_STEPS + self.n_repeats) *
            len(species))

        # Create a progress task executor.
        gw = ProcessGateway()
        gw.set_pdialog_handler(self.pdialog_handler)
        gw.start()

        # Create a process pool with workers.
        cp = setlyze.config.cfg.get('concurrent-processes')
        self.pool = multiprocessing.Pool(cp)

        # Create a list of jobs.
        logging.info("Adding %d jobs to the queue" % len(species))
        jobs = ((Analysis, (locations, sp, gw.queue)) for sp in species)

        # Add the jobs to the pool.
        self.pool.map_async(calculatestar, jobs, callback=self.on_pool_finished)

    def summarize_results(self, results):
        """Return a summary report from a list of analysis reports `results`.

        Creates a dictionary in the following format ::

            {
                'attr': {
                    'columns_over': ('..', 'Wilcoxon rank sum test', 'Chi-squared test'),
                    'columns_over_spans': (2, 24, 24),
                    'columns': ('Species', 'n (plates)', 'Wilcoxon 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', 'Chi sq 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24')
                },
                'results': [
                    ['Obelia dichotoma', 143, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n', 's', 's', 's', 's', 's', 's', 's', 's', 's', 's', 'n', 's', 'n', 's', 's', 's', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n'],
                    ['Obelia geniculata', 62, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'r', 'n', None, 'n', 'r', None, None, None, None, None, None, None, None, 's', 's', 'n', 's', 'n', 'n', 'n', 's', 's', None, 's', 's', 's', None, 's', 's', None, None, None, None, None, None, None, None],
                    ...
                ]
            }
        """
        summary = {
            'attr': {
                'columns_over': ('..', 'Wilcoxon rank sum test', 'Chi-squared test'),
                'columns_over_spans': (2, 24, 24),
                'columns': ('Species','n (plates)','2-24','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','2-24','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24')
            },
            'results': []
        }
        for result in results:
            chi_squared = None
            wilcoxon = None
            species_selection = [s for s in result.species_selections[0].values()]
            species = species_selection[0]['name_latin']
            if 'wilcoxon_spots_repeats' in result.statistics:
                wilcoxon = result.statistics['wilcoxon_spots_repeats'][0]
            if 'chi_squared_spots' in result.statistics:
                chi_squared = result.statistics['chi_squared_spots'][0]

            # Figure out for which positive spots number the result was
            # significant. A result is considered significant if
            # (confidence level)% of the test repeats were significant.
            positive_spots = [-24,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
            row = []
            for spots in positive_spots:
                if not wilcoxon:
                    row.append(None)
                    continue
                stats = wilcoxon['results'].get(spots, None)
                if stats:
                    significant = float(stats['n_significant']) / wilcoxon['attr']['repeats'] >= 1-self.alpha_level
                    if significant:
                        # Significant: attraction or repulsion.
                        if stats['n_attraction'] > stats['n_repulsion']:
                            row.append('at')
                        else:
                            row.append('rp')
                    else:
                        # Not significant.
                        row.append('n')
                else:
                    # No data.
                    row.append(None)

            # Add the results for the Chi squared tests.
            for spots in positive_spots:
                if not chi_squared:
                    row.append(None)
                    continue
                stats = chi_squared['results'].get(spots, None)
                if stats:
                    # Check if the result was significant. When all values are
                    # 0 the p-value will be NaN. Function `is_significant` will
                    # raise ValueError if the p-value is NaN.
                    try:
                        significant = setlyze.std.is_significant(stats['p_value'], self.alpha_level)
                    except ValueError:
                        significant = False

                    if significant:
                        if stats['mean_observed'] < stats['mean_expected']:
                            code = 'at'
                        else:
                            code = 'rp'
                        row.append("%s; chi-sq=%.2f; p=%.4f" %
                            (code, stats['chi_squared'], stats['p_value']))
                    else:
                        # Not significant.
                        row.append('n')
                else:
                    # No data.
                    row.append(None)

            # Only add the row to the report if one item in the row was
            # significant.
            for c in row:
                if c in (None,'n'):
                    continue
                else:
                    r = [species, result.get_option('Total plates')]
                    r.extend(row)
                    summary['results'].append(r)
                    break

        # Create a report object from the dictionary.
        report = setlyze.report.Report()
        report.set_statistics('positive_spots_summary', summary)
        return report

    def on_display_results(self, sender, results=[]):
        """Create a summary report and display it in a report dialog.

        This method is used as a handler for the "pool-finished" signal.
        The batch results `results` are attached to the signal.
        """
        report = self.summarize_results(results)

        # Set analysis options.
        report.set_option('Alpha level', self.alpha_level)
        report.set_option('Repeats', self.n_repeats)
        report.set_option('Statistical tests', "Chi-squared test, Wilcoxon rank sum test")
        if self.elapsed_time:
            report.set_option('Running time', setlyze.std.seconds_to_hms(self.elapsed_time))

        # Set a definition list for the report.
        definitions = {
            'n': "The result for the statistical test was not significant.",
            'at': "There was a significant attraction for the species in question.",
            'rp': "There was a significant repulsion for the species in question.",
            'na': "There is not enough data for the analysis or in case of the\n"
                  "  Chi Squared test one of the expected frequencies is less than 5.",
        }
        report.set_definitions(definitions)

        # Display the report.
        w = setlyze.gui.Report(report, "Batch report for analysis Attraction within Species")
        # Enable export of individual reports.
        if len(self.results) > 0:
            w.toolbutton_save_all.set_sensitive(True)

class Analysis(AnalysisWorker):
    """Perform the calculations for the analysis.

    Argument `locations` is the locations selection, `species` is the species
    selection, and `execute_queue` is an optional
    :class:`~setlyze.analysis.common.ProcessGateway` queue.

    The analysis can be broken down in the following steps:

        1. Get all SETL records that match the localities+species selection and
           save these to a separate "species spots table" in the local database.
        2. Merge records with the same plate ID in the species spots table to
           make the plate IDs unique.
        3. Calculate the intra specific spot distances from the records in the
           species spots table.
        4. Calculate expected intra-specific spot distances by generating
           random spots.
        5. Perform the Wilcoxon rank sum tests with repeats to calculate the
           significance in difference between the observed and expected spot
           distances.
        6. Perform a single Wilcoxon rank sum tests.
        7. Perform the Chi-squared test to calculate the significance in
           difference between the observed and expected spot distances.
        8. Generate the analysis report.

    Design Part: 1.4.2
    """

    def __init__(self, locations, species, execute_queue=None):
        super(Analysis, self).__init__(execute_queue)
        logging.info("Performing %s" % setlyze.locale.text('analysis-attraction-intra'))
        self.locations_selection = locations
        self.species_selection = species
        self.statistics = {
            'wilcoxon_spots': {'attr': None, 'results':{}},
            'chi_squared_spots': {'attr': None, 'results':{}},
            'wilcoxon_spots_repeats': {'attr': None, 'results':{}}
        }

    def run(self):
        """Perform the analysis and return the analysis report.

        Calls the necessary methods for the analysis in the right order
        and do some data checks:

        * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
          :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
        * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
          :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
        * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
        * :meth:`~setlyze.database.AccessDBGeneric.fill_plate_spot_totals_table`
        * :meth:`calculate_distances_intra`
        * :meth:`repeat_wilcoxon_test`
        * :meth:`calculate_significance`
        * :meth:`generate_report`

        Design Part: 1.59
        """
        if not self.stopped():
            # Make an object that facilitates access to the database.
            self.db = setlyze.database.get_database_accessor()

            # Create temporary tables.
            self.db.create_table_species_spots_1()
            self.db.create_table_plate_spot_totals()
            self.db.create_table_spot_distances_observed()
            self.db.create_table_spot_distances_expected()
            self.db.conn.commit()

            # Get the record IDs that match the locations + species selection.
            rec_ids = self.db.get_record_ids(self.locations_selection, self.species_selection)
            logging.info("\tTotal records that match the species+locations selection: %d" % len(rec_ids))

            # Make a spots table for the selected species.
            logging.info("\tCreating table with species spots...")
            self.exec_task('progress.increase', "Creating table with species spots...")
            self.db.set_species_spots(rec_ids, slot=0)

        if not self.stopped():
            # Combine records with the same plate ID.
            logging.info("\tCombining records with the same plate ID...")
            self.exec_task('progress.increase', "Combining records with the same plate ID...")
            n_plates_unique = self.db.make_plates_unique(slot=0)
            logging.info("\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # Save the positive spot totals for each plate to the database.
            logging.info("\tSaving the positive spot totals for each plate...")
            self.exec_task('progress.increase', "Saving the positive spot totals for each plate...")
            self.affected, skipped = self.db.fill_plate_spot_totals_table('species_spots_1')
            logging.info("\tSkipping %d records with too few positive spots." % skipped)
            logging.info("\t  %d records remaining." % self.affected)

            # Calculate the observed spot distances.
            logging.info("\tCalculating the intra-specific distances for the selected species...")
            self.exec_task('progress.increase', "Calculating the intra-specific distances for the selected species...")
            self.calculate_distances_intra()

        if not self.stopped():
            # Perform the repeats for the Wilcoxon rank sum test. This will
            # repeatedly calculate the expected totals. The expected values of
            # the last repeat will be used for the non-repeated Wilcoxon test.
            logging.info("\tPerforming statistical tests with %d repeats..." %
                self.n_repeats)
            self.exec_task('progress.increase',
                "Performing statistical tests with %s repeats..." %
                self.n_repeats)
            self.repeat_wilcoxon_test(self.n_repeats)

        if not self.stopped():
            # Perform the Chi-squared and Wilcoxon rank sum test (non-repeated).
            # The expected values for the last repeat is used for this Wilcoxon
            # test.
            logging.info("\tPerforming statistical tests...")
            self.exec_task('progress.increase', "Performing statistical tests...")
            self.calculate_significance()

        # If the cancel button is pressed don't finish this function.
        if self.stopped():
            logging.info("Analysis aborted by user")
            self.on_exit()
            return None

        # Generate the report.
        self.exec_task('progress.increase', "Generating the analysis report...")
        self.generate_report()

        # Update the progress bar.
        logging.info("%s was completed!" % setlyze.locale.text('analysis-attraction-intra'))
        self.exec_task('progress.increase', "")

        # Run finalizers.
        self.on_exit()

        # Return the result.
        return self.result

    def calculate_distances_intra(self):
        """Calculate the intra specific spot distances.

        This is done for each plate in the species_spots table and the
        distances are saved to the spot_distances_observed table in the local
        database.

        Design Part: 1.22
        """
        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_observed table before we use it again.
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
            # Get all possible positive spot combinations for each plate.
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
        cursor.close()
        cursor2.close()

    def calculate_distances_intra_expected(self):
        """Calculate the expected spot distances.

        This is based on the observed spot distances and they are saved to the
        spot_distances_expected table in the local database.

        Design Part: 1.23
        """
        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_expected table before we use it again.
        cursor.execute("DELETE FROM spot_distances_expected")
        connection.commit()

        # Get the number of positive spots for each plate. This will serve
        # as a template for the random spots.
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
        cursor.close()
        cursor2.close()

    def calculate_significance(self):
        """Perform statistical tests to check for significant differences.

        The differences between the observed and expected spot distances are
        checked.

        We perform two statistical tests:

        1. The unpaired Wilcoxon rank sum test. We use unpaired because the two
           sets of distances are unrelated (:ref:`Dalgaard <ref-dalgaard>`). In
           other words, a distance n in 'observed' is unrelated to distance n
           in 'expected' (where n is an item number in the lists).

        2. The Chi-squared test for given probabilities
           (:ref:`Millar <ref-dalgaard>`, :ref:`Dalgaard <ref-millar>`). The
           probabilities for all spot distances have been pre-calcualted. So
           the observed probabilities are compared with the pre-calculated
           probabilities.

           For the Chi-squared test the expected frequencies should not be
           less than 5 (:ref:`Buijs <ref-buijs>`). If we find an expected
           frequency that is less than 5, the result for this test is not
           saved.

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

            # Get the lengths.
            count_observed = len(observed)
            count_expected = len(expected)

            # The number of observed and expected spot distances must always
            # be the same.
            assert count_observed == count_expected, \
                "Number of observed and expected values are not equal."

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this spots number if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform the two sample Wilcoxon test.
            test_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Set some test attributes for the report.
            if not self.statistics['wilcoxon_spots_repeats']['attr']:
                self.statistics['wilcoxon_spots_repeats']['attr'] = {
                    'method': test_result['method'],
                    'alternative': test_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'repeats': self.n_repeats,
                    'groups': 'spots',
                }
            if not self.statistics['wilcoxon_spots']['attr']:
                self.statistics['wilcoxon_spots']['attr'] = {
                    'method': test_result['method'],
                    'alternative': test_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'groups': 'spots',
                }

            # Save the test result.
            self.statistics['wilcoxon_spots']['results'][n_spots] = {
                'n_plates': n_plates,
                'n_values': count_observed,
                'p_value': test_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
            }

            # Get the probability for each spot distance (used for the
            # Chi-squared test).
            spot_dist_to_prob = setlyze.config.cfg.get('spot-dist-to-prob-intra')

            # Get the frequencies for the observed distances (used for the
            # Chi-squared test).
            observed_freq = setlyze.std.distance_frequency(observed, 'intra')

            # Also perform the Chi-squared test.
            test_result = setlyze.std.chisq_test(observed_freq.values(),
                p = spot_dist_to_prob.values())

            # If we find an expected frequency that is less than 5, do not save
            # the result.
            for f in test_result['expected']:
                if f < 5:
                    continue

            # Save the test result.
            if not self.statistics['chi_squared_spots']['attr']:
                self.statistics['chi_squared_spots']['attr'] = {
                    'method': test_result['method'],
                    'groups': 'spots',
                }
            self.statistics['chi_squared_spots']['results'][n_spots] = {
                'n_plates': n_plates,
                'n_values': count_observed,
                'chi_squared': test_result['statistic']['X-squared'],
                'p_value': test_result['p.value'],
                'df': test_result['parameter']['df'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
            }

    def repeat_wilcoxon_test(self, n):
        """Repeat the Wilcoxon rank sum test `n` times.

        The significance test is performed by
        :meth:`wilcoxon_test_for_repeats`.

        Each time before :meth:`wilcoxon_test_for_repeats` is called,
        :meth:`calculate_distances_intra_expected` is called to re-calculate
        the expected values (which are random).

        Design Part: 1.103
        """
        for i in range(n):
            if self.stopped():
                return

            # Update the progess bar.
            self.exec_task('progress.increase')

            # The expected spot distances are random. So the expected values
            # differ a little on each repeat.
            self.calculate_distances_intra_expected()

            # And then we calculate the siginificance for each repeat.
            self.wilcoxon_test_for_repeats()

    def wilcoxon_test_for_repeats(self):
        """Perform the Wilcoxon rank sum test for repeats.

        This method does the same Wilcoxon test from :meth:`calculate_significance`,
        but it is designed to be called repeatedly, saving the results
        of the repeated test. This method doesn't save the detailed
        results of the Wilcoxon test, but just saves whether the p-value
        was significant, and whether it was attraction or repulsion for the
        different numbers of positive spots.

        Repeation of the Wilcoxon test is necessary because the expected values
        are calculated randomly. The test needs to be repeated many times if
        you want to draw a solid conclusion from the test.

        This method will be put in a loop by :meth:`repeat_wilcoxon_test`.

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

            # Get the list lengths.
            count_observed = len(observed)
            count_expected = len(expected)

            # The number of observed and expected spot distances must always
            # be the same.
            assert count_observed == count_expected, \
                "Number of observed and expected values are not equal."

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
            test_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Check if the result was significant. When all values are
            # 0 the p-value will be NaN. Function `is_significant` will
            # raise ValueError if the p-value is NaN.
            try:
                significant = setlyze.std.is_significant(test_result['p.value'], self.alpha_level)
            except ValueError:
                significant = False

            if significant:
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

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.14
        """
        self.result.set_analysis("Attraction within Species")
        self.result.set_option('Alpha level', self.alpha_level)
        self.result.set_option('Repeats', self.n_repeats)
        self.result.set_option('Total plates', self.affected)
        self.result.set_location_selections([self.locations_selection])
        self.result.set_species_selections([self.species_selection])
        self.result.set_statistics('wilcoxon_spots', self.statistics['wilcoxon_spots'])
        self.result.set_statistics('wilcoxon_spots_repeats', self.statistics['wilcoxon_spots_repeats'])
        self.result.set_statistics('chi_squared_spots', self.statistics['chi_squared_spots'])
