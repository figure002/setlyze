#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010-2013, GiMaRIS <info@gimaris.com>
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

"""This module performs analysis *Attraction between Species*.

This analysis determines whether two different marine species attract or repel
each other.

Two statistical tests are performed:

* Chi-squared test for given probabilities
* Wilcoxon rank sum test with continuity correction

First the analysis is prepared with :class:`Begin`, or with :class:`BeginBatch`
in batch mode. Finally the analysis is performed with :class:`Analysis`.

"""

import logging
import itertools
import time
import math
import multiprocessing
import re

import gtk

import setlyze
from setlyze.analysis.common import (calculatestar, ProcessGateway,
    PrepareAnalysis, AnalysisWorker)
import setlyze.config
import setlyze.gui
import setlyze.locale
import setlyze.std
from setlyze.stats import chisq_test, wilcox_test
import setlyze.report

# The number of progress steps for this analysis.
PROGRESS_STEPS = 10

class Begin(PrepareAnalysis):
    """Make the preparations for the analysis.

    The preparations can be broken down in the following steps:

        1. Show a list of all locations and let the user select from which
           locations to select species.
        2. Show a list of all species that match the locations selection and
           let the user perform the first species selection. If multiple
           species are selected they are treated as a single species.
        3. Show a list of all species that match the locations selection and
           let the user perform the second species selection. If multiple
           species are selected they are treated as a single species.
        4. Start the analysis with :class:`Analysis`.
        5. Display the results.

    Design Part: 1.5.1
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Beginning analysis Attraction between Species")

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Reset the save slot.
        setlyze.sender.set_property('save-slot', 0)

        # Emit the signal that an analysis has started.
        setlyze.sender.emit('beginning-analysis')

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            # This analysis has just started.
            'beginning-analysis': setlyze.sender.connect('beginning-analysis', self.on_select_locations),
            # The user pressed the X button of a locations/species selection window.
            'selection-dialog-closed': setlyze.sender.connect('selection-dialog-closed', self.on_analysis_closed),
            # User pressed the Back button in the locations selection window.
            'locations-dialog-back': setlyze.sender.connect('locations-dialog-back', self.on_analysis_closed),
            # User pressed the Back button in the species selection window.
            'species-dialog-back': setlyze.sender.connect('species-dialog-back', self.on_species_back),
            # The user selected locations have been saved.
            'locations-selection-saved': setlyze.sender.connect('locations-selection-saved', self.on_locations_saved),
            # The user selected species have been saved.
            'species-selection-saved': setlyze.sender.connect('species-selection-saved', self.on_species_saved),
            # The report window was closed.
            'report-dialog-closed': setlyze.sender.connect('report-dialog-closed', self.on_analysis_closed),
            # Cancel button pressed.
            'analysis-canceled': setlyze.sender.connect('analysis-canceled', self.on_cancel_button),
            # The process pool has finished.
            'pool-finished': setlyze.sender.connect('pool-finished', self.on_display_results),
            # There were no results.
            'no-results': setlyze.sender.connect('no-results', self.on_no_results),
            # Request to repeat the analysis.
            'repeat-analysis': setlyze.sender.connect('repeat-analysis', self.on_repeat_analysis),
            # Request to save the individual reports for a batch analysis.
            'save-individual-reports': setlyze.sender.connect('save-individual-reports', self.on_save_individual_reports),
        }

    def on_select_locations(self, sender, slot=None):
        """Display the locations selection dialog.

        The "species-dialog-back" signal provides the save slot `slot`.
        """
        select = setlyze.gui.SelectLocations()
        select.set_title(setlyze.locale.text('analysis-attraction-inter'))
        select.set_header("Locations Selection")
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
        )

    def on_locations_saved(self, sender, selection=None, slot=None):
        """Handler for the "locations-selection-saved" signal.

        The "locations-selection-saved" signal provides the locations selection
        `selection` and the save slot `slot`.

        When the locations selection was made it shows the first species
        selection dialog.
        """
        if selection:
            # Use the same locations selection for both species selections.
            self.locations_selection = selection
            self.locations_selections = [selection,selection]
        self.on_select_species()

    def on_select_species(self):
        """Display the species selection dialog."""
        save_slot = setlyze.sender.get_property('save-slot')
        select = setlyze.gui.SelectSpecies(self.locations_selection, width=600,
            slot=save_slot)
        select.set_title(setlyze.locale.text('analysis-attraction-inter'))
        if self.in_batch_mode():
            select.set_description( setlyze.locale.text('select-species-batch-mode-inter') +
                "\n\n" + setlyze.locale.text('selection-tips')
            )
        else:
            select.set_description( setlyze.locale.text('select-species') +
                "\n\n" + setlyze.locale.text('selection-tips')
            )
        select.maximize()

        if self.in_batch_mode():
            # In batch mode at least two species must be selected.
            select.set_selection_minimum(2,
                "Please select at least two species from the list.")
        else:
            # In normal mode we have two separate species selections.
            if save_slot == 0:
                select.set_header("First Species Selection")
            elif save_slot == 1:
                select.set_header("Second Species Selection")

    def on_species_back(self, sender, slot=0):
        """Handler for the "species-dialog-back" signal.

        The "species-dialog-back" signal provides the save slot `slot`.

        If the Back button on the first species selection dialog was clicked
        (`slot` is set to 0) the locations selection dialog is shown.
        If the Back button on the second species selection dialog was clicked
        (`slot` is set to 1) the first species selection dialog is shown.
        """
        if slot == 0:
            self.on_select_locations(sender, slot)
        elif slot == 1:
            sender.set_property('save-slot', 0)
            self.on_select_species()

    def on_species_saved(self, sender, selection, slot):
        """Handler for the "species-selection-saved" signal.

        The "species-selection-saved" signal provides the species selection
        `selection` and the save slot `slot`.

        If the first species selection was made (`slot` is set to 0) it
        shows the second species selection dialog. If the second species
        selection was made (`slot` is set to 1) it starts the analysis.
        """
        if self.in_batch_mode():
            # In batch mode we need only one species selection.
            self.species_selection = selection
            self.on_start_analysis(self.locations_selections, self.species_selection)
        else:
            # In normal mode we need two species selections.
            self.species_selections[slot] = selection
            if slot == 0:
                sender.set_property('save-slot', 1)
                self.on_select_species()
            elif slot == 1:
                self.on_start_analysis(self.locations_selections, self.species_selections)

    def on_repeat_analysis(self, sender):
        """Repeat the analysis with modified options."""
        dialog = setlyze.gui.RepeatAnalysis()
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            # Update the analysis options.
            self.set_analysis_options()
            # Repeat the analysis.
            if self.in_batch_mode():
                self.on_start_analysis(self.locations_selections, self.species_selection)
            else:
                self.on_start_analysis(self.locations_selections, self.species_selections)
        dialog.destroy()

    def on_start_analysis(self, locations, species):
        """Start the analysis.

        Starts the analysis with the locations selections `locations` and the
        species selections `species`. Both must be tuples containing two lists,
        each list being a selection.
        """
        assert len(locations) == 2, \
            "The locations tuple does not contain two items."
        assert len(species) == 2, \
            "The species tuple does not contain two items."

        # Create a progress dialog and a handler.
        self.pdialog, self.pdialog_handler = self.get_progress_dialog()

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps(
            PROGRESS_STEPS + self.n_repeats
        )

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
           let the user perform the species selection. If multiple
           species are selected the analysis will be repeated for each
           possible inter species combination of the selected species.
        3. Repeat the analysis with :class:`Analysis` for each possible inter
           species combination.
        4. Obtain the results from all analyses and create a summary report.
        5. Display the batch report.
    """

    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")
        self.report_prefix = "attraction_inter_"

    def on_start_analysis(self, locations, species):
        """Run the analysis for all possible inter species combinations.

        Creates a pool of worker processes. A job is set for every possible
        inter species combination of the species selection. The jobs are then
        added to the pool for execution. If multiple workers were created,
        analyses will run in parallel. When the results are ready,
        :meth:`~setlyze.analysis.common.PrepareAnalysis.on_pool_finished` is
        applied to it.
        """
        assert len(locations) == 2, \
            "The locations tuple does not contain two items."
        assert len(species) > 1, \
            "The species tuple has less than two items."

        self.start_time = time.time()

        # Get all inter species combinations for the species selection.
        species_combos = tuple(itertools.combinations(species, 2))

        # Create a progress dialog and a handler.
        self.pdialog, self.pdialog_handler = self.get_progress_dialog()

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps(
            (PROGRESS_STEPS + self.n_repeats) * len(species_combos)
        )

        # Create a progress task executor.
        gw = ProcessGateway()
        gw.set_pdialog_handler(self.pdialog_handler)
        gw.start()

        # Create a process pool with workers.
        cp = setlyze.config.cfg.get('concurrent-processes')
        self.pool = multiprocessing.Pool(cp, maxtasksperchild=50)

        # Create a list of jobs.
        logging.info("Adding %d jobs to the queue" % len(species_combos))
        jobs = ((Analysis, (locations, sp_comb, gw.queue)) for sp_comb in species_combos)

        # Add the jobs to the pool.
        self.pool.map_async(calculatestar, jobs, callback=self.on_pool_finished)

    def summarize_results(self, results):
        """Return a summary report from a list of analysis reports `results`.

        Creates a dictionary in the following format ::

            {
                'attr': {
                    'columns_over': ('..', 'Wilcoxon rank sum test', 'Chi-squared test'),
                    'columns_over_spans': (3, 6, 6),
                    'columns': ('Species A', 'Species B', 'n (plates)', 'Wilcoxon 1-5', '1', '2', '3', '4', '5', 'Chi sq 1-5', '1', '2', '3', '4', '5')
                },
                'results': [
                    ['Obelia dichotoma', 'Obelia geniculata', 12, 'n', 'r', 'a', 'n', None, None, 'n', 's', 's', 'n', None, None],
                    ['Obelia dichotoma', 'Obelia longissima', 73, 'r', 'r', 'r', 'r', 'r', 'r', 's', 's', 's', 's', 's', 's'],
                    ...
                ]
            }
        """
        summary = {
            'attr': {
                'columns_over': ('..', 'Wilcoxon rank sum test', 'Chi-squared test'),
                'columns_over_spans': (3, 6, 6),
                'columns': ('Species A','Species B','n (plates)','1-5','1','2','3','4','5','1-5','1','2','3','4','5')
            },
            'results': []
        }
        for result in results:
            chi_squared = None
            wilcoxon = None
            species_selection = [s for s in result.species_selections[0].values()]
            species_a = species_selection[0]['name_latin']
            species_selection = [s for s in result.species_selections[1].values()]
            species_b = species_selection[0]['name_latin']

            if 'wilcoxon_ratios_repeats' in result.statistics:
                wilcoxon = result.statistics['wilcoxon_ratios_repeats'][0]
            if 'chi_squared_ratios' in result.statistics:
                chi_squared = result.statistics['chi_squared_ratios'][0]

            # Figure out for which ratio groups the result was
            # significant. A result is considered significant if
            # (confidence level)% of the test repeats were significant.
            ratio_groups = [-5,1,2,3,4,5]
            row = []
            for ratio in ratio_groups:
                if not wilcoxon:
                    row.append(None)
                    continue
                stats = wilcoxon['results'].get(ratio, None)
                if stats:
                    # Calculate the P-value.
                    # Attraction and repulsion should not be summed up
                    # because they contradict. Only use the major value.
                    if stats['n_attraction'] > stats['n_repulsion']:
                        major = stats['n_attraction']
                    else:
                        major = stats['n_repulsion']
                    p = 1 - float(major) / wilcoxon['attr']['repeats']

                    if setlyze.std.is_significant(p, self.alpha_level):
                        if stats['n_attraction'] > stats['n_repulsion']:
                            code = 'at'
                        else:
                            code = 'rp'
                    else:
                        code = 'ns'
                    row.append("%s; p=%.4f" % (code,p))
                else:
                    # No data.
                    row.append(None)

            # Add the results for the Chi squared tests.
            for ratio in ratio_groups:
                if not chi_squared:
                    row.append(None)
                    continue
                stats = chi_squared['results'].get(ratio, None)
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
                    else:
                        code = 'ns'

                    row.append("%s; χ²=%.2f; p=%.4f" %
                        (code, stats['chi_squared'], stats['p_value']))
                else:
                    # No data.
                    row.append(None)

            # Only add the row to the report if one item in the row was
            # significant.
            for val in row:
                if val and re.match('^(s|at|rp);', val):
                    r = [species_a, species_b, result.get_option('Total plates')]
                    r.extend(row)
                    summary['results'].append(r)
                    break

        # Create a report object from the dictionary.
        report = setlyze.report.Report()
        report.set_statistics('ratio_groups_summary', summary)
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
            'ns': "The result for the statistical test was not significant.",
            'at': "There was a significant attraction for the species in question.",
            'rp': "There was a significant repulsion for the species in question.",
            'na': "There is not enough data for the analysis or in case of the\n"
                  "  Chi Squared test one of the expected frequencies is less than 5.",
        }
        report.set_definitions(definitions)

        # Display the report.
        w = setlyze.gui.Report(report,
            "Batch report for analysis Attraction between Species",
            'summary-report-attraction-between-species')
        # Enable export of individual reports.
        if len(self.results) > 0:
            w.toolbutton_save_all.set_sensitive(True)

