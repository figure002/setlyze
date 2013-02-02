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

"""This module performs analysis 3 "Attraction between species". This analysis
can be broken down in the following steps:

1. Show a list of all localities and let the user perform a localities
   selection.

2. Show a list of all species that match the locations selection and
   let the user perform the first species selection.

3. Show a list of all species that match the locations selection and
   let the user perform the second species selection.

4. Get all SETL records that match the localities + first species
   selection and save these to table "species_spots_1" in the local
   database.

5. Merge records with the same plate ID in table "species_spots_1" to
   make the plate IDs unique.

6. Get all SETL records that match the localities + second species
   selection and save these to table "species_spots_2" in the local
   database.

7. Merge records with the same plate ID in table "species_spots_2" to
   make the plate IDs unique.

8. Calculate the inter-specific spot distances from the records in both
   species spots tables and save the distances to table
   "spot_distances_observed" in the local database.

9. Calculate expected inter-specific spot distances by generating
   random spots and save the distances to table
   "spot_distances_expected" in the local database.

10. Calculate the significance in difference between the observed and
    expected spot distances. Two tests of significance are performed:
    the Wilcoxon rank-sum test and the Chi-squared test.

11. Generate the analysis report.

12. Show the analysis report to the user.

"""

import logging
import itertools
import time
from sqlite3 import dbapi2 as sqlite

import gobject

import setlyze.analysis.common
import setlyze.locale
import setlyze.config
import setlyze.gui
import setlyze.locale
import setlyze.std
import setlyze.report

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"

# The number of progress steps for this analysis.
PROGRESS_STEPS = 12

