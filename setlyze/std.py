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

import sys
import os
import math
import itertools
import random
import logging
import time
import xml.dom.minidom
from sqlite3 import dbapi2 as sqlite

import gobject
import rpy

import setlyze.config

"""This module provides standard functions and classes."""

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/10/01 13:42:16"

def update_progress_dialog(fraction, action=None, autoclose=True):
    """Set a new fraction for the progress bar."""
    pdialog = setlyze.config.cfg.get('progress-dialog')

    # If no progress dialog is set, do nothing.
    if not pdialog:
        return

    # This is always called from a separate thread, so we must use
    # gobject.idle_add to access the GUI.
    gobject.idle_add(on_update_progress_dialog, fraction, action, autoclose)

def on_close_progress_dialog(delay=0):
    """Close the progress dialog. Optionally set a delay before it's
    being closed.

    There's no need to call this function manually, as it is called
    by :meth:`on_update_progress_dialog` when it's needed.
    """
    pdialog = setlyze.config.cfg.get('progress-dialog')

    # If a delay is set, sleep 'delay' seconds.
    if delay: time.sleep(delay)

    # Close the dialog along with emitting the signal.
    pdialog.on_close()

    # This callback function must return False, so it is
    # automatically removed from the list of event sources.
    return False

def on_update_progress_dialog(fraction, action=None, autoclose=True):
    """Update the progress dialog fraction and action-string. Optionally
    set autoclose if fraction equals 1.0.

    Don't call this function manually; use :meth:`update_progress_dialog`
    instead.
    """
    pdialog = setlyze.config.cfg.get('progress-dialog')

    # Update fraction.
    pdialog.pbar.set_fraction(fraction)

    # Set percentage text for the progress bar.
    percent = fraction * 100.0
    pdialog.pbar.set_text("%.0f%%" % percent)

    # Show the current action below the progress bar.
    if isinstance(action, str):
        action = "<span style='italic'>%s</span>" % (action)
        pdialog.action.set_markup(action)

    if fraction == 1.0:
        pdialog.pbar.set_text("Finished!")
        pdialog.button_close.set_sensitive(True)

        if autoclose:
            # Close the progress dialog when finished. We set a delay
            # of 1 second before closing it, so the user observedly gets
            # to see the dialog when an analysis finishes very fast.

            # This is always called from a separate thread, so we must
            # use gobject.idle_add to access the GUI.
            gobject.idle_add(on_close_progress_dialog, 1)

    # This callback function must return False, so it is
    # automatically removed from the list of event sources.
    return False

def uniqify(seq):
    """Remove all duplicates from a list."""
    return {}.fromkeys(seq).keys()

def median(values):
    """Return the median of a series of numbers."""
    values = sorted(values)
    count = len(values)

    if count % 2 == 1:
        return values[(count+1)/2-1]
    else:
        lower = values[count/2-1]
        upper = values[count/2]
        return (float(lower + upper)) / 2

def distance(p1, p2):
    """Use the Pythagorean theorem to calculate the distance between
    two spots.
    """
    val = math.sqrt(p1**2 + p2**2)

    # Round the value to the second decimal. High precision is useless
    # for spot distances and takes too much space in the local database.
    val = round(val, 2)

    return val

def get_spot_combinations_from_record(record1, record2=None):
    """Return all possible positive spot combinations from `record1` or
    between `record1` and `record2`. Each record must be a sequence of
    25 spot booleans.

    If just `record1` was provided, return all possible positive spot
    combinations within this record. If both `record1` and `record2` are
    given, return all possible positive spot combinations between the
    the two records. If no combinations are possible (i.e. not enough
    positive spots), and empty list will be returned.

    This method returns an iterable object, which returns the
    combinations as tuples with two items. Each item is the spot number
    of a positive spot.

    Example, get all possible combinations within one records ::

        >>> import setlyze.std
        >>> record = (4567,1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
        >>> combos = setlyze.std.get_spot_combinations_from_record(record[1:])
        >>> for spot1,spot2 in combos:
        ...     print spot1,spot2
        ...
        1 2
        1 5
        1 15
        2 5
        2 15
        5 15

    Example, get all possible combinations between two records ::

        >>> import setlyze.std
        >>> record1 = (4567,1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
        >>> record2 = (4538,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1)
        >>> combos = setlyze.std.get_spot_combinations_from_record(record1[1:], record2[1:])
        >>> for spot1,spot2 in combos:
        ...     print spot1,spot2
        ...
        1 3
        1 25
        2 3
        2 25
        5 3
        5 25
        15 3
        15 25

    """
    spots1 = get_spots_from_record(record1)

    if not record2:
        # Create a generator with all the possible positive spot
        # combinations within a record.
        combos = itertools.combinations(spots1,2)
    else:
        spots2 = get_spots_from_record(record2)
        # Create a generator with the Cartesian product of the
        # positive spots in two records.
        combos = itertools.product(spots1,spots2)

    # Return the generator that contains all combinations.
    return combos