class Analysis(AnalysisWorker):
    """Perform the calculations for the analysis.

    Argument `locations` is the locations selection, `species` is the species
    selection, and `execute_queue` is an optional
    :class:`~setlyze.analysis.common.ProcessGateway` queue.

    The analysis can be broken down in the following steps:

        1. Get all SETL records that match the localities + first species
           selection and save these to table "species_spots_1" in the local
           database.
        2. Merge records with the same plate ID in table "species_spots_1" to
           make the plate IDs unique.
        3. Get all SETL records that match the localities + second species
           selection and save these to table "species_spots_2" in the local
           database.
        4. Merge records with the same plate ID in table "species_spots_2" to
           make the plate IDs unique.
        5. Calculate the inter specific spot distances from the records in both
           species spots tables and save the distances to table
           "spot_distances_observed" in the local database.
        6. Calculate expected inter specific spot distances by generating
           random spots and save the distances to table
           "spot_distances_expected" in the local database.
        7. Calculate the significance in difference between the observed and
           expected spot distances. Two tests of significance are performed:
           the Wilcoxon rank-sum test and the Chi-squared test.
        8. Generate the analysis report.

    Design Part: 1.5.2
    """

    def __init__(self, locations, species, execute_queue=None):
        super(Analysis, self).__init__(execute_queue)
        logging.info("Performing %s" % setlyze.locale.text('analysis-attraction-inter'))
        self.locations_selections = locations
        self.species_selections = species
        self.statistics = {
            'wilcoxon_ratios': {'attr': None, 'results':{}},
            'chi_squared_ratios': {'attr': None, 'results':{}},
            'wilcoxon_ratios_repeats': {'attr': None, 'results':{}}
        }

    def run(self):
        """Perform the analysis and return the analysis report.

        Calls the necessary methods for the analysis in the right order
        and do some data checks:

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
        * :meth:`~setlyze.database.AccessDBGeneric.fill_plate_spot_totals_table`
        * :meth:`calculate_distances_inter`
        * :meth:`repeat_wilcoxon_test`
        * :meth:`calculate_significance`
        * :meth:`generate_report`

        Design Part: 1.60
        """
        if not self.stopped():
            # Make an object that facilitates access to the database.
            self.db = setlyze.database.get_database_accessor()

            # Create temporary tables.
            self.db.create_table_species_spots_1()
            self.db.create_table_species_spots_2()
            self.db.create_table_plate_spot_totals()
            self.db.create_table_spot_distances_observed()
            self.db.create_table_spot_distances_expected()
            self.db.conn.commit()

        if not self.stopped():
            # SELECTION 1

            # Get the record IDs that match the selections.
            self.exec_task('progress.increase', "Creating first table with species spots...")
            rec_ids1 = self.db.get_record_ids(self.locations_selections[0], self.species_selections[0])
            logging.info("\tTotal records that match the first species+locations selection: %d" % len(rec_ids1))

            # Make a spots table for both species selections.
            logging.info("\t\tCreating first table with species spots...")
            self.db.set_species_spots(rec_ids1, slot=0)

            # Combine records with the same plate ID.
            self.exec_task('progress.increase', "Combining records with the same plate ID...")
            logging.info("\t\tCombining records with the same plate ID...")
            n_plates_unique = self.db.make_plates_unique(slot=0)
            logging.info("\t\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # SELECTION 2

            # Get the record IDs that match the selections.
            self.exec_task('progress.increase', "Creating second table with species spots...")
            rec_ids2 = self.db.get_record_ids(self.locations_selections[1], self.species_selections[1])
            logging.info("\tTotal records that match the second species+locations selection: %d" % len(rec_ids2))

            # Make a spots table for both species selections.
            logging.info("\t\tCreating second table with species spots...")
            self.db.set_species_spots(rec_ids2, slot=1)

            # Combine records with the same plate ID.
            self.exec_task('progress.increase', "Combining records with the same plate ID...")
            logging.info("\t\tCombining records with the same plate ID...")
            n_plates_unique = self.db.make_plates_unique(slot=1)
            logging.info("\t\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # Save the positive spot totals for each plate to the database.
            logging.info("\tSaving the positive spot totals for each plate...")
            self.exec_task('progress.increase', "Saving the positive spot totals for each plate...")
            self.affected, skipped = self.db.fill_plate_spot_totals_table('species_spots_1','species_spots_2')

            # Calculate the observed spot distances.
            self.exec_task('progress.increase', "Calculating the inter-specific distances for the selected species...")
            logging.info("\tCalculating the inter-specific distances for the selected species...")
            self.calculate_distances_inter()

            # Perform the repeats for the Wilcoxon rank sum test. This will
            # repeatedly calculate the expected totals. The expected values of
            # the last repeat will be used for the non-repeated Wilcoxon test.
            logging.info("\tPerforming statistical tests with %d repeats..." %
                self.n_repeats)
            self.exec_task('progress.increase', "Performing statistical tests with %s repeats..." %
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
        logging.info("\tGenerating the analysis report...")
        self.exec_task('progress.increase', "Generating the analysis report...")
        self.generate_report()

        # Update progress dialog.
        logging.info("%s was completed!" % setlyze.locale.text('analysis-attraction-inter'))
        self.exec_task('progress.increase', "")

        # Run finalizers.
        self.on_exit()

        # Return the result.
        return self.result

    def generate_spot_ratio_groups(self):
        """Return an iterator that returns the ratio groups.

        Each returned group is a list of ratios in the form of two-item
        tuples.
        """
        for end in range(6, 31, 5):
            previous_end = end-5

            # Plates where one species has all 25 spots covered are not
            # expected to be significant. So we exclude these from the
            # ratios.
            if end == 26:
                end = 25

            # Get the ratios for this group.
            group = itertools.combinations_with_replacement(xrange(1,end), 2)
            group = list(group)

            if end > 6:
                # Remove the ratios of the previous groups from the current group.
                remove = itertools.combinations_with_replacement(xrange(1,previous_end), 2)
                setlyze.std.remove_items_from_list(group,remove)

            # Yield the ratios for this group.
            yield group

        # Lastly, yield all ratios (excluding the ones containing 25)
        all_ratios = list(itertools.combinations_with_replacement(xrange(1,25), 2))
        yield all_ratios

    def calculate_distances_inter(self):
        """Calculate the inter specific spot distances.

        This is done for each plate in the species_spots tables and the
        distances are saved to the "spot_distances_observed" table in the local
        database.

        Design Part: 1.27
        """
        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_observed table before we use it again.
        cursor.execute("DELETE FROM spot_distances_observed")
        connection.commit()

        # Get all records from both spots tables where the plate IDs
        # match.
        # Each returned record has this format:
        # id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|
        # rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|
        # rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|
        # rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|
        # rec_sur24|rec_sur25|id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|
        # rec_sur4|rec_sur5|rec_sur6|rec_sur7|rec_sur8|rec_sur9|
        # rec_sur10|rec_sur11|rec_sur12|rec_sur13|rec_sur14|rec_sur15|
        # rec_sur16|rec_sur17|rec_sur18|rec_sur19|rec_sur20|rec_sur21|
        # rec_sur22|rec_sur23|rec_sur24|rec_sur25
        cursor.execute( "SELECT s1.*, s2.* FROM species_spots_1 as s1 "
                        "INNER JOIN species_spots_2 as s2 "
                        "ON s1.rec_pla_id=s2.rec_pla_id"
                        )

        for record in cursor:
            record1 = record[2:27]
            record2 = record[29:54]
            plate_id = record[1]

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

                # Use the h/v differences to calculate the corresponding spot
                # distance.
                distance = setlyze.std.distance(h,v)

                # Save the observed spot distances to the database.
                cursor2.execute( "INSERT INTO spot_distances_observed "
                                 "VALUES (null,?,?)",
                                 (plate_id, distance)
                                )

        # Commit the transaction.
        connection.commit()
        cursor.close()
        cursor2.close()

    def calculate_distances_inter_expected(self):
        """Calculate the expected spot distances.

        This is based on the observed inter specific distances and the
        distances are saved to the "spot_distances_expected" table in the local
        database.

        Design Part: 1.69
        """
        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the spot_distances_expected table before we use it again.
        cursor.execute("DELETE FROM spot_distances_expected")
        connection.commit()

        # Get the number of positive spots for each plate. This will serve
        # as a template for the random spots.
        cursor.execute( "SELECT pla_id, n_spots_a, n_spots_b "
                        "FROM plate_spot_totals"
                        )

        for plate_id, n_spots_a, n_spots_b in cursor:
            # Use that number of spots to generate the same number of random
            # positive spots for both records.
            random_spots1 = setlyze.std.get_random_for_plate(n_spots_a)
            random_spots2 = setlyze.std.get_random_for_plate(n_spots_b)

            # Get all possible combinations between the two sets of random
            # spots.
            combos = itertools.product(random_spots1,random_spots2)

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

        Based on the results of the tests we can decide which hypothesis
        we can assume to be true.

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
        positive spots ratios.

        Because we match plates that contain both species selection, we
        can calculate a ratio of positive spots for each plate. So a
        plate with 3 positive spots for species A and 2 positive spots
        for species B, would result in a ratio of 3:2 (or 2:3). We consider
        a ratio of A:B to be the same as ratio B:A.

        We've grouped all possible ratio's in 5 ratios groups. See
        :ref:`record grouping <record-grouping>` in the user manual for
        more details. Both tests are performed on each ratios group.

        Both tests are also performed on ratios groups 1-5 taken together.

        Design Part: 1.24
        """

        # Create an iterator returning the ratio groups.
        ratio_groups = self.generate_spot_ratio_groups()

        for n_group, ratio_group in enumerate(ratio_groups, start=1):
            # Ratios group 6 is actually all 5 groups taken together.
            # So change the group number to -5, meaning all groups up
            # to 5.
            if n_group == 6:
                n_group = -5

            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_distances_matching_ratios(
                'spot_distances_observed', ratio_group)
            expected = self.db.get_distances_matching_ratios(
                'spot_distances_expected', ratio_group)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Get the number of matching plates.
            n_plates = self.db.matching_plates_total

            # Get the lengths.
            count_observed = len(observed)
            count_expected = len(expected)

            # The number of observed and expected spot distances must always
            # be the same.
            assert count_observed == count_expected, \
                "Number of observed and expected values are not equal."

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this ratio group if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            test_result = wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Save the significance result.
            if not self.statistics['wilcoxon_ratios_repeats']['attr']:
                self.statistics['wilcoxon_ratios_repeats']['attr'] = {
                    'method': test_result['method'],
                    'alternative': test_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'repeats': self.n_repeats,
                    'groups': 'ratios',
                }

            if not self.statistics['wilcoxon_ratios']['attr']:
                self.statistics['wilcoxon_ratios']['attr'] = {
                    'method': test_result['method'],
                    'alternative': test_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'groups': 'ratios',
                }

            self.statistics['wilcoxon_ratios']['results'][n_group] = {
                'n_plates': n_plates,
                'n_values': count_observed,
                'p_value': test_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
            }

            # Get the probability for each spot distance. Required for
            # the Chi-squared test.
            spot_dist_to_prob = setlyze.config.cfg.get('spot-dist-to-prob-inter')

            # Get the frequencies for the observed distances. These
            # are required for the Chi-squared test.
            observed_freq = setlyze.std.distance_frequency(observed, 'inter')

            # Also perform Chi-squared test.
            test_result = chisq_test(observed_freq.values(),
                p = spot_dist_to_prob.values())

            # If we find an expected frequency that is less than 5, do not save
            # the result.
            for f in test_result['expected']:
                if f < 5:
                    continue

            # Save the significance result.
            if not self.statistics['chi_squared_ratios']['attr']:
                self.statistics['chi_squared_ratios']['attr'] = {
                    'method': test_result['method'],
                    'groups': 'ratios',
                }

            self.statistics['chi_squared_ratios']['results'][n_group] = {
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
        :meth:`calculate_distances_inter_expected` is called to re-calculate
        the expected values (which are random).

        Design Part: 1.105
        """
        for i in range(n):
            if self.stopped():
                return

            # Update the progess bar.
            self.exec_task('progress.increase')

            # The expected spot distances are random. So the expected values
            # differ a little on each repeat.
            self.calculate_distances_inter_expected()

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

        Design Part: 1.104
        """

        # Create an iterator returning the ratio groups.
        ratio_groups = self.generate_spot_ratio_groups()

        for n_group, ratio_group in enumerate(ratio_groups, start=1):
            # Ratios group 6 is actually all 5 groups taken together.
            # So change the group number to -5, meaning all groups up
            # to 5.
            if n_group == 6:
                n_group = -5

            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_distances_matching_ratios(
                'spot_distances_observed', ratio_group)
            expected = self.db.get_distances_matching_ratios(
                'spot_distances_expected', ratio_group)

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
            # significance test. So skip this ratio group if it's less.
            if count_observed < 2:
                continue

            # Check if this ratios group is present in the statistics variable.
            # If not, create it.
            if n_group not in self.statistics['wilcoxon_ratios_repeats']['results']:
                self.statistics['wilcoxon_ratios_repeats']['results'][n_group] = {
                    'n_plates': self.db.matching_plates_total,
                    'n_values': count_observed,
                    'n_significant': 0,
                    'n_attraction': 0,
                    'n_repulsion': 0
                }

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            test_result = wilcox_test(observed, expected,
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
                self.statistics['wilcoxon_ratios_repeats']['results'][n_group]['n_significant'] += 1

                # If significant, also check if there is preference or
                # rejection for this plate area.
                if mean_observed < mean_expected:
                    # Increase attracion counter with one.
                    self.statistics['wilcoxon_ratios_repeats']['results'][n_group]['n_attraction'] += 1
                else:
                    # Increase repulsion counter with one.
                    self.statistics['wilcoxon_ratios_repeats']['results'][n_group]['n_repulsion'] += 1

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.15
        """
        self.result.set_analysis("Attraction between Species")
        self.result.set_option('Alpha level', self.alpha_level)
        self.result.set_option('Repeats', self.n_repeats)
        self.result.set_option('Total plates', self.affected)
        self.result.set_location_selections(self.locations_selections)
        self.result.set_species_selections(self.species_selections)
        self.result.set_statistics('wilcoxon_ratios', self.statistics['wilcoxon_ratios'])
        self.result.set_statistics('wilcoxon_ratios_repeats', self.statistics['wilcoxon_ratios_repeats'])
        self.result.set_statistics('chi_squared_ratios', self.statistics['chi_squared_ratios'])