class Begin(setlyze.analysis.common.PrepareAnalysis):
    """Make the preparations for analysis 3:

    1. Show a list of all localities and let the user perform a localities
       selection.

    2. Show a list of all species that match the locations selection and
       let the user perform the first species selection.

    3. Show a list of all species that match the locations selection and
       let the user perform the second species selection.

    4. Start the analysis.

    5. Show the analysis report to the user.

    Design Part: 1.5.1
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Beginning Analysis ”Attraction between species”")

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)

        # Reset the save slot.
        setlyze.std.sender.set_property('save-slot', 0)

        # Emit the signal that an analysis has started.
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
            'species-dialog-back': setlyze.std.sender.connect('species-dialog-back', self.on_species_back),

            # The user selected locations have been saved.
            'locations-selection-saved': setlyze.std.sender.connect('locations-selection-saved', self.on_locations_saved),

            # The user selected species have been saved.
            'species-selection-saved': setlyze.std.sender.connect('species-selection-saved', self.on_species_saved),

            # Display the report after the analysis has finished.
            'analysis-finished': setlyze.std.sender.connect('analysis-finished', self.on_display_report),

            # The report window was closed.
            'report-dialog-closed': setlyze.std.sender.connect('report-dialog-closed', self.on_analysis_closed),

            # Cancel button
            'analysis-canceled': setlyze.std.sender.connect('analysis-canceled', self.on_cancel_button),

            # Progress dialog closed
            'progress-dialog-closed': setlyze.std.sender.connect('progress-dialog-closed', self.on_analysis_closed),
        }

    def on_locations_saved(self, sender, save_slot=0, data=None):
        # Make sure the second slot for the locations selection is the
        # same as the first slot, as the same selections should be used
        # for both species selections.
        selection = setlyze.config.cfg.get('locations-selection', slot=0)
        setlyze.config.cfg.set('locations-selection', selection, slot=1)

        # Show species selection dialog.
        self.on_select_species()

    def on_species_saved(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            sender.set_property('save-slot', 1)
            self.on_select_species()
            return
        elif save_slot == 1:
            self.on_start_analysis()
            return

    def on_species_back(self, sender, save_slot=0, data=None):
        if save_slot == 0:
            self.on_select_locations()
            return
        elif save_slot == 1:
            sender.set_property('save-slot', 0)
            self.on_select_species()
            return

    def on_select_locations(self, sender=None, data=None):
        """Display the window for selecting the locations."""

        # Display the species selection window.
        select = setlyze.gui.SelectLocations(width=370, slot=0)
        select.set_title(setlyze.locale.text('analysis3'))

        # Change the header text.
        select.set_header("Locations Selection")
        select.set_description(setlyze.locale.text('select-locations') + "\n" +
            setlyze.locale.text('option-change-source') + "\n\n" +
            setlyze.locale.text('selection-tips')
            )

    def on_select_species(self, sender=None, data=None):
        """Display the window for selecting the species."""

        # Find out to which selection slot this species selection
        # should be saved.
        save_slot = setlyze.std.sender.get_property('save-slot')

        # Display the species selection window.
        select = setlyze.gui.SelectSpecies(width=500, slot=save_slot)
        select.set_title(setlyze.locale.text('analysis3'))
        select.set_description( setlyze.locale.text('select-species') + "\n\n" +
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
        locations = setlyze.config.cfg.get('locations-selection')
        species = setlyze.config.cfg.get('species-selection')

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing Analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)

        # Create analysis instance.
        t = Analysis(self.lock, locations, species)
        t.set_pdialog_handler(pdialog_handler)

        # Set the update steps for the progress handler.
        pdialog_handler.set_total_steps(t.get_total_steps())

        # Add the thread to the threads list.
        self.threads.append(t)

        # Start the analysis.
        t.start()

    def on_display_report(self, sender):
        """Display the report in a window.

        Design Part: 1.68
        """
        report = setlyze.config.cfg.get('analysis-report')
        setlyze.gui.DisplayReport(report)

class BeginBatch(Begin):
    """Make the preparations for batch analysis:

    1. Show a list of all localities and let the user perform a localities
       selection.

    2. Show a list of all species that match the locations selection and
       let the user perform the first species selection.

    3. Show a list of all species that match the locations selection and
       let the user perform the second species selection.

    4. Start the analysis.

    5. Show the analysis report to the user.
    """

    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")

    def on_start_analysis(self, sender=None, data=None):
        """Run the analysis in batch mode.

        Repeat the analysis for each possible combination of two species for
        the two species selections.
        """
        locations = setlyze.config.cfg.get('locations-selection')
        species = setlyze.config.cfg.get('species-selection')
        self.start_time = time.time()

        # Get all species combinations for the two species selections.
        species_combos = itertools.product(species[0], species[1])

        # Show a progress dialog.
        self.pdialog = setlyze.gui.ProgressDialog(title="Performing analysis",
            description=setlyze.locale.text('analysis-running'))

        # Create a progress dialog handler.
        pdialog_handler = setlyze.std.ProgressDialogHandler(self.pdialog)
        pdialog_handler.autoclose = False

        # Set the total number of times we decide to update the progress dialog.
        pdialog_handler.set_total_steps(
            (PROGRESS_STEPS + setlyze.config.cfg.get('test-repeats')) *
            len(species[0]) * len(species[1])
            )

        # Spawn a single worker thread.
        t = setlyze.analysis.common.Worker(self.queue, pdialog_handler)
        t.start()

        # Add the thread to the threads list.
        self.threads.append(t)

        # Populate the job queue.
        for sp_combo in species_combos:
            self.add_job(Analysis, self.lock, locations, sp_combo)

    def on_display_report(self, sender):
        """Display the report in a window."""
        logging.info( "Running time: %f" % (time.time() - self.start_time) )

class Analysis(setlyze.analysis.common.AnalysisWorker):
    """Perform the calculations for analysis 3.

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

    5. Calculate the inter-specific spot distances from the records in both
       species spots tables and save the distances to table
       "spot_distances_observed" in the local database.

    6. Calculate expected inter-specific spot distances by generating
       random spots and save the distances to table
       "spot_distances_expected" in the local database.

    7. Calculate the significance in difference between the observed and
       expected spot distances. Two tests of significance are performed:
       the Wilcoxon rank-sum test and the Chi-squared test.

    8. Generate the analysis report.

    Design Part: 1.5.2
    """

    def __init__(self, lock, locations_selection, species_selection):
        super(Analysis, self).__init__(lock)

        self.locations_selection = locations_selection
        self.species_selection = species_selection
        self.statistics = {'wilcoxon':[], 'chi_squared':[], 'repeats':{}}

        # Create log message.
        logging.info("Performing %s" % setlyze.locale.text('analysis3'))

        # Emit the signal that an analysis has started.
        setlyze.std.sender.emit('analysis-started')

    def get_total_steps(self):
        """Return the number of progress steps for this analysis.

        This equals to the total number of times we decide to update the
        progress dialog for a single analysis.

        Module constant `PROGRESS_STEPS` has to be set in the analysis module.
        """
        return PROGRESS_STEPS + self.n_repeats

    def generate_spot_ratio_groups(self):
        """Return an iterator that returns the ratio groups.

        Each returned group is a list of ratios in the form of two-item
        tuples.
        """
        for end in range(6, 31, 5):
            group = setlyze.std.combinations_with_replacement(xrange(1,end), 2)
            group = list(group)

            if end > 6:
                # Remove the ratios present in the previous group from
                # the current group.
                remove = setlyze.std.combinations_with_replacement(xrange(1,end-5), 2)
                setlyze.std.remove_items_from_list(group,remove)
            if end == 26:
                # Plates with a 25:25 ratio will never be significant.
                # So we remove this ratio, as it is useless.
                group.remove((25,25))

            yield group

        all_ratios = list(setlyze.std.combinations_with_replacement(xrange(1,26), 2))
        all_ratios.remove((25,25))

        yield all_ratios

    def run(self):
        """Call the necessary methods for the analysis in the right order:
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
            * :meth:`repeat_test`
            * :meth:`calculate_significance`
            * :meth:`generate_report`

        Design Part: 1.60
        """

        # Add a short delay. This gives the progress dialog time to
        # display properly.
        time.sleep(0.5)

        # Lock access to the database while we're accessing the shared
        # database resources.
        self._lock.acquire()

        # Make an object that facilitates access to the database.
        self.db = setlyze.database.get_database_accessor()

        if not self.stopped():
            # SELECTION 1

            # Update progress dialog.
            self.pdialog_handler.increase("Creating first table with species spots...")
            # Get the record IDs that match the selections.
            rec_ids1 = self.db.get_record_ids(self.locations_selection[0], self.species_selection[0])
            # Update progress dialog.
            logging.info("\tTotal records that match the first species+locations selection: %d" % len(rec_ids1))

            # Create log message.
            logging.info("\t\tCreating first table with species spots...")
            # Make a spots table for both species selections.
            self.db.set_species_spots(rec_ids1, slot=0)

            # Update progress dialog.
            self.pdialog_handler.increase("Making plate IDs in species spots table unique...")
            # Create log message.
            logging.info("\t\tMaking plate IDs in species spots table unique...")
            # Make the plate IDs unique.
            n_plates_unique = self.db.make_plates_unique(slot=0)
            # Create log message.
            logging.info("\t\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # SELECTION 2

            # Update progress dialog.
            self.pdialog_handler.increase("Creating second table with species spots...")
            # Get the record IDs that match the selections.
            rec_ids2 = self.db.get_record_ids(self.locations_selection[1], self.species_selection[1])
            # Create log message.
            logging.info("\tTotal records that match the second species+locations selection: %d" % len(rec_ids2))

            # Create log message.
            logging.info("\t\tCreating second table with species spots...")
            # Make a spots table for both species selections.
            self.db.set_species_spots(rec_ids2, slot=1)

            # Update progress dialog.
            self.pdialog_handler.increase("Making plate IDs in species spots table unique...")
            # Create log message.
            logging.info("\t\tMaking plate IDs in species spots table unique...")
            # Make the plate IDs unique.
            n_plates_unique = self.db.make_plates_unique(slot=1)
            # Create log message.
            logging.info("\t\t  %d records remaining." % (n_plates_unique))

        if not self.stopped():
            # GENERAL

            # Create log message.
            logging.info("\tSaving the positive spot totals for each plate...")
            # Update progress dialog.
            self.pdialog_handler.increase("Saving the positive spot totals for each plate...")
            # Save the positive spot totals for each plate to the database.
            self.db.fill_plate_spot_totals_table('species_spots_1','species_spots_2')

            # Update progress dialog.
            self.pdialog_handler.increase("Calculating the inter-specific distances for the selected species...")
            # Create log message.
            logging.info("\tCalculating the inter-specific distances for the selected species...")
            # Calculate the observed spot distances.
            self.calculate_distances_inter()

            # Create log message.
            logging.info("\tPerforming statistical tests with %d repeats..." %
                setlyze.config.cfg.get('test-repeats'))
            # Update progress dialog.
            self.pdialog_handler.increase("Performing statistical tests with %s repeats..." %
                setlyze.config.cfg.get('test-repeats'))
            # Perform the repeats for the statistical tests. This will repeatedly
            # calculate the expected totals, so we'll use the expected values
            # of the last repeat for the non-repeated tests.
            self.repeat_test(setlyze.config.cfg.get('test-repeats'))

        if not self.stopped():
            # Create log message.
            logging.info("\tPerforming statistical tests...")
            # Update progress dialog.
            self.pdialog_handler.increase("Performing statistical tests...")
            # Performing the statistical tests. The expected values for the last
            # repeat is used for this test.
            self.calculate_significance()

            # Create log message.
            logging.info("\tGenerating the analysis report...")
            # Update progress dialog.
            self.pdialog_handler.increase("Generating the analysis report...")

        # If the cancel button is pressed don't finish this function.
        if self.stopped():
            logging.info("Analysis aborted by user")

            # Release the lock to shared resources.
            self._lock.release()
            return

        # Generate the report.
        self.generate_report()

        # Update progress dialog.
        self.pdialog_handler.increase("")

        # Emit the signal that the analysis has finished.
        # Note that the signal will be sent from a separate thread,
        # so we must use gobject.idle_add.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')
        logging.info("%s was completed!" % setlyze.locale.text('analysis3'))

        # Release the lock to shared resources.
        self._lock.release()

    def calculate_distances_inter(self):
        """Calculate the inter-specific spot distances for each plate
        and save the distances to table "spot_distances_observed" in
        the local database.

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

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

    def calculate_distances_inter_expected(self):
        """Calculate the expected distances based on the observed
        inter-specific distances and save these to table
        "spot_distances_expected" in the local database.

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
        connection.close()

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

            # Perform a consistency check. The number of observed and
            # expected spot distances must always be the same.
            count_observed = len(observed)
            count_expected = len(expected)
            if count_observed != count_expected:
                raise ValueError("Number of observed and expected spot "
                    "distances are not equal. This indicates a bug "
                    "in the application.")

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this ratio group if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - setlyze.config.cfg.get('alpha-level'),
                conf_int = False)

            # Save the significance result.
            data = {}
            data['attr'] = {
                'ratio_group': n_group,
                'n_plates': n_plates,
                'n': count_observed,
                'method': sig_result['method'],
                'alternative': sig_result['alternative'],
                'conf_level': 1 - setlyze.config.cfg.get('alpha-level'),
                'paired': False,
                }
            data['results'] = {
                'p_value': sig_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
                #'conf_int_start': sig_result['conf.int'][0],
                #'conf_int_end': sig_result['conf.int'][1],
                }

            # Append the result to the list of results.
            self.statistics['wilcoxon'].append(data)

            # Get the probability for each spot distance. Required for
            # the Chi-squared test.
            spot_dist_to_prob = setlyze.config.cfg.get('spot-dist-to-prob-inter')

            # Get the frequencies for the observed distances. These
            # are required for the Chi-squared test.
            observed_freq = setlyze.std.distance_frequency(observed, 'inter')

            # Also perform Chi-squared test.
            sig_result = setlyze.std.chisq_test(observed_freq.values(),
                p = spot_dist_to_prob.values())

            # Save the significance result.
            data = {}
            data['attr'] = {
                'ratio_group': n_group,
                'n_plates': n_plates,
                'n': count_observed,
                'method': sig_result['method'],
                }
            data['results'] = {
                'chi_squared': sig_result['statistic']['X-squared'],
                'p_value': sig_result['p.value'],
                'df': sig_result['parameter']['df'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
                }

            # Append the result to the list of results.
            self.statistics['chi_squared'].append(data)

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

            # Check if this ratios group is present in the statistics variable.
            # If not, create it.
            if n_group not in self.statistics['repeats']:
                self.statistics['repeats'][n_group] = {'n_significant': 0,
                    'n_attraction': 0, 'n_repulsion': 0}

            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_distances_matching_ratios(
                'spot_distances_observed', ratio_group)
            expected = self.db.get_distances_matching_ratios(
                'spot_distances_expected', ratio_group)

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
            # significance test. So skip this ratio group if it's less.
            if count_observed < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = 1 - setlyze.config.cfg.get('alpha-level'),
                conf_int = False)

            # Save basic results for this repeated test.
            # Check if the result was significant (P-value < alpha-level).
            p_value = float(sig_result['p.value'])
            if p_value < setlyze.config.cfg.get('alpha-level') and p_value != 'nan':
                # If so, increase significant counter with one.
                self.statistics['repeats'][n_group]['n_significant'] += 1

                # If significant, also check if there is preference or
                # rejection for this plate area.
                if mean_observed < mean_expected:
                    # Increase attracion counter with one.
                    self.statistics['repeats'][n_group]['n_attraction'] += 1
                else:
                    # Increase repulsion counter with one.
                    self.statistics['repeats'][n_group]['n_repulsion'] += 1

    def repeat_test(self, number):
        """Repeats the siginificance test `number` times. The significance
        test is performed by :meth:`calculate_significance_for_repeats`.

        Each time before :meth:`calculate_significance_for_repeats` is called,
        :meth:`calculate_distances_inter_expected` is called to re-calculate the
        expected values (which are random).

        Design Part: 1.105
        """
        for i in range(number):
            if self.stopped():
                return

            # Update the progess bar.
            self.pdialog_handler.increase()

            # The expected spot distances are random. So the expected values
            # differ a little on each repeat.
            self.calculate_distances_inter_expected()

            # And then we calculate the siginificance for each repeat.
            self.calculate_significance_for_repeats()

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.15
        """
        report = setlyze.report.ReportGenerator()
        report.set_analysis('attraction_inter')
        report.set_location_selections()
        report.set_species_selections()

        # Update progress dialog.
        self.pdialog_handler.increase("Generating the analysis report...")

        report.set_spot_distances_observed()

        # Update progress dialog.
        self.pdialog_handler.increase("Generating the analysis report...")

        report.set_spot_distances_expected()

        report.set_statistics('wilcoxon_ratios', self.statistics['wilcoxon'])
        report.set_statistics_repeats('wilcoxon_ratios', self.statistics['repeats'])
        report.set_statistics('chi_squared_ratios', self.statistics['chi_squared'])

        # Create a global link to the report.
        setlyze.config.cfg.set('analysis-report', report.get_report())