def get_spots_from_record(record):
    """Return a list with all numbers of the positive spots.

    Example:
    record = (1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
    print get_spots_from_record(record)

    This would print [1,2,5,15]
    """
    spots = []
    for i, spot in enumerate(record, start=1):
        if spot:
            spots.append(i)
    return spots

def get_spot_coordinate(spot_num):
    """Return a tuple (row,col) representing on which row and column a
    spot is located on a 5x5 SETL plate.

    Keyword arguments:
    spot_num -  The spot number (1 - 25)
    """
    if not 1 <= spot_num <= 25:
        logging.error("The spot number must be an integer between 0 and "
            "26. Instead got: %s" % spot_num)
        sys.exit(1)

    rows = [(1,2,3,4,5),
            (6,7,8,9,10),
            (11,12,13,14,15),
            (16,17,18,19,20),
            (21,22,23,24,25)]

    cols = [(1,6,11,16,21),
            (2,7,12,17,22),
            (3,8,13,18,23),
            (4,9,14,19,24),
            (5,10,15,20,25)]

    # Figure out the row number of the spot number.
    for row_num,row in enumerate(rows, start=1):
        if spot_num in row:
            row = row_num
            break
    # Figure out the column number of the spot number.
    for col_num,col in enumerate(cols, start=1):
        if spot_num in col:
            col = col_num
            break

    return (row,col)

def get_spot_position_difference(s1, s2):
    """Return the horizontal and vertical difference between two spots.

    Keyword arguments:
    s1 -  Integer, first spot number (1 - 25).
    s2 -  Integer, second spot number (1 - 25).

    Returns:
    A tuple: (h,v)
        h = horizontal difference (delta X)
        v = vertical difference (delta Y)
    """

    # Calculate the coordinates for both spots.
    s1 = get_spot_coordinate(s1)
    s2 = get_spot_coordinate(s2)

    # Calculate the vertical and horizontal difference between the spot
    # coordinates.
    v = abs(s1[0]-s2[0])
    h = abs(s1[1]-s2[1])

    return (h,v)

def get_random_for_plate(n):
    """Return n random spots from a single plate.

    We make use of the random.sample function from the Python standard
    library. This function used the system time as the random seed.

    Keyword arguments:
    n - Number of random positive spots to be generated. This must be
        a value ranging from 1 to 25.

    Return: A list with n random values ranging from 1 to 25 without
            replacement.
    """
    spots = random.sample(xrange(1,26), n)
    return spots

