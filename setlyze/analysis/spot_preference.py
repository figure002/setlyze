#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
#
#  This file is part of SETLyze - A tool for analyzing the settlement of species.
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
8. Generate the anayslis report.
9. Show the analysis report to the user.

"""

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

__author__ = "Jonathan den Boer, Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

class Begin(object):
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
        # Create log message.
        logging.info("Beginning Analysis 1 \"Spot preference\"")

        # Bind handles to application signals.
        self.handle_application_signals()

        # Reset the settings when an analysis is beginning.
        setlyze.config.cfg.set('locations-selection', None)
        setlyze.config.cfg.set('species-selection', None)
        setlyze.config.cfg.set('plate-areas-definition', None)

        # Emit the signal that we are beginning with an analysis.
        setlyze.std.sender.emit('beginning-analysis')

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

        # Display the report after the analysis has finished.
        self.handler12 = setlyze.std.sender.connect('analysis-finished',
            self.on_display_report)

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

    def on_analysis_aborted(self, sender):
        setlyze.config.cfg.get('progress-dialog').destroy()

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
        t.start()

    def on_display_report(self, sender):
        """Display the report in a window.

        Design Part: 1.68
        """
        report = setlyze.config.cfg.get('analysis-report')
        setlyze.gui.DisplayReport(report)

class Start(threading.Thread):
    """Perform the calculations for analysis 1.

    1. Calculate the observed species frequencies for the plate areas.

    2. Check if all plate area frequencies are zero. If so, abort.

    3. Calculate the expected species frequencies for the plate areas.

    4. Calculate the significance in difference between the observed and
       expected area totals. The Chi-squared test is used for this.

    5. Generate the anayslis report.

    Design Part: 1.3.2
    """

    def __init__(self):
        super(Start, self).__init__()

        self.dbfile = setlyze.config.cfg.get('db-file')
        self.total_species = None
        self.mean = None
        self.areas_totals_observed = None # Design Part: 2.25
        self.areas_totals_expected = None # Design Part: 2.26
        self.area2chisquare = None
        self.chisquare = None
        # Dictionary for the statistic test results.
        self.statistics = {'wilcoxon':[], 'chi_squared':[]}

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
        total_steps = 9.0

        # Make an object that facilitates access to the database.
        self.db = setlyze.database.get_database_accessor()

        # Get the record IDs that match the localities+species selection.
        locations_selection = setlyze.config.cfg.get('locations-selection', slot=0)
        species_selection = setlyze.config.cfg.get('species-selection', slot=0)
        rec_ids = self.db.get_record_ids(locations_selection, species_selection)
        # Create log message.
        logging.info("\tTotal records that match the species+locations selection: %d" % len(rec_ids))

        # Create log message.
        logging.info("\tCreating table with species spots...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(1/total_steps, "Creating table with species spots...")
        # Make a spots table for the selected species.
        self.db.set_species_spots(rec_ids, slot=0)

        # Create log message.
        logging.info("\tMaking plate IDs in species spots table unique...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(2/total_steps, "Making plate IDs in species spots table unique...")
        # Make the plate IDs unique.
        n_plates_unique = self.db.make_plates_unique(slot=0)
        # Create log message.
        logging.info("\t  %d records remaining." % (n_plates_unique))

        # Update progress dialog.
        setlyze.std.update_progress_dialog(3/total_steps,
            "Calculating the observed plate area totals for each plate...")
        # Calculate the expected totals.
        self.set_plate_area_totals_observed()

        # Create log message.
        logging.info("\tPerforming statistical tests with %d repeats..." %
            setlyze.config.cfg.get('test-repeats'))
        # Update progress dialog.
        setlyze.std.update_progress_dialog(4/total_steps,
            "Performing statistical tests with %s repeats..." %
            setlyze.config.cfg.get('test-repeats'))
        # Perform the repeats for the statistical tests. This will repatedly
        # calculate the expected totals, so we'll use the expected totals
        # of the last repeat as the results for the report dialog.
        self.repeat_test(setlyze.config.cfg.get('test-repeats'))

        # Update progress dialog.
        setlyze.std.update_progress_dialog(5/total_steps,
            "Calculating observed species totals per plate area...")
        # Calculate the species totals.
        self.areas_totals_observed = self.get_defined_areas_totals_observed()
        # Create log message.
        logging.info("\tObserved species totals: %s" % self.areas_totals_observed)

        # Make sure that spot area totals are not all zero. If so, abort
        # the analysis, because we can't devide by zero (unless you're
        # Chuck Norris of course).
        areas_total = 0
        for area_total in self.areas_totals_observed.itervalues():
            areas_total += area_total

        if areas_total == 0:
            # Create log message.
            logging.info("\tAll plate areas totals are zero. Aborting.")
            # Send signal the analysis was aborted.
            setlyze.std.sender.emit('analysis-aborted')
            return

        # Update progress dialog.
        setlyze.std.update_progress_dialog(6/total_steps,
            "Calculating expected species totals per plate area...")
        # Calculate the expected totals.
        self.areas_totals_expected = self.get_defined_areas_totals_expected()
        # Create log message.
        logging.info("\tExpected species totals: %s" % self.areas_totals_expected)

        # Create log message.
        logging.info("\tPerforming statistical tests...")
        # Update progress dialog.
        setlyze.std.update_progress_dialog(7/total_steps,
            "Performing statistical tests...")
        # Performing the statistical tests.
        self.calculate_significance()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(8/total_steps,
            "Generating the analysis report...")
        # Generate the report.
        self.generate_report()

        # Update progress dialog.
        setlyze.std.update_progress_dialog(9/total_steps, "")

        # Emit the signal that the analysis has finished.
        # Note that the signal will be sent from a separate thread,
        # so we must use gobject.idle_add.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')

    def set_plate_area_totals_observed(self):
        """Fill the 'plate_area_totals_observed' table."""
        locations_selection = setlyze.config.cfg.get('locations-selection', slot=0)
        species_selection = setlyze.config.cfg.get('species-selection', slot=0)

        # From plate area to spot numbers.
        area2spots = {'A': (1,5,21,25),
            'B': (2,3,4,6,10,11,15,16,20,22,23,24),
            'C': (7,8,9,12,14,17,18,19),
            'D': (13,),
            }

        connection = sqlite.connect(self.dbfile)
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
        connection.close()

    def set_plate_area_totals_expected(self):
        """Fill the 'plate_area_totals_expected' table."""

        # From plate area to spot numbers.
        area2spots = {'A': (1,5,21,25),
            'B': (2,3,4,6,10,11,15,16,20,22,23,24),
            'C': (7,8,9,12,14,17,18,19),
            'D': (13,),
            }

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
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
        connection.close()

    def calculate_significance(self):
        """TODO"""

        # The area groups to perfom the test on.
        area_groups = [('A'),('B'),('C'),('D'),('A','B'),('C','D'),
            ('A','B','C'),('B','C','D')]

        for area_group in area_groups:
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)
            expected = self.db.get_area_totals(
                'plate_area_totals_expected', area_group)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Perform a consistency check. The number of observed and
            # expected spot distances must always be the same.
            count_observed = len(observed)
            count_expected = len(expected)

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this spots number if it's less.
            if count_observed < 2 or count_expected < 2:
                continue

            # Calculate the means.
            mean_observed = setlyze.std.mean(observed)
            mean_expected = setlyze.std.mean(expected)

            # Create a human readable string with the areas in the area group.
            area_group_str = "+".join(area_group)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = setlyze.config.cfg.get('significance-confidence'),
                conf_int = False)

            # Save the significance result.
            data = {}
            data['attr'] = {
                'area_group': area_group_str,
                'n': count_observed,
                'method': sig_result['method'],
                'alternative': sig_result['alternative'],
                'conf_level': setlyze.config.cfg.get('significance-confidence'),
                'paired': False,
                }
            data['results'] = {
                'p_value': sig_result['p.value'],
                'mean_observed': mean_observed,
                'mean_expected': mean_expected,
                }

            # Append the result to the list of results.
            self.statistics['wilcoxon'].append(data)

    def calculate_significance_for_repeats(self):
        """TODO"""

        # The area groups to perfom the test on.
        area_groups = [('A'),('B'),('C'),('D'),('A','B'),('C','D'),
            ('A','B','C'),('B','C','D')]

        for area_group in area_groups:
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)
            expected = self.db.get_area_totals(
                'plate_area_totals_expected', area_group)

            # Iterators cannot be used directly by RPy, so convert them to
            # lists first.
            observed = list(observed)
            expected = list(expected)

            # Perform a consistency check. The number of observed and
            # expected spot distances must always be the same.
            count_observed = len(observed)
            count_expected = len(expected)

            # A minimum of 2 observed distances is required for the
            # significance test. So skip this spots number if it's less.
            if count_observed < 2 or count_expected < 2:
                continue

            # Create a human readable string with the areas in the area group.
            area_group_str = "+".join(area_group)

            # Perform two sample Wilcoxon tests.
            sig_result = setlyze.std.wilcox_test(observed, expected,
                alternative = "two.sided", paired = False,
                conf_level = setlyze.config.cfg.get('significance-confidence'),
                conf_int = False)

            # Save the significance result.
            p_value = float(sig_result['p.value'])
            if p_value < 0.05 and p_value != 'nan':
                self.repeat_results[area_group_str] += 1

    def repeat_test(self, number):
        self.repeat_results = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'A+B': 0, 'C+D': 0,
            'A+B+C': 0, 'B+C+D': 0}

        for i in range(number):
            self.set_plate_area_totals_expected()
            self.calculate_significance_for_repeats()

        print self.repeat_results

    def get_defined_areas_totals_observed(self):
        """Return the observed totals for a species for each plate area.

        Design Part: 1.62
        """
        areas_definition = setlyze.config.cfg.get('plate-areas-definition')

        # Dictionary which will contain the species total for each area.
        areas_totals_observed = {'area1': 0,
            'area2': 0,
            'area3': 0,
            'area4': 0,}

        for area_name, area_group in areas_definition.iteritems():
            # Get both sets of distances from plates per total spot numbers.
            observed = self.db.get_area_totals(
                'plate_area_totals_observed', area_group)

            # Sum all totals in the correct area name.
            for total in observed:
                areas_totals_observed[area_name] += total

        # Remove the areas that were earlier removed, as these areas
        # were empty, and shouldn't be included for the calculations
        # later on.
        for area_name in areas_definition:
            if len(area_name) == 0:
                del areas_totals_observed[area_name]

        return areas_totals_observed

    def get_defined_areas_totals_expected(self):
        """Return the expected totals for a species for each plate area.

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

    def generate_report(self):
        """Generate the analysis report.

        Design Part: 1.13
        """
        report = setlyze.std.ReportGenerator()
        report.set_analysis('spot_preference')
        report.set_location_selections()
        report.set_species_selections()
        report.set_plate_areas_definition()
        report.set_area_totals_observed(self.areas_totals_observed)
        report.set_area_totals_expected(self.areas_totals_expected)
        report.set_statistics('wilcoxon_areas', self.statistics['wilcoxon'])
        report.set_significance_test_repeats_areas(self.repeat_results)

        # Create global a link to the report.
        setlyze.config.cfg.set('analysis-report', report.get_report())


