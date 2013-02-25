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

"""This module performs analysis 1 "Spot preference". This analysis
can be broken down in the following steps:

1. Show a list of all localities and let the user perform a localities
   selection.
2. Show a list of all species that match the locations selection and
   let the user perform a species selection.
3. Show the Define Plate Areas dialog and let the user define the plate
   areas.
4. Calculate the observed species frequencies for the plate areas.
5. Check if all plate area frequencies are zero. If so, abort.
6. Calculate the expected species frequencies for the plate areas.
7. Calculate the significance in difference between the observed and
   expected area totals. The Chi-squared test is used for this.
8. Generate the analysis report.
9. Show the analysis report to the user.

"""

import logging
import time
import collections
import multiprocessing

import gobject
import pygtk
pygtk.require('2.0')
import gtk

from setlyze.analysis.common import calculatestar,ProcessTaskExec,PrepareAnalysis,AnalysisWorker
import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.std
import setlyze.report

__author__ = ("Jonathan den Boer, Serrano Pereira, Adam van Adrichem, "
        "Fedde Schaeffer")
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

# The number of progress steps for this analysis.
PROGRESS_STEPS = 7

class Begin(PrepareAnalysis):
    """Make the preparations for analysis 1:

    1. Show a list of all localities and let the user perform a localities
       selection.
    2. Show a list of all species that match the locations selection and
       let the user perform a species selection.
    3. Show the Define Plate Areas dialog and let the user define the plate
       areas.
    4. Start the analysis.
    5. Show the analysis report to the user.

    Design Part: 1.3.1
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Beginning analysis Spot Preference")

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
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_select_locations),
            # The user pressed the X button of a locations/species selection window.
            'selection-dialog-closed': setlyze.std.sender.connect('selection-dialog-closed', self.on_analysis_closed),
            # The user pressed the X button of a define spots window.
            'define-areas-dialog-closed': setlyze.std.sender.connect('define-areas-dialog-closed', self.on_analysis_closed),
            # User pressed the Back button in the locations selection window.
            'locations-dialog-back': setlyze.std.sender.connect('locations-dialog-back', self.on_analysis_closed),
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
            # Cancel button pressed.
            'analysis-canceled': setlyze.std.sender.connect('analysis-canceled', self.on_cancel_button),
            # Analysis aborted.
            'analysis-aborted': setlyze.std.sender.connect('analysis-aborted', self.on_analysis_aborted),
            # Progress dialog closed
            'progress-dialog-closed': setlyze.std.sender.connect('progress-dialog-closed', self.on_cancel_button),
            # The process pool has finished.
            'pool-finished': setlyze.std.sender.connect('pool-finished', self.on_display_results),
        }

    def on_select_locations(self, sender=None, data=None):
        """Display the window for selecting the locations."""
        select = setlyze.gui.SelectLocations(slot=0)
        select.set_title(setlyze.locale.text('analysis1'))
        select.set_description(setlyze.locale.text('select-locations') + "\n\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

    def on_select_species(self, sender=None, data=None):
        """Display the window for selecting the species."""
        select = setlyze.gui.SelectSpecies(width=600, slot=0)
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
        locations = setlyze.config.cfg.get('locations-selection', slot=0)
        species = setlyze.config.cfg.get('species-selection', slot=0)
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        self.pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps(PROGRESS_STEPS + self.n_repeats)

        # Create a progress task executor.
        exe = ProcessTaskExec()
        exe.set_pdialog_handler(self.pdialog_handler)
        exe.start()

        # Create a process pool with a single worker.
        self.pool = multiprocessing.Pool(1)

        # Create a list of jobs.
        jobs = [(Analysis, (locations, species, areas_definition, exe.queue))]

        # Add the job to the pool.
        self.pool.map_async(calculatestar, jobs, callback=self.on_pool_finished)

class BeginBatch(Begin):
    """Make the preparations for batch analysis:

    1. Show a list of all localities and let the user perform a localities
       selection.
    2. Show a list of all species that match the locations selection and
       let the user perform a species selection.
    3. Run the analysis for all species in batch.
    4. Show the analysis report to the user.
    """

    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")

        self.report_prefix = "spot_preference_"

        # Don't print abort messages during batch mode.
        setlyze.std.sender.disconnect(self.signal_handlers['analysis-aborted'])
        self.signal_handlers['analysis-aborted'] = None

    def on_start_analysis(self, sender=None, data=None):
        """Run analysis Spot Preference in batch mode.

        Repeat the analysis for each species separately.
        """
        locations = setlyze.config.cfg.get('locations-selection', slot=0)
        species = setlyze.config.cfg.get('species-selection', slot=0)
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')
        self.start_time = time.time()

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        self.pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)

        # Set the total number of times we decide to update the progress dialog.
        self.pdialog_handler.set_total_steps((PROGRESS_STEPS + self.n_repeats) *
            len(species))

        # Create a progress task executor.
        exe = ProcessTaskExec()
        exe.set_pdialog_handler(self.pdialog_handler)
        exe.start()

        # Create a process pool with workers.
        cp = setlyze.config.cfg.get('concurrent-processes')
        self.pool = multiprocessing.Pool(cp)

        # Create a list of jobs.
        logging.info("Adding %d jobs to the queue" % len(species))
        jobs = ((Analysis, (locations, sp, areas_definition, exe.queue)) for sp in species)

        # Add the jobs to the pool.
        self.pool.map_async(calculatestar, jobs, callback=self.on_pool_finished)

    def summarize_results(self, results):
        """Join results from multiple analyses to a single report.

        Creates a dictionary in the following format ::

            {
                'attr': {
                    'columns': ('Species', 'n (plates)', 'A', 'B', 'C', 'D', 'A+B', 'C+D', 'A+B+C', 'B+C+D', 'Chi sq')
                },
                'results': [
                    ['Obelia dichotoma', 166, 'p', 'n', 'r', 'r', 'p', 'r', 'n', 'r', 's'],
                    ['Obelia geniculata', 88, 'n', 'n', 'r', 'n', 'n', 'r', 'n', 'r', 's'],
                    ...
                ]
            }
        """
        report = {
            'attr': {'columns': ('Species','n (plates)','A','B','C','D','A+B','C+D','A+B+C','B+C+D','Chi sq')},
            'results': []
        }
        for result in results:
            chi_squared = None
            wilcoxon = None
            species_selection = [s for s in result.species_selections[0].values()]
            species = species_selection[0]['name_latin']
            if 'wilcoxon_areas_repeats' in result.statistics:
                wilcoxon = result.statistics['wilcoxon_areas_repeats'][0]
            if 'chi_squared_areas' in result.statistics:
                chi_squared = result.statistics['chi_squared_areas'][0]

            # Skip this result if there was not enough data for one of the
            # analyses.
            if not wilcoxon or not chi_squared:
                continue

            # Figure out for which plate areas the result was significant. A
            # result is considered significant if 95% of the tests for a plate
            # area were significant.
            areas = ['A','B','C','D','A+B','C+D','A+B+C','B+C+D']
            row = []
            for plate_area in areas:
                stats = wilcoxon['results'].get(plate_area, None)
                if stats:
                    significant = float(stats['n_significant']) / wilcoxon['attr']['repeats'] >= 1-self.alpha_level
                    if significant:
                        # Significant: preference or rejection.
                        if stats['n_preference'] > stats['n_rejection']:
                            row.append('p')
                        else:
                            row.append('r')
                    else:
                        # Not significant.
                        row.append('n')
                else:
                    # No data.
                    row.append(None)

            # At the boolean for the Chi squared test. This is either
            # significant or not.
            significant = chi_squared['results']['p_value'] < self.alpha_level
            if significant:
                row.append('s')
            else:
                row.append('n')

            # Only add the row to the report if one item in the row was
            # significant.
            for c in row:
                if c and c in 'prs':
                    r = [species, result.get_option('Total plates')]
                    r.extend(row)
                    report['results'].append(r)
                    break

        return report

    def on_display_results(self, sender, results=[]):
        """Display the results."""
        # Create a summary from all results.
        summary = self.summarize_results(results)

        # Create a report object from the dictionary.
        report = setlyze.report.Report()
        report.set_statistics('plate_areas_summary', summary)

        # Set analysis options.
        for name, value in results[0].options.iteritems():
            report.set_option(name, value)

        # Set elapsed time.
        if self.elapsed_time:
            report.set_option('Running time', setlyze.std.seconds_to_hms(self.elapsed_time))

        # Display the report.
        w = setlyze.gui.Report(report, "Results: Batch summary for Sport Preference")
        w.set_size_request(700, 500)

class Analysis(AnalysisWorker):
    """Perform the calculations for analysis 1.

    1. Calculate the observed species frequencies for the plate areas.
    2. Check if all plate area frequencies are zero. If so, abort.
    3. Calculate the expected species frequencies for the plate areas.
    4. Calculate the significance in difference between the observed and
       expected area totals. The Chi-squared test is used for this.
    5. Generate the analysis report.

    Design Part: 1.3.2
    """

    def __init__(self, locations_selection, species_selection, areas_definition, execute_queue=None):
        super(Analysis, self).__init__(execute_queue)

        self.locations_selection = locations_selection
        self.species_selection = species_selection
        self.areas_definition = areas_definition
        self.chisq_observed = None # Design Part: 2.25
        self.chisq_expected = None # Design Part: 2.26
        self.statistics = {
            'chi_squared_areas': {'attr': None, 'results': {}},
            'wilcoxon_areas': {'attr': None, 'results': collections.OrderedDict()},
            'wilcoxon_areas_repeats': {'attr': None, 'results': collections.OrderedDict()}
        }

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis1'))

    def set_areas_definition(self, definition):
        """Set the plate areas definition.

        The plate areas definition `definition` is a definition as saved by
        :class:`setlyze.gui.DefinePlateAreas`.
        """
        self.areas_definition = definition

    def run(self):
        """Call the necessary methods for the analysis in the right order
        and do some data checks:

            * :meth:`~setlyze.database.AccessLocalDB.get_record_ids` or
              :meth:`~setlyze.database.AccessRemoteDB.get_record_ids`
            * :meth:`~setlyze.database.AccessLocalDB.set_species_spots` or
              :meth:`~setlyze.database.AccessRemoteDB.set_species_spots`
            * :meth:`~setlyze.database.AccessDBGeneric.make_plates_unique`
            * :meth:`set_plate_area_totals_observed`
            * :meth:`get_defined_areas_totals_observed`
            * Check if all plate area totals are zero. If so, abort.
            * :meth:`repeat_test`
            * :meth:`calculate_significance_wilcoxon`
            * :meth:`calculate_significance_chisq`
            * :meth:`generate_report`

        Design Part: 1.58
        """
        try:
            if not self.stopped():
                # Make an object that facilitates access to the database.
                self.db = setlyze.database.get_database_accessor()

                assert isinstance(self.db, setlyze.database.AccessLocalDB), \
                    "Expected an instance of AccessLocalDB. Got %s" % self.db.__class__.__name__

                # Create temporary tables.
                self.db.create_table_species_spots_1()
                self.db.create_table_plate_area_totals_observed()
                self.db.create_table_plate_area_totals_expected()
                self.db.conn.commit()

                # Get the record IDs that match the localities+species selection.
                rec_ids = self.db.get_record_ids(self.locations_selection, self.species_selection)
                # Create log message.
                logging.info("\tTotal records that match the species+locations selection: %d" % len(rec_ids))

                # Create log message and update progress dialog.
                logging.info("\tCreating table with species spots...")
                self.exec_task('progress.increase', "Creating table with species spots...")
                # Make a spots table for the selected species.
                self.db.set_species_spots(rec_ids, slot=0)

                # Create log message and update progress dialog.
                logging.info("\tMaking plate IDs in species spots table unique...")
                self.exec_task('progress.increase', "Making plate IDs in species spots table unique...")
                # Make the plate IDs unique.
                self.n_plates_unique = self.db.make_plates_unique(slot=0)
                # Create log message.
                logging.info("\t  %d records remaining." % (self.n_plates_unique))

            if not self.stopped():
                # Create log message and update progress dialog.
                logging.info("\tCalculating the observed plate area totals for each plate...")
                self.exec_task('progress.increase', "Calculating the observed plate area totals for each plate...")
                # Calculate the expected totals.
                self.set_plate_area_totals_observed()

                # Calculate the observed species encounters for the user defined plate
                # areas.
                self.chisq_observed = self.get_defined_areas_totals_observed()

                # Make sure that spot area totals are not all zero. If so, abort
                # the analysis, because we can't devide by zero (unless you're
                # Chuck Norris of course).
                areas_total = 0
                for area_total in self.chisq_observed.itervalues():
                    areas_total += area_total
                if areas_total == 0:
                    logging.info("The species was not found on any plates, aborting.")
                    self.exec_task('emit', 'analysis-aborted', setlyze.locale.text('empty-plate-areas'))

                    # Exit gracefully.
                    self.on_exit()
                    return None

            if not self.stopped():
                # Create log message and update progress dialog.
                logging.info("\tPerforming Wilcoxon tests with %d repeats..." % self.n_repeats)
                self.exec_task('progress.increase', "Performing Wilcoxon tests with %s repeats..." % self.n_repeats)
                # Perform the repeats for the statistical tests. This will repeatedly
                # calculate the expected totals, so we'll use the expected values
                # of the last repeat for the non-repeated tests.
                self.repeat_test(self.n_repeats)

            if not self.stopped():
                # Create log message.
                logging.info("\tPerforming statistical tests...")
                # Update progress dialog.
                self.exec_task('progress.increase', "Performing statistical tests...")
                # Performing the statistical tests.
                self.calculate_significance_wilcoxon()
                self.calculate_significance_chisq()

            # If the cancel button is pressed don't finish this function.
            if self.stopped():
                logging.info("Analysis aborted by user")

                # Exit gracefully.
                self.on_exit()
                return None

            # Update progress dialog.
            self.exec_task('progress.increase', "Generating the analysis report...")
            # Generate the report.
            self.generate_report()

            # Update progress dialog.
            self.exec_task('progress.increase', "")

            # Emit the signal that the analysis has finished.
            # Note that the signal will be sent from a separate thread,
            # so we must use gobject.idle_add.
            gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')
            logging.info("%s was completed!" % setlyze.locale.text('analysis1'))
        except Exception, e:
            self.exception = e
            return None

        # Exit gracefully.
        self.on_exit()

        return self.result

    def set_plate_area_totals_observed(self):
        """Fills :ref:`design-part-data-2.41`, the "plate_area_totals_observed"
        table in the local SQLite database.

        Design Part: 1.62
        """

        # From plate area to spot numbers.
        area2spots = {'A': (1,5,21,25),
            'B': (2,3,4,6,10,11,15,16,20,22,23,24),
            'C': (7,8,9,12,14,17,18,19),
            'D': (13,),
            }

        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the plate_area_totals table.
        cursor.execute("DELETE FROM plate_area_totals_observed")
        connection.commit()

        # Get all records from the table.
        cursor.execute( "SELECT rec_pla_id,"
                        "rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM species_spots_1")

        # Fill the totals table.
        for record in cursor:
            # From plate area to total spots for a record.
            area_totals = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

            # Check for each spot in the record row if the species is
            # present. 'precence' == 1 if the species is present on
            # that spot.
            for spot, precence in enumerate(record[1:], start=1):
                # In case the 'precence' boolean is False, just continue
                # with the next spot.
                if not precence:
                    continue

                # If we pass here, the species is present on this spot.
                # Walk through each area in the area2spots dictionary.
                for area, area_spots in area2spots.iteritems():
                    # Check if the current spot ID belongs to that area.
                    if spot in area_spots:
                        # If so, add 1 to the species total of that area.
                        area_totals[area] += 1
                        # Once a match was found, that same spot ID can't
                        # belong to another area. So continue with the next
                        # spot for this record.
                        break

            # Save the plate area totals for this record to the database.
            cursor2.execute("INSERT INTO plate_area_totals_observed VALUES (?,?,?,?,?)",
                            (record[0],
                            area_totals['A'],
                            area_totals['B'],
                            area_totals['C'],
                            area_totals['D'])
                            )

        # Commit the database transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()

    def set_plate_area_totals_expected(self):
        """Fills :ref:`design-part-data-2.42`, the "plate_area_totals_expected"
        table in the local SQLite database.

        Design Part: 1.63
        """

        # From plate area to spot numbers.
        area2spots = {'A': (1,5,21,25),
            'B': (2,3,4,6,10,11,15,16,20,22,23,24),
            'C': (7,8,9,12,14,17,18,19),
            'D': (13,),
            }

        # Make a connection with the local database.
        connection = self.db.conn
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the plate_area_totals_expected table before we use it
        # again.
        cursor.execute("DELETE FROM plate_area_totals_expected")
        connection.commit()

        # Get the number of positive spots for each plate. This
        # will serve as a template for the random spots.
        cursor.execute( "SELECT pla_id, area_a, area_b, area_c, area_d "
                        "FROM plate_area_totals_observed"
                        )

        for pla_id, area_a, area_b, area_c, area_d in cursor:
            # Calculate the number of positive spots by summing the spot totals
            # of all plate areas for the current plate.
            n_spots = area_a + area_b + area_c + area_d

            # Use that number of spots to generate the same number of
            # random spots.
            random_spots = setlyze.std.get_random_for_plate(n_spots)

            # From plate area to total spots for a record.
            area_totals = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

            # Sort the random positive spots in the correct areas in
            # 'area_totals'.
            for spot in random_spots:
                # Walk through each area in the area2spots dictionary.
                for area, area_spots in area2spots.iteritems():
                    # Check if the current spot ID belongs to that area.
                    if spot in area_spots:
                        # If so, add 1 to the species total of that area.
                        area_totals[area] += 1
                        # Once a match was found, that same spot ID can't
                        # belong to another area. So continue with the next
                        # spot for this record.
                        break

            # Save the plate area totals for this record to the database.
            cursor2.execute("INSERT INTO plate_area_totals_expected VALUES (?,?,?,?,?)",
                            (pla_id,
                            area_totals['A'],
                            area_totals['B'],
                            area_totals['C'],
                            area_totals['D'])
                            )

        # Commit the database transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()

    def calculate_significance_wilcoxon(self):
        """Perform statistical tests to check if the differences between
        the means of the two sets of positive spots numbers are statistically
        significant.

        The unpaired Wilcoxon rank sum test is used. We use unpaired
        because the two sets of positive spots numbers are unrelated
        (:ref:`Dalgaard <ref-dalgaard>`).

        The test is performed on different data groups. Each data group
        contains the positive spots numbers for a specific plate area or
        a combination of plate areas. The user defined plate areas are not
        used for this test, so the default plate areas A, B, C and D are used.
        The groups are defined as follows:

        1. Plate area A
        2. Plate area B
        3. Plate area C
        4. Plate area D
        5. Plate area A+B
        6. Plate area C+D
        7. Plate area A+B+C
        8. Plate area B+C+D

        Based on the results of a test we can decide which hypothesis we can
        assume to be true.

        Null hypothesis
            The species in question does not have a preference or rejection
            for the plate area in question.

        Alternative hypothesis
            The species in question has a preference for the plate area in
            question (mean observed > mean expected) or has a rejection for
            the plate area in question (mean observed < mean expected).

        The decision is based on the p-value calculated by the test:

        P >= alpha level
            Assume that the null hypothesis is true.

        P < alpha level
            Assume that the alternative hypothesis is true.

        Combining the results of all plate area groups listed above should
        allow you to draw a conclusion about the species' plate area preference.
        For example, should a species have a strong preference for the corners
        of a SETL-plate, then you would expect to find low p-values for group
        1 (preference). But also low P-values for groups 3, 4, 6 and 8
        because of rejection. If group 2 would not be significant, then group
        7 wouldn't be either, because areas A and C neutralize each other.

        Design Part: 1.98
        """

        # The area groups to perfom the test on.
        area_groups = [('A'),('B'),('C'),('D'),('A','B'),('C','D'),
            ('A','B','C'),('B','C','D')]

        for area_group in area_groups:
            # Get area totals per area group per plate.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)
            expected = self.db.get_area_totals(
                'plate_area_totals_expected', area_group)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Calculate the number of species encounters for the current
            # area group.
            species_encouters_observed = sum(observed)
            species_encouters_expected = sum(expected)

            # Get the lengths.
            count_observed = len(observed)
            count_expected = len(expected)

            # The number of observed and expected plate area totals must
            # always be the same.
            assert count_observed == count_expected, \
                "Number of observed and expected values are not equal."

            # A minimum of two positive spots totals are required for the
            # significance test. So skip this plate area if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Create a human readable string with the areas in the area group.
            area_group_str = "+".join(area_group)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Set the attributes for the tests.
            if not self.statistics['wilcoxon_areas_repeats']['attr']:
                self.statistics['wilcoxon_areas_repeats']['attr'] = {
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'groups': "areas",
                    'repeats': self.n_repeats,
                }

            if not self.statistics['wilcoxon_areas']['attr']:
                self.statistics['wilcoxon_areas']['attr'] = {
                    'method': sig_result['method'],
                    'alternative': sig_result['alternative'],
                    'conf_level': 1 - self.alpha_level,
                    'paired': False,
                    'groups': "areas",
                }

            # Save the results for each test.
            self.statistics['wilcoxon_areas']['results'][area_group_str] = {
                'n_values': count_observed,
                'n_sp_observed': species_encouters_observed,
                'n_sp_expected': species_encouters_expected,
                'p_value': sig_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
            }

    def calculate_significance_chisq(self):
        """Perform statistical tests to check if the differences between
        the means of the two sets of positive spots numbers are statistically
        significant.

        The Chi-squared test for given probabilities (:ref:`Millar <ref-millar>`,
        :ref:`Dalgaard <ref-dalgaard>`) is used to calculate this significance.
        The probabilities for the user defined plate areas are first calculated.
        From these probabilities the expected positive spots numbers are
        calculated by the Chi-squared test. The number of observed positive
        spots are then compared to the expected number of positive spots. This
        is done for all user defined plate areas.

        Based on the results of a test we can decide which hypothesis we can
        assume to be true.

        Null hypothesis
            The species in question does not have a preference or rejection
            for the plate area in question.

        Alternative hypothesis
            The species in question has a preference for the plate area in
            question (n observed > n expected) or has a rejection for
            the plate area in question (n observed < n expected).

        The decision is based on the p-value calculated by the test:

        P >= alpha level
            Assume that the null hypothesis is true.

        P < alpha level
            Assume that the alternative hypothesis is true.

        In contrast to the results of the Wilcoxon test, the results for this
        test don't show whether the species has a preference or a rejection
        for a specific user defined plate area. This is because the design of
        the Chi-squared test, which looks at the data of all plate areas
        together. So it just tells you if the data shows significant
        differences.

        Design Part: 1.99
        """

        # Only perform the Chi2 test if there are at least 5 values.
        if sum(self.chisq_observed.values()) < 5:
            return

        # Get the probabilities for the user defined plate areas.
        probabilities = self.get_area_probabilities()

        # Also perform Chi-squared test.
        sig_result = setlyze.std.chisq_test(self.chisq_observed.values(),
            p = probabilities.values())

        # Save the significance result.
        self.statistics['chi_squared_areas']['attr'] = {
            'method': sig_result['method'],
            }
        self.statistics['chi_squared_areas']['results'] = {
            'chi_squared': sig_result['statistic']['X-squared'],
            'p_value': sig_result['p.value'],
            'df': sig_result['parameter']['df'],
            }

        # Save the expected values.
        self.chisq_expected = {}
        for i, area in enumerate(self.chisq_observed):
            self.chisq_expected[area] = sig_result['expected'][i]

    def calculate_significance_wilcoxon_repeats(self):
        """This method does the same as :meth:`calculate_significance_wilcoxon`,
        but instead is designed to be called repeatedly, saving the results
        of the repeated test. This method doesn't save the detailed
        results of the Wilcoxon test, but just saves whether the p-value
        was significant, and whether it was preference or rejection for the
        plate area in question.

        Repeation of the Wilcoxon test is necessary, as the expected values
        are calculated randomly. The test needs to be repeated many times
        if you want to draw a solid conclusion from the results.

        The number of times this method is called depends on the configuration
        setting "test-repeats".

        Design Part: 1.100
        """

        # The plate area groups to perfom the test on.
        area_groups = [('A'),('B'),('C'),('D'),('A','B'),('C','D'),
            ('A','B','C'),('B','C','D')]

        # Perform the test on each area group.
        for area_group in area_groups:
            # Create a human readable string with the areas in the area group.
            area_group_str = "+".join(area_group)

            # Get area totals per area group per plate.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)
            expected = self.db.get_area_totals(
                'plate_area_totals_expected', area_group)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # A minimum of two positive spots totals are required for the
            # significance test. So skip this spots number if it's less.
            count_observed = len(observed)
            count_expected = len(expected)

            # The number of observed and expected plate area totals must
            # always be the same.
            assert count_observed == count_expected, \
                "Number of observed and expected values are not equal."

            # A minimum of two positive spots totals are required for the
            # significance test. So skip this plate area if it's less.
            if count_observed < 2:
                continue

            # Check if this area group is present in the statistics variable.
            # If not, create it.
            if area_group_str not in self.statistics['wilcoxon_areas_repeats']['results']:
                self.statistics['wilcoxon_areas_repeats']['results'][area_group_str] = {
                    'n_values': count_observed,
                    'n_sp_observed': sum(observed),
                    'n_significant': 0,
                    'n_preference': 0,
                    'n_rejection': 0
                }

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - self.alpha_level,
                conf_int = False)

            # Save basic results for this repeated test.
            # Check if the result was significant (P-value < alpha-level).
            p_value = float(sig_result['p.value'])
            if p_value < self.alpha_level and p_value != 'nan':
                # If so, increase significant counter with one.
                self.statistics['wilcoxon_areas_repeats']['results'][area_group_str]['n_significant'] += 1

                # If significant, also check if there is preference or
                # rejection for this plate area.
                if mean_observed > mean_expected:
                    # Increase preference counter with one.
                    self.statistics['wilcoxon_areas_repeats']['results'][area_group_str]['n_preference'] += 1
                else:
                    # Increase rejection counter with one.
                    self.statistics['wilcoxon_areas_repeats']['results'][area_group_str]['n_rejection'] += 1

    def repeat_test(self, number):
        """Repeats the siginificance test `number` times. The significance
        test is performed by :meth:`calculate_significance_wilcoxon_repeats`.

        Each time before :meth:`calculate_significance_wilcoxon_repeats` is
        called, :meth:`set_plate_area_totals_expected` is called to
        re-calculate the expected values (which are random).

        Design Part: 1.65
        """
        for i in range(number):
            # Test if the cancel button is pressed.
            if self.stopped():
                return

            # Update the progess bar.
            self.exec_task('progress.increase')

            # The expected area totals are random. So the expected values
            # differ a little on each repeat.
            self.set_plate_area_totals_expected()

            # And then we calculate the siginificance for each repeat.
            self.calculate_significance_wilcoxon_repeats()

    def get_defined_areas_totals_observed(self):
        """Return the number of positive spots for each user defined plate
        area. The positive spots for the areas of all plates matching the
        species selection are summed up.

        Returns a dictionary where the keys are the unique names of the plate
        areas, and the values are the number of positive spots.

        Design Part: 1.64
        """

        # Dictionary which will contain the species total for each area.
        areas_totals_observed = {'area1': 0,
            'area2': 0,
            'area3': 0,
            'area4': 0,
            }

        for area_name, area_group in self.areas_definition.iteritems():
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)

            # Sum all totals in the correct area name.
            for total in observed:
                areas_totals_observed[area_name] += total

        # Remove unused areas from the variable.
        delete = []
        for area in areas_totals_observed:
            if area not in self.areas_definition:
                delete.append(area)
        for area in delete:
            del areas_totals_observed[area]

        return areas_totals_observed

    def get_area_probabilities(self):
        """Return the probabilities for the defined plate areas.

        It is assumed that each of the 25 plate surfaces on a SETL-plate
        have a probability of 1/25.

        Returns a dictionary; the keys are the unique names of the user
        defined plate areas, and the values are the probabilities. The
        probabilities are floats between 0 and 1.

        Design Part: 1.101
        """

        # The spot names, and how many times they occur on a plate.
        probabilities = {'A': 4/25.0,
            'B': 12/25.0,
            'C': 8/25.0,
            'D': 1/25.0,
            }

        # Calculate what each spot area should be multiplied with, as
        # the spot areas can be combinations of spots.
        area_probabilities = { 'area1': 0, 'area2': 0, 'area3': 0, 'area4': 0 }
        for area, spot_names in self.areas_definition.iteritems():
            for spot_name in spot_names:
                area_probabilities[area] += probabilities[spot_name]

        # Remove unused areas.
        delete = []
        for area in area_probabilities:
            if area not in self.areas_definition:
                delete.append(area)

        for area in delete:
            del area_probabilities[area]

        return area_probabilities

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.13
        """
        self.result.set_analysis("Spot Preference")
        self.result.set_option('Alpha level', self.alpha_level)
        self.result.set_option('Repeats', self.n_repeats)
        self.result.set_option('Total plates', self.n_plates_unique)
        self.result.set_location_selections([self.locations_selection])
        self.result.set_species_selections([self.species_selection])
        self.result.set_plate_areas_definition(self.areas_definition)
        self.result.set_area_totals_observed(self.chisq_observed)
        self.result.set_area_totals_expected(self.chisq_expected)
        self.result.set_statistics('chi_squared_areas', self.statistics['chi_squared_areas'])
        self.result.set_statistics('wilcoxon_areas', self.statistics['wilcoxon_areas'])
        self.result.set_statistics('wilcoxon_areas_repeats', self.statistics['wilcoxon_areas_repeats'])