def combine_by_plate(records):
    """Combine SETL records that have the same plate ID. `records`
    is a tuple containing multiple SETL records. Each record must consist
    of a plate ID as the fisrt item followed by 25 spot booleans.

    If one spot in a column contains 1, the resulting spot becomes 1.
    If all spots from a column are 0, the resulting spot becomes 0.

    If this isn't very clear, look at this visual example. Let's say
    `records` has the following 3 records. Notice that they must have the
    same plate ID:

    (4567,1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
    (4567,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1)
    (4567,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0)

    The following combined record would then be returned:

    (4567,1,1,1,0,1,0,0,0,0,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1)
    """
    combined = [None,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    # Set the plate ID.
    if len(records):
        combined[0] = records[0][0]

    for record in records:
        # Make sure all plate IDs are the same.
        if combined[0] != record[0]:
            sys.exit("setlyze.std.combine_by_plate: 'records' argument must "
                "contain records with the same plate ID.")

        # For each positive spot we find, set that spot in the combined
        # record to 1.
        for i, spot in enumerate(record[1:], start=1):
            # We skip the first item, as that's the plate ID.
            # If spot is positive, set the same spot in 'combined'
            # to 1.
            if spot:
                combined[i] = 1

    return combined

def t_test(x, y = None, alternative = "two.sided", mu = 0,
            paired = False, var_equal = False, conf_level = 0.95):
    """Performs one and two sample t-tests on sequences of data.

    Keyword arguments:
    x -  A sequence of numeric values.

    Returns: A dictionary,
    """
    result = rpy.r['t.test'](x, y, alternative, mu, paired,
        var_equal, conf_level)

    return result

def wilcox_test(x, y = None, alternative = "two.sided",
                 mu = 0, paired = False, exact = None, correct = True,
                 conf_int = False, conf_level = 0.95):
    """Performs one and two sample Wilcoxon tests on vectors of data; the
    latter is also known as ‘Mann-Whitney’ test.

    Keyword arguments:
    x -  A sequence of numeric values.

    Returns: A dictionary,
    """
    result = rpy.r['wilcox.test'](x, y, alternative, mu, paired, exact,
        correct, conf_int, conf_level)

    return result

def shapiro_test(x):
    """Performs the Shapiro-Wilk test of normality.

    Keyword arguments:
    x -  A sequence of numeric values.

    Returns: A dictionary,
        {
        'method': 'Shapiro-Wilk normality test',
        'p.value': <P-value>,
        'statistic': {'W': <W-value>}
        }
    """
    if len(x) > 5000:
        rand_items = random.sample(x, 5000)
        result = rpy.r['shapiro.test'](rand_items)
    elif len(x) < 3:
        return None
    else:
        result = rpy.r['shapiro.test'](x)

    return result

def average(values):
    """Computes the arithmetic mean of a sequence of numbers."""
    return sum(values, 0.0) / len(values)


class Sender(gobject.GObject):
    """Custom sender for emitting SETLyze specific application signals."""

    __gproperties__ = {
        'save-slot' : (gobject.TYPE_INT, # type
            'Save slot for selections.', # nick name
            'Save slot for selections. There are two slots possible (0 and 1).', # description
            0, # minimum value
            1, # maximum value
            0, # default value
            gobject.PARAM_READWRITE), # flags
    }

    # Create custom application signals.
    __gsignals__ = {
        'beginning-analysis': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-started': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'locations-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'species-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'define-areas-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'local-db-created': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'locations-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'species-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'plate-areas-defined': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'save-analysis-report-as': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,gobject.TYPE_STRING)),

        'analysis-aborted': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'selection-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'define-areas-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'report-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'progress-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.save_slot = 0

    def do_get_property(self, property):
        if property.name == 'save-slot':
            return self.save_slot
        else:
            raise AttributeError, 'unknown property %s' % property.name

    def do_set_property(self, property, value):
        if property.name == 'save-slot':
            self.save_slot = value
        else:
            raise AttributeError, 'unknown property %s' % property.name

class ReportGenerator(object):
    """Create a XML DOM (Document Object Model) object of the analysis
    settings and results. The DOM can then be exported to an XML file.

    Design Part: 1.48
    """

    def __init__(self):
        self.ns = "http://www.gimaris.com/setlyze/"
        self.dbfile = setlyze.config.cfg.get('db-file')

        # Create a new XML DOM object (Design Part: 2.17).
        self.doc = xml.dom.minidom.Document()
        # Create the top report element.
        self.report = self.doc.createElementNS(self.ns, "setlyze:report")
        # Manually add the namespace to the top element.
        self.report.setAttribute("xmlns:setlyze", self.ns)
        self.doc.appendChild(self.report)

    def create_element(self, parent, name, child_elements={}, attributes={}, text=None):
        # Create a new element.
        element = self.doc.createElementNS(self.ns, name)

        # Make this new element a child of the provided parent element.
        if parent:
            parent.appendChild(element)

        # Add attributes.
        for key,val in attributes.iteritems():
            element.setAttribute(str(key), str(val))

        # Add child elements.
        for key,val in child_elements.iteritems():
            child_element = self.doc.createElementNS(self.ns, key)
            text_node = self.doc.createTextNode(str(val))
            child_element.appendChild(text_node)
            element.appendChild(child_element)

        # Add a text element.
        if text != None:
            text_node = self.doc.createTextNode(str(text))
            element.appendChild(text_node)

        return element

    def set_analysis(self, name):
        """Create a new element in the XML DOM report that describes
        which analysis this report belongs to.

        Design Part: 1.72
        """

        # A dictinary with all the known analysis.
        analysis_names = {'spot_preference': "Spot Preference",
            'attraction_intra': "Attraction of Species (intra-specific)",
            'attraction_inter': "Attraction of Species (inter-specific)",
            'relations': "Relation between Species",
            }

        # Check if the provided name is present in the list of
        # analysis names. If so, use the name from the list.
        # If 'name' is not in the list, do nothing and just use the
        # name as it is.
        if name in analysis_names:
            name = analysis_names[name]

        # Create the element.
        self.create_element(parent=self.report,
            name="analysis",
            text=name
            )

    def set_location_selections(self):
        """Create the element 'location_selections' in the XML DOM report
        that contains the user selected locations.

        Design Part: 1.50
        """

        # Create a new element to save the location selections in.
        location_selections = self.create_element(
            parent=self.report,
            name="location_selections"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for slot in (0,1):
            # Get the locations selection for each slot.
            loc_ids = setlyze.config.cfg.get('locations-selection',
                slot=slot)

            # Skip to the next slot if this selection is not set.
            if not loc_ids:
                continue

            # Create a 'locations_selection' child element for each
            # selection. We give each selection element a 'slot'
            # attribute.
            loc_selection_element = self.create_element(
                parent=location_selections,
                name="selection",
                attributes={'slot': slot}
                )

            # Fetch all information about the locations selection.
            loc_ids_str = ",".join([str(id) for id in loc_ids])
            cursor.execute( "SELECT loc_id,loc_name,loc_nr "
                            "FROM localities "
                            "WHERE loc_id IN (%s)" %
                            (loc_ids_str)
                            )

            for row in cursor:
                self.create_element(parent=loc_selection_element,
                    name="location",
                    child_elements={'name':row[1], 'nr':row[2]},
                    attributes={'id':row[0]}
                    )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_specie_selections(self):
        """Create the element 'specie_selections' in the XML DOM report
        that contains the user selected species.

        Design Part: 1.51
        """

        # Create a new element to save the specie selections in.
        specie_selections = self.create_element(
            parent=self.report,
            name="specie_selections"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for slot in (0,1):
            # Get the species selection for each slot.
            spe_ids = setlyze.config.cfg.get('species-selection',
                slot=slot)

            # Skip to the next slot if this selection is not set.
            if not spe_ids:
                continue

            # Create a 'species_selection' child element for each
            # selection. We give each selection element a 'slot'
            # attribute.
            spe_selection_element = self.create_element(
                parent=specie_selections,
                name="selection",
                attributes={'slot': slot}
                )

            # Fetch all information about the species selection.
            spe_ids_str = ",".join([str(id) for id in spe_ids])
            cursor.execute( "SELECT spe_id,spe_name_venacular,spe_name_latin "
                            "FROM species "
                            "WHERE spe_id IN (%s)" %
                            (spe_ids_str)
                            )

            for row in cursor:
                self.create_element(parent=spe_selection_element,
                    name="specie",
                    child_elements={'name_venacular': row[1],'name_latin': row[2]},
                    attributes={'id':row[0]}
                    )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_observed(self):
        """Create the element 'spot_distances_observed' in the XML DOM
        report that contains the observed spot distances.

        Design Part: 1.52
        """

        # Create a new child element for the report.
        distances_observed_element = self.create_element(
            parent=self.report,
            name="spot_distances_observed"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the observed distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_observed"
                        )

        for row in cursor:
            self.create_element(parent=distances_observed_element,
                name="distance",
                attributes={'plate_id': row[0]},
                text=row[1]
                )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_expected(self):
        """Create the element 'spot_distances_expected' in the XML DOM
        report that contains the expected spot distances.

        Design Part: 1.53
        """

        # Create a new child element for the report.
        distances_expected_element = self.create_element(
            parent=self.report,
            name="spot_distances_expected"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the observed distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_expected"
                        )

        for row in cursor:
            self.create_element(parent=distances_expected_element,
                name="distance",
                attributes={'plate_id': row[0]},
                text=row[1]
                )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_plate_areas_definition(self):
        """Create the element 'plate_areas_definition' in the XML DOM
        report that contains the user defined spot areas definition.

        Design Part: 1.54
        """

        # Get the spot areas definition.
        definition = setlyze.config.cfg.get('plate-areas-definition')

        # Create a new element for the areas definition.
        areas_definition_element = self.create_element(
            parent=self.report,
            name="plate_areas_definition"
            )

        for area, spots in definition.iteritems():
            area_element = self.create_element(
                parent=areas_definition_element,
                name="area",
                attributes={'id':area}
                )
            for spot in spots:
                self.create_element(
                    parent=area_element,
                    name="spot",
                    text=spot
                    )

    def set_area_totals_observed(self, totals_observed):
        """Create the element 'area_totals_observed' in the XML DOM
        report that contains the observed species totals per plate area.

        Design Part: 1.55
        """

        # Create a new child element for the report.
        species_totals_element = self.create_element(
            parent=self.report,
            name="area_totals_observed"
            )

        for area, total in totals_observed.iteritems():
            self.create_element(parent=species_totals_element,
                name="area",
                attributes={'id': area},
                text=total
                )

    def set_area_totals_expected(self, totals_observed):
        """Create the element 'area_totals_expected' in the XML DOM
        report that contains the expected species totals per plate area.

        Design Part: 1.56
        """

        # Create a new child element for the report.
        species_totals_element = self.create_element(
            parent=self.report,
            name="area_totals_expected"
            )

        for area, total in totals_observed.iteritems():
            self.create_element(parent=species_totals_element,
                name="area",
                attributes={'id': area},
                text=total
                )

    def set_statistics_normality(self, results):
        """Create the element 'statistics_normality' in the XML DOM
        report that contains the results of the performed statistical
        tests.

        Keyword arguments:
        results - A dictionary,
            {
            'attr': {'<name>': <value>, ...},
            'items': {'<name>': <value>, ...}
            }

            Where 'attr' contains the attributes and 'items' are the
            sub-elements for the 'statistics_normality' element.

        Design Part: 1.70
        """

        # Create a new child element for the report.
        statistics_element = self.create_element(
            parent=self.report,
            name="statistics_normality"
            )

        for result in results:
            self.create_element(
                parent=statistics_element,
                name="result",
                attributes=result['attr'],
                child_elements=result['items'],
                )

    def set_statistics_significance(self, results):
        """Create the element 'statistics_significance' in the XML DOM
        report that contains the results of the performed statistical
        tests.

        Keyword arguments:
        results - A dictionary,
            {
            'attr': {'<name>': <value>, ...},
            'items': {'<name>': <value>, ...}
            }

            Where 'attr' contains the attributes and 'items' are the
            sub-elements for the 'statistics_significance' element.

        Design Part: 1.71
        """

        # Create a new child element for the report.
        statistics_element = self.create_element(
            parent=self.report,
            name="statistics_significance"
            )

        for result in results:
            self.create_element(
                parent=statistics_element,
                name="result",
                attributes=result['attr'],
                child_elements=result['items'],
                )

    def get_report(self):
        """Return the XML DOM report object."""
        return self.doc

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, encoding="utf-8")
        f.close()

class ReportReader(object):
    """
    Read the contents of a XML DOM (Document Object Model) of the
    analysis settings and results.

    This class can also export the XML DOM object to an XML document.

    Design Part: 1.49
    """

    def __init__(self, report = None):
        self.ns = "http://www.gimaris.com/setlyze/"
        self.doc = None

        if report:
            self.set_report(report)

    def set_report(self, report):
        """
        Set the XML DOM report object created by ReportGenerator.

        Keyword arguments:
        report -    Can be either an XML DOM report object created by
                    setlyze.std.ReportGenerator, or the path to an
                    XML report file.
        """
        if isinstance(report, xml.dom.minidom.Document):
            self.doc = report
        elif isinstance(report, str) and os.path.isfile(report):
            self.doc = xml.dom.minidom.parse(report)
        else:
            logging.error("set_report: attribute 'report' must be either an XML DOM report or the path to an XML file containing a report.")
            sys.exit(1)

        # Check if the report contains a 'report' element.
        if not self.doc.childNodes[0].localName == "report":
            logging.error("set_report: the XML DOM object is missing a setlyze report.")
            sys.exit(1)

    def get_element(self, parent, name):
        """Return the element object from a parent element."""
        element = None
        for e in parent.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == name:
                element = e
                break
        return element

    def get_report_elements(self):
        """
        Return all the XML elements the top 'report' element contains.

        Use this as a quick way to find out which elements are present
        in a XML DOM report object.
        """
        report_elements = []
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE:
                report_elements.append(e.localName)
        return report_elements

    def get_analysis_name(self):
        """
        Return the content of the 'analysis' element. This element
        contains the name of the analysis.

        The value of the 'analysis' element is used for the report
        header.
        """
        analysis_name = None

        # Find the 'specie_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "analysis":
                # Found the 'specie_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                analysis_name = e.childNodes[0].nodeValue.strip()
                break

        return analysis_name

    def get_locations_selection(self, slot=0):
        """
        Return the user selected locations for the specified slot from
        the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.

        Keyword arguments:
        slot -  The slot from which to get the locations selection from.
                There are two slots, so 0 and 1 are allowed slots.
        """
        locations_selection = None

        # Find the 'location_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "location_selections":
                # Found the 'location_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE and \
                            e2.localName == "selection" and \
                            e2.getAttribute("slot") == str(slot):
                        locations_selection = e2
                        break

        # Check if the locations 'selection' node was found.
        if not locations_selection:
            yield None
            return

        # Return each location from the 'locations_selection' node.
        for e in locations_selection.childNodes:
            location = {}
            if e.nodeType == e.ELEMENT_NODE and e.localName == "location":
                # Save each 'location' element to the location
                # dictionary as: location[node_name] = node_value
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        location[e2.localName] = e2.childNodes[0].nodeValue.strip()

            yield location

    def get_species_selection(self, slot=0):
        """
        Return the user selected species for the specified slot from the
        XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.

        Keyword arguments:
        slot -  The slot from which to get the locations selection from.
                There are two slots, so 0 and 1 are allowed slots.
        """
        species_selection = None

        # Find the 'specie_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "specie_selections":
                # Found the 'specie_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE and \
                            e2.localName == "selection" and \
                            e2.getAttribute("slot") == str(slot):
                        species_selection = e2
                        break

        # Check if the species 'selection' node was found.
        if not species_selection:
            yield None
            return

        # Return each specie from the 'species_selection' node.
        for e in species_selection.childNodes:
            specie = {}
            if e.nodeType == e.ELEMENT_NODE and e.localName == "specie":
                # Save each 'specie' element to the specie
                # dictionary as: specie[node_name] = node_value
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        specie[e2.localName] = e2.childNodes[0].nodeValue.strip()

            yield specie

    def get_spot_distances_observed(self):
        """Return the observed spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.
        """

        # Find the 'spot_distances_observed' node in the XML DOM object.
        spot_distances_observed = self.get_element(self.doc, "spot_distances_observed")

        # Check if the 'spot_distances_observed' node was found.
        if not spot_distances_observed:
            return

        # Return each distance from the 'spot_distances_observed' node.
        for e in spot_distances_observed.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "distance":
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_spot_distances_expected(self):
        """
        Return the expected spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.
        """

        # Find the 'spot_distances_expected' node in the XML DOM object.
        spot_distances_expected = self.get_element(self.doc, "spot_distances_expected")

        # Check if the 'spot_distances_expected' node was found.
        if not spot_distances_expected:
            return

        # Return each distance from the 'spot_distances_expected' node.
        for e in spot_distances_expected.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "distance":
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_plate_areas_definition(self):
        """
        Return the spot areas definition from the XML DOM report.
        """

        # Find the 'spots_definition' node in the XML DOM object.
        areas_definition = self.get_element(self.doc, "plate_areas_definition")

        # Check if the 'spots_definition' node was found.
        if not areas_definition:
            return

        # Fill this dictionary with the spots definition.
        definition = {}

        # Return each area from the 'spots_definition' node.
        for e in areas_definition.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                # Add each area to the 'definition' dictionary.
                area_id = e.getAttribute("id")
                if not area_id in definition:
                    definition[area_id] = []

                # Now put each spot from that area in the definition.
                for e2 in e.childNodes:
                    definition[area_id].append( e2.childNodes[0].nodeValue.strip() )

        return definition

    def get_area_totals_observed(self):
        """
        Return the observed specie totals per area from the XML DOM report.
        """

        # Find the 'area_totals_observed' node in the XML DOM object.
        area_totals = self.get_element(self.doc, "area_totals_observed")

        # Check if the 'area_totals_observed' node was found.
        if not area_totals:
            return

        # Add each area total to the 'totals' dictionary.
        totals = {}
        for e in area_totals.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                area_id = e.getAttribute("id")

                totals[area_id] = e.childNodes[0].nodeValue.strip()

        return totals

    def get_area_totals_expected(self):
        """
        Return the expected specie totals per area from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.
        """

        # Find the 'area_totals_expected' node in the XML DOM object.
        area_totals = self.get_element(self.doc, "area_totals_expected")

        # Check if the 'area_totals_expected' node was found.
        if not area_totals:
            return

        # Add each area total to the 'totals' dictionary.
        totals = {}
        for e in area_totals.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                area_id = e.getAttribute("id")

                totals[area_id] = e.childNodes[0].nodeValue.strip()

        return totals

    def get_statistics_significance(self):
        """Return the statistics from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.
        """

        # Find the 'statistics' node in the XML DOM object.
        statistics = self.get_element(self.doc, "statistics_significance")

        # Check if the 'spot_distances_observed' node was found.
        if not statistics:
            return

        # Return each distance from the 'spot_distances_observed' node.
        for result in statistics.childNodes:
            if result.nodeType == result.ELEMENT_NODE and result.localName == "result":
                attributes = {}
                items = {}

                # Get all attributes for this result element.
                for key in result.attributes.keys():
                    # Save each attribute to the attributes dictionary.
                    attributes[key] = result.getAttribute(key)

                # Get all sub elements for this result element.
                for e in result.childNodes:
                    if e.nodeType == e.ELEMENT_NODE:
                        # Save each item of the result element to the
                        # items dictionary.
                        items[e.localName] = e.childNodes[0].nodeValue.strip()

                # Return a tuple.
                yield (attributes,items)

    def get_statistics_normality(self):
        """Return the statistics from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator can be used in a for-loop.
        """

        # Find the 'statistics' node in the XML DOM object.
        statistics = self.get_element(self.doc, "statistics_normality")

        # Check if the 'spot_distances_observed' node was found.
        if not statistics:
            return

        # Return each distance from the 'spot_distances_observed' node.
        for result in statistics.childNodes:
            if result.nodeType == result.ELEMENT_NODE and result.localName == "result":
                attributes = {}
                items = {}

                # Get all attributes for this result element.
                for key in result.attributes.keys():
                    # Save each attribute to the attributes dictionary.
                    attributes[key] = result.getAttribute(key)

                # Get all sub elements for this result element.
                for e in result.childNodes:
                    if e.nodeType == e.ELEMENT_NODE:
                        # Save each item of the result element to the
                        # items dictionary.
                        items[e.localName] = e.childNodes[0].nodeValue.strip()

                # Return a tuple.
                yield (attributes,items)

    def save_report(self, path, type):
        """Save the XML DOM report to a file.

        The following file types are supported:
        * XML: A regular XML file.

        Design Part: 1.17
        """

        # Based on the type, decide in which file type to save the
        # report.
        if "xml" in type:
            # Add the extension if it's missing from the filename.
            if not path.endswith(".xml"):
                path += ".xml"

            # Save report.
            self.export_xml(path)
            logging.info("Analysis report saved to %s" % path)

    def get_xml(self):
        """Return the XML source for the XML DOM report."""
        return self.doc.toprettyxml(encoding="utf-8")

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, addindent="\t", newl="\n", encoding="utf-8")
        f.close()

# Register the Sender class as an official GType.
gobject.type_register(Sender)

# Create a sender object which will send all the application signals.
sender = Sender()
