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

"""This module provides functions for generating analysis reports."""

import os
import logging
import xml.dom.minidom
from sqlite3 import dbapi2 as sqlite

import setlyze.config
import setlyze.std

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/06"

def export(report, path, type, elements=None):
    """Save the data from a :class:`Report` object `reader` to a data file.

    The file is saved to `path` in a format specified by `type`. Possible
    values for `type` are ``xml``, ``txt`` or ``latex``. The report elements
    to be exported are specified by `elements`.

    .. todo::
       Make this work with the new report model.

    Design Part: 1.17
    """

    # Based on the type, decide in which file type to save the
    # report.
    if type == 'xml':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".xml"):
            path += ".xml"
        dom_report = DOMReport(report)
        dom_report.export_xml(path, elements)

    elif type == 'txt':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".txt"):
            path += ".txt"
        exporter = ExportTextReport(report)
        exporter.export(path, elements)

    elif type == 'latex':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".tex") and not path.endswith(".latex"):
            path += ".tex"
        exporter = ExportLatexReport(report)
        exporter.export(path, elements)

    else:
        raise ValueError("Unsupported file type specified.")

    logging.info("Analysis report saved to %s" % path)

class Report(object):
    """Create a report object.

    The results for an analysis are saved to an instance of this class using
    the set methods. An instance of this class is passed to an instance of
    :class:`setlyze.gui.Report` to display the results graphically.
    """

    def __init__(self):
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.statistics = {}

    def set_analysis(self, name):
        """Set the analysis name to `name`."""
        self.analysis_name = name

    def set_location_selections(self, selections):
        """Set the locations selections.

        This element will be filled with the locations selections `selections`,
        a list with location ID lists (e.g. [[1,2], ..., [3]]).

        The selections will be saved as follows: ::

            self.locations_selections = [
                {
                    1: {'nr':100, 'name':"Location A"},
                    2: {'nr':200, 'name':"Location B"},
                },
                ...
                {
                    3: {'nr':300, 'name':"Location C"},
                }
            ]
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        self.locations_selections = []
        for selection in selections:
            if not isinstance(selection, (list, tuple)):
                continue

            # Fetch all information about the locations selection.
            selection_str = ",".join([str(id) for id in selection])
            cursor.execute( "SELECT loc_id,loc_nr,loc_name "
                            "FROM localities "
                            "WHERE loc_id IN (%s)" %
                            (selection_str)
                            )

            # Create a dictionary for the selection.
            selection_dict = {}
            for loc_id,loc_nr,loc_name in cursor:
                selection_dict[loc_id] = {'nr':loc_nr, 'name':loc_name}

            # Add the selection to the main variable.
            self.locations_selections.append(selection_dict)

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_species_selections(self, selections):
        """Set the species selections.

        This element will be filled with the species selections `selections`,
        a list with location ID lists (e.g. [[1,2], ..., [3]]).

        The selections will be saved as follows: ::

            self.species_selections = [
                {
                    1: {'name_latin':"Ectopleura larynx", 'name_common':"Gorgelpijp"},
                    2: {'name_latin':"Metridium senile", 'name_common':"Zeeanjelier"},
                },
                ...
                {
                    3: {'name_latin':"Balanus improvisus", 'name_common':"Brakwaterpok"},
                }
            ]
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        self.species_selections = []
        for selection in selections:
            if not isinstance(selection, (list, tuple, int)):
                continue

            # Allow an integer to be passed, meaning that just one species was
            # selected. But we have to put it in a list in order to work with
            # it.
            if isinstance(selection, int):
                selection = [selection]

            # Fetch all information about the locations selection.
            selection_str = ",".join([str(id) for id in selection])
            cursor.execute( "SELECT spe_id,spe_name_latin,spe_name_venacular "
                            "FROM species "
                            "WHERE spe_id IN (%s)" %
                            (selection_str)
                            )

            # Create a dictionary for the selection.
            selection_dict = {}
            for spe_id,name_latin,name_common in cursor:
                selection_dict[spe_id] = {'name_latin':name_latin, 'name_common':name_common}

            # Add the selection to the main variable.
            self.species_selections.append(selection_dict)

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_observed(self):
        """Set the observed spot distances.

        This element will be filled with the observed spot distances.

        The spot distances will be saved as follows ::

            self.spot_distances_observed = {
                63: [1.0, 2.0, ...],
                229: [3.16, ...],
                ...
            }

        Where the dictionary keys are plate numbers and the values are lists
        with distances for the corresponding plates.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the observed distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_observed"
                        )

        # Populate the main variable.
        self.spot_distances_observed = {}
        for pla_id,distance in cursor:
            if pla_id in self.spot_distances_observed:
                self.spot_distances_observed[pla_id].append(distance)
            else:
                self.spot_distances_observed[pla_id] = [distance]

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_expected(self):
        """Set the expected spot distances.

        This element will be filled with the expected spot distances.

        The spot distances will be saved as follows ::

            self.spot_distances_expected = {
                63: [1.0, 3.16, ...],
                229: [4.47, ...],
                ...
            }

        Where the dictionary keys are plate numbers and the values are lists
        with distances for the corresponding plates.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the expected distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_expected"
                        )

        # Populate the main variable.
        self.spot_distances_expected = {}
        for pla_id,distance in cursor:
            if pla_id in self.spot_distances_expected:
                self.spot_distances_expected[pla_id].append(distance)
            else:
                self.spot_distances_expected[pla_id] = [distance]

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_plate_areas_definition(self, definition):
        """Set the plate areas definition `definition`.

        Examples of `definition` ::

            {
                'area1': ['A'],
                'area2': ['B'],
                'area3': ['C'],
                'area3': ['D']
            }

            {
                'area1': ['A'],
                'area2': ['B'],
                'area3': ['C', 'D']
            }
        """
        self.plate_areas_definition = definition

    def set_area_totals_observed(self, totals):
        """Set the observed plate area totals.


        Examples of `totals` ::

            {
                'area1': 261,
                'area2': 943,
                'area3': 2837,
                'area4': 1858,
            }

            {
                'area1': 261,
                'area2': 943,
                'area3': 2837,
            }
        """
        self.area_totals_observed = totals

    def set_area_totals_expected(self, totals):
        """Set the expected plate area totals.


        Examples of `totals` ::

            {
                'area1': 235.96,
                'area2': 943.84,
                'area3': 2831.52,
                'area4': 1887.68,
            }

            {
                'area1': 235.96,
                'area2': 943.84,
                'area3': 2831.52,
            }
        """
        self.area_totals_expected = totals

    def set_statistics(self, name, data):
        """Set statistics results `data` under key `name`.

        This method is used to save results from statistical tests. The results
        must be supplied with the `data` argument. The `data` argument is a
        list containing dictionaries in the format
        {'attr': {'<name>': <value>, ...}, 'results': {'<name>': <value>, ...}}
        where the value for 'attr' is a dictionary with the attributes for the
        test and 'results' is a dictionary with elements of the results.

        Examples of `data` ::

            {
                'attr': {
                    'method': "Chi-squared test for given probabilities"
                },
                'results': {
                    'df': 3.0,
                    'p_value': 0.37,
                    'chi_squared': 3.13
                }
            }

            {
                'attr': {
                    'method': "Chi-squared test for given probabilities",
                    'groups': "ratios",
                },
                'results': {
                    1: {
                        'n_plates': 2,
                        'n_distances': 56,
                        'df': 14.0,
                        'p_value': 0.90,
                        'chi_squared': 7.75,
                        'mean_expected': 2.77,
                        'mean_observed': 2.50
                    },
                    ...
                }
            }

            {
                'attr': {
                    'method': "Wilcoxon rank sum test with continuity correction",
                    'alternative': "two.sided",
                    'conf_level': 0.95,
                    'paired': False,
                    'groups': "areas",
                },
                'results': {
                    'A': {'p_value': 0.67, 'mean_expected': 1.33, 'mean_observed': 1.35},
                    'B': {'p_value': 0.97, 'mean_expected': 4.08, 'mean_observed': 4.07},
                    'A+B': {'p_value': 0.97, 'mean_expected': 2.70, 'mean_observed': 2.71},
                    ...
                }
            }

        Of repeated tests ::

            {
                'attr': {
                    'method': "Wilcoxon rank sum test with continuity correction",
                    'groups': "areas",
                    'alpha_level': 0.05,
                    'repeats': 10,
                },
                'results': {
                    'A': {'n_significant': 10, 'n_preference': 10, 'n_rejection': 0},
                    'B': {'n_significant': 1, 'n_preference': 0, 'n_rejection': 1},
                    'A+B': {'n_significant': 9, 'n_preference': 9, 'n_rejection': 0},
                    ...
                }
            }

            {
                'attr': {
                    'method': "Wilcoxon rank sum test with continuity correction",
                    'groups': "spots|ratios",
                    'alpha_level': 0.05,
                    'repeats': 10,
                },
                'results': {
                    2: {'n_significant': 10, 'n_attraction': 10, 'n_repulsion': 0},
                    3: {'n_significant': 1, 'n_attraction': 0, 'n_repulsion': 1},
                    ...
                }
            }
        """
        if not data['attr']:
            return
        if name in self.statistics:
            self.statistics[name].append(data)
        else:
            self.statistics[name] = [data]

class DOMReport(object):
    """Create an XML DOM object from a :class:`Report` object.

    The DOM can be exported to an XML file.

    .. todo::
       Make this work with the new report model.

    Design Part: 1.48
    """

    def __init__(self):
        self.ns = "http://www.gimaris.com/setlyze/xmlns/"
        self.dbfile = setlyze.config.cfg.get('db-file')

        # Create a new XML DOM object (Design Part: 2.17).
        self.doc = xml.dom.minidom.Document()
        # Create the top report element.
        self.report = self.doc.createElementNS(self.ns, "setlyze:report")
        # Manually add the namespace to the top element.
        self.report.setAttribute("xmlns:setlyze", self.ns)
        self.doc.appendChild(self.report)

    def create_element(self, parent, name, child_elements={}, attributes={}, text=None):
        """Add a new child element with name `name` to the element
        `parent` for the XML DOM object.

        Usually you'll start by adding child elements to the
        root element ``self.report``. In this case `parent` would be
        ``self.report``. It's then possible to add child elements for
        for those by setting `parent` to the newly created child
        elements.

        Optionally you can easily add child elements by setting
        `child_elements` to a dictionary. The dictionary keys will be
        the names of the child elements, and the corresponding
        dictionary values will be the values for the elements.

        This method also allows you to easily add attributes. To add
        attributes, set `attributes` to a dictionary. The dictionary
        keys will be the names of attributes, and the corresponding
        dictionary values will be the values for the attributes.

        The `text` argument gives the element a value. The value of
        `text` can be anything.

        This method returns the newly created element. This allows you
        to set the returned element object as the parent element
        for other elements.

        We shall clarify with some usage examples. First we add an
        empty child element to the root element: ::

            location_selections_element = self.create_element(
                parent=self.report,
                name="location_selections"
                )

        Then we add some child elements to the just created element: ::

            self.create_element(
                parent=location_selections_element,
                name="location",
                child_elements={'nr':1, 'name':"Aquadome, Grevelingen"},
                attributes={'id':1}
                )

            self.create_element(
                parent=location_selections_element,
                name="location",
                child_elements={'nr':2, 'name':"Colijnsplaat, floating dock, Oosterschelde"},
                attributes={'id':2}
                )

        Would this be exported to an XML file, the contents of the file
        would look like this: ::

            <?xml version="1.0" encoding="utf-8"?>
            <setlyze:report xmlns:setlyze="http://www.gimaris.com/setlyze/">
                <location_selections>
                    <location id="1">
                        <nr>
                            1
                        </nr>
                        <name>
                            Aquadome, Grevelingen
                        </name>
                    </location>
                    <location id="2">
                        <nr>
                            2
                        </nr>
                        <name>
                            Colijnsplaat, floating dock, Oosterschelde
                        </name>
                    </location>
                </location_selections>
            </setlyze:report>
        """

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

    def get_element(self, parent, name):
        """Return the element object with name `name` from a parent
        element `parent`.
        """
        element = None
        for e in parent.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == name:
                element = e
                break
        return element

    def set_analysis(self, name):
        """Add the element ``analysis`` with value `name` to the XML DOM
        report.

        This element describes to which analysis this report belongs. So
        `name` is just a string with the title of an analysis.

        Design Part: 1.72
        """
        self.create_element(parent=self.report, name="analysis", text=name)

    def set_location_selections(self, selections):
        """Add the element ``location_selections`` to the XML DOM
        report.

        This element will be filled with the location selections `selections`,
        a list with location ID lists (e.g. [[1,2,3], ..., [5,6,7]]).

        The XML representation looks like this: ::

            <location_selections>
                <selection slot="0">
                    <location id="1">
                        <nr>
                            1
                        </nr>
                        <name>
                            Aquadome, Grevelingen
                        </name>
                    </location>
                </selection>
                <selection slot="1">
                    <location id="2">
                        <nr>
                            2
                        </nr>
                        <name>
                            Colijnsplaat, floating dock, Oosterschelde
                        </name>
                    </location>
                </selection>
            </location_selections>

        Design Part: 1.50
        """

        # Create a new element to save the location selections in.
        location_selections = self.create_element(
            parent=self.report,
            name='location_selections'
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for i, loc_ids in selections.enumerate():
            if not isinstance(loc_ids, (list, tuple)):
                continue

            # Create a 'locations_selection' child element for each
            # selection. We give each selection element a 'slot' attribute.
            loc_selection_element = self.create_element(
                parent=location_selections,
                name="selection",
                attributes={'slot': i}
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

    def set_species_selections(self, selections):
        """Add the element ``species_selections`` to the XML DOM
        report.

        This element will be filled with the species selections `selections`,
        a list with species ID lists (e.g. [[1,2,3], ..., [5,6,7]]).

        The XML representation looks like this: ::

            <species_selections>
                <selection slot="0">
                    <species id="2">
                        <name_latin>
                            Ectopleura larynx
                        </name_latin>
                        <name_venacular>
                            Gorgelpijp
                        </name_venacular>
                    </species>
                </selection>
                <selection slot="1">
                    <species id="6">
                        <name_latin>
                            Metridium senile
                        </name_latin>
                        <name_venacular>
                            Zeeanjelier
                        </name_venacular>
                    </species>
                </selection>
            </species_selections>

        Design Part: 1.51
        """

        # Create a new element to save the species selections in.
        species_selections = self.create_element(
            parent=self.report,
            name="species_selections"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for i, spe_ids in selections.enumerate():
            if not isinstance(spe_ids, (list, tuple)):
                continue

            # Create a 'species_selection' child element for each
            # selection. We give each selection element a 'slot'
            # attribute.
            spe_selection_element = self.create_element(
                parent=species_selections,
                name="selection",
                attributes={'slot': i}
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
                    name="species",
                    child_elements={'name_venacular': row[1],'name_latin': row[2]},
                    attributes={'id':row[0]}
                    )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_observed(self):
        """Add the element ``spot_distances_observed`` to the XML DOM
        report.

        This element will be filled with the observed spot distances.

        The XML representation looks like this: ::

            <spot_distances_observed>
                <distance plate_id="63">
                    1.0
                </distance>
                <distance plate_id="63">
                    2.0
                </distance>
                <distance plate_id="229">
                    3.16
                </distance>
            </spot_distances_observed>

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
        """Add the element ``spot_distances_expected`` to the XML DOM
        report.

        This element will be filled with the expected spot distances.

        The XML representation looks like this: ::

            <spot_distances_expected>
                <distance plate_id="62">
                    1.0
                </distance>
                <distance plate_id="62">
                    3.16
                </distance>
                <distance plate_id="228">
                    4.47
                </distance>
            </spot_distances_expected>

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

    def set_plate_areas_definition(self, definition):
        """Add the element ``plate_areas_definition`` to the XML DOM
        report.

        This element will be filled with the user defined spot areas
        definition `definition`.

        The XML representation looks like this: ::

            <plate_areas_definition>
                <area id="area1">
                    <spot>
                        A
                    </spot>
                </area>
                <area id="area2">
                    <spot>
                        B
                    </spot>
                </area>
                <area id="area3">
                    <spot>
                        C
                    </spot>
                    <spot>
                        D
                    </spot>
                </area>
            </plate_areas_definition>

        Design Part: 1.54
        """
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
        """Add the element ``area_totals_observed`` to the XML DOM
        report.

        This element will be filled with the observed species totals per
        plate area.

        The XML representation looks like this: ::

            <area_totals_observed>
                <area id="area1">
                    27
                </area>
                <area id="area2">
                    75
                </area>
                <area id="area3">
                    52
                </area>
            </area_totals_observed>

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
        """Add the element ``area_totals_expected`` to the XML DOM
        report.

        This element will be filled with the expected species totals per
        plate area.

        The XML representation looks like this: ::

            <area_totals_expected>
                <area id="area1">
                    24.64
                </area>
                <area id="area2">
                    73.92
                </area>
                <area id="area3">
                    55.44
                </area>
            </area_totals_expected>

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

    def set_statistics(self, name, data):
        """Add the element ``statistics`` with child element
        ``name`` to the XML DOM report.

        This element will be filled with the results of the performed
        statistical tests. The results must be supplied with the
        `data` argument. The `data` argument is a list containing
        dictionaries in the format {'attr': {'<name>': <value>, ...},
        'results': {'<name>': <value>, ...}} where the value for 'attr' is
        a dictionary with the attributes and 'results' is a dictionary
        with child elements for the ``statistics`` element.

        An XML representation: ::

            <statistics>
                <wilcoxon alternative="two.sided" conf_level="0.95" method="Wilcoxon rank sum test with continuity correction" n="3" n_plates="1" n_positive_spots="3" paired="False">
                    <conf_int_start>
                        -2.16
                    </conf_int_start>
                    <p_value>
                        0.353678517318
                    </p_value>
                    <mean_expected>
                        2.13333333333
                    </mean_expected>
                    <conf_int_end>
                        1.0
                    </conf_int_end>
                    <mean_observed>
                        1.33333333333
                    </mean_observed>
                </wilcoxon>
            </statistics>

        Design Part: 1.70
        """

        # Create the 'statistics' element if it doesn't exist.
        statistics_element = self.get_element(self.report, 'statistics')
        if not statistics_element:
            statistics_element = self.create_element(
                parent=self.report,
                name='statistics'
                )

        for x in data:
            self.create_element(
                parent=statistics_element,
                name=name,
                attributes=x['attr'],
                child_elements=x['results'],
                )

    def set_statistics_repeats(self, name, results):
        """Add the element "significance_test_repeats_areas" to the XML DOM
        report.

        This element will be filled with the number of significant results
        per plate area group.

        The XML representation looks like this: ::

            <wilcoxon_areas_repeats alpha_level="0.05" repeats="100">
                <result plate_area="A">
                    <n_preference>
                        100
                    </n_preference>
                    <n_rejection>
                        0
                    </n_rejection>
                    <n_significant>
                        100
                    </n_significant>
                </result>
                <plate_area id="B+C+D">
                    <n_preference>
                        0
                    </n_preference>
                    <n_rejection>
                        100
                    </n_rejection>
                    <n_significant>
                        100
                    </n_significant>
                </plate_area>
            </significance_test_repeats_areas>

        Design Part: 1.71
        """

        # Make sure the testid is valid.
        valid_names = ('wilcoxon_areas','wilcoxon_spots','wilcoxon_ratios')
        if name not in valid_names:
            raise ValueError("Possible values for 'name' are %s. You gave '%s'." %
                (", ".join(testids), name))

        # Decide which attribute name to use for 'result' elements.
        if 'areas' in name:
            group_attribute = 'plate_area'
        elif 'spots' in name:
            group_attribute = 'n_spots'
        elif 'ratios' in name:
            group_attribute = 'ratio_group'

        # Create a new child element for the report.
        repeats_element = self.create_element(
            parent=self.report,
            name="%s_repeats" % (name),
            attributes={'repeats': setlyze.config.cfg.get('test-repeats'),
                'alpha_level': setlyze.config.cfg.get('alpha-level')},
            )

        for group_attribute_value, items in results.iteritems():
            result_element = self.create_element(parent=repeats_element,
                name='result',
                attributes={group_attribute: group_attribute_value},
                )

            for name, value in items.iteritems():
                self.create_element(parent=result_element,
                    name=name,
                    text=value,
                    )

    def get_report(self):
        """Return the XML DOM report object."""
        return self.doc

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, encoding="utf-8")
        f.close()

class DOMReportConvert(object):
    """Convert a :class:`DOMReport` report to a :class:`Report` report.

    .. todo::
       Make this work with the new report model.

    Design Part: 1.49
    """

    def __init__(self, report = None):
        self.ns = "http://www.gimaris.com/setlyze/xmlns/"
        self.doc = None

        if report:
            self.set_report(report)

    def set_report(self, report):
        """Set the XML DOM report object `report` generated by
        :class:`ReportGenerator`. `report` can also be the path to an
        XML file containing an analysis report.
        """
        if isinstance(report, xml.dom.minidom.Document):
            # 'report' is an XML DOM object.
            self.doc = report
        elif isinstance(report, str) and os.path.isfile(report):
            # 'report' is path to an XML file. So parse its contents.
            self.doc = xml.dom.minidom.parse(report)
        else:
            raise ValueError("Argument 'report' must be either a XML "
                "DOM object or the path to an XML file containing "
                "analysis data.")

        # Check if the report contains a 'report' element.
        if not self.doc.childNodes[0].localName == "report":
            raise ValueError("The XML DOM object is missing a setlyze report.")

    def get_element(self, parent, name):
        """Return the element object with name `name` from a parent
        element `parent`.
        """
        element = None
        for e in parent.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == name:
                element = e
                break
        return element

    def get_child_names(self, parent=None):
        """Return a list with all child element names from the XML DOM
        object. The child elements for the report elements are excluded.

        Use this as a quick way to find out which elements are present
        in a XML DOM report object.
        """
        report_elements = []
        if parent:
            for e in parent.childNodes:
                if e.nodeType == e.ELEMENT_NODE:
                    report_elements.append(e.localName)
        else:
            for e in self.doc.childNodes[0].childNodes:
                if e.nodeType == e.ELEMENT_NODE:
                    report_elements.append(e.localName)
        return setlyze.std.uniqify(report_elements)

    def get_analysis_name(self):
        """Return the value of the `analysis` element. This element
        contains the name of the analysis.
        """
        analysis_name = None

        # Find the 'species_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == 'analysis':
                # Found the 'species_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                analysis_name = e.childNodes[0].nodeValue.strip()
                break

        return analysis_name

    def get_locations_selection(self, slot=0):
        """Return the locations selection from the selection slot with
        number `slot` from the XML DOM report. Possible values for
        `slot` are ``0`` and ``1``.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns dictionaries in the format
        ``{'nr': <value>, 'name': <value>}``.

        Usage example: ::

            locations_selection = reader.get_locations_selection(slot=0)
            for loc in locations_selection:
                print loc['nr'], loc['name']
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

        # Check if the 'selection' element was found. If not, yield
        # None and exit.
        if not locations_selection:
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
        """Return the species selection from the selection slot with
        number `slot` from the XML DOM report. Possible values for
        `slot` are ``0`` and ``1``.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns dictionaries in the format
        ``{'name_latin': <value>, 'name_venacular': <value>}``.

        Usage example: ::

            species_selection = reader.get_species_selection(slot=0)
            for spe in species_selection:
                print spe['name_latin'], spe['name_venacular']
        """
        species_selection = None

        # Find the 'species_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "species_selections":
                # Found the 'species_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE and \
                            e2.localName == "selection" and \
                            e2.getAttribute("slot") == str(slot):
                        species_selection = e2
                        break

        # Check if the 'selection' element was found. If not, yield
        # None and exit.
        if not species_selection:
            return

        # Return each species from the 'species_selection' node.
        for e in species_selection.childNodes:
            species = {}
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'species':
                # Save each 'species' element to the species
                # dictionary as: species[node_name] = node_value
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        species[e2.localName] = e2.childNodes[0].nodeValue.strip()

            yield species

    def get_spot_distances_observed(self):
        """Return the observed spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. The iterator returns the distances.

        Usage example: ::

            observed_distances = reader.get_spot_distances_observed()
            for dist in observed_distances:
                print dist
        """

        # Find the 'spot_distances_observed' node in the XML DOM object.
        spot_distances_observed = self.get_element(self.doc, 'spot_distances_observed')

        # Check if the 'spot_distances_observed' node was found.
        if not spot_distances_observed:
            return

        # Return each distance from the 'spot_distances_observed' node.
        for e in spot_distances_observed.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'distance':
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_spot_distances_expected(self):
        """Return the expected spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. The iterator returns the distances.

        Usage example: ::

            expected_distances = reader.get_spot_distances_expected()
            for dist in expected_distances:
                print dist
        """

        # Find the 'spot_distances_expected' node in the XML DOM object.
        spot_distances_expected = self.get_element(self.doc, 'spot_distances_expected')

        # Check if the 'spot_distances_expected' node was found.
        if not spot_distances_expected:
            return

        # Return each distance from the 'spot_distances_expected' node.
        for e in spot_distances_expected.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'distance':
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_plate_areas_definition(self):
        """Return the spot areas definition from the XML DOM report.
        This method returns a dictionary. For example: ::

            {
            'area1': ['A'],
            'area2': ['B'],
            'area3': ['C', 'D']
            }

        or: ::

            {
            'area1': ['A'],
            'area2': ['B'],
            'area3': ['C'],
            'area4': ['D']
            }
        """

        # Find the 'spots_definition' node in the XML DOM object.
        areas_definition = self.get_element(self.doc, 'plate_areas_definition')

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
        """Return the observed species totals per plate area from the
        XML DOM report.

        This method returns a dictionary. For example: ::

            {
            'area1': 24.64,
            'area2': 73.92,
            'area3': 55.44
            }
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
        """Return the expected species totals per area from the XML DOM
        report.

        This method returns a dictionary. For example: ::

            {
            'area1': 23.12,
            'area2': 60.10,
            'area3': 40.44
            }
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

    def get_statistics(self, element_name):
        """Return the statistics elements with name `name` from the
        XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns tuples in the format
        ``({'<name>': <value>, ...}, {'<name>': <value>, ...})`` where
        the first dictionary contains the attributes and the second
        the results.
        """

        # Find the 'statistics' element in the XML DOM object.
        statistics = self.get_element(self.doc, 'statistics')

        # Check if the 'statistics' element was returned.
        if not statistics:
            return

        # Return each element with name `name` from the 'statistics' node.
        for e in statistics.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == element_name:
                attributes = {}
                results = {}

                # Get all attributes for this result element.
                for key in e.attributes.keys():
                    # Save each attribute to the attributes dictionary.
                    attributes[key] = e.getAttribute(key)

                # Get all sub elements for this result element.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        # Save each item of the result element to the
                        # items dictionary.
                        results[e2.localName] = e2.childNodes[0].nodeValue.strip()

                # Return a tuple.
                yield (attributes,results)

    def get_statistics_repeats(self, element_name):
        """Return the repeated statistical test results for `element_name`
        from the XML DOM report. `element_name` is the element name of the
        non-repeated variant. Possible values for `element_name` are
        "wilcoxon_areas", "wilcoxon_spots", "wilcoxon_ratios",
        "chi_squared_areas", "chi_squared_spots" and "chi_squared_ratios".

        This method returns a dictionary. For example: ::

            {
                'A': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0},
                'B': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'C': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'D': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'A+B': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'repeats': 100,
            }
        """

        # Find the 'element_name_repeats' node in the XML DOM object.
        element_name = '%s_repeats' % element_name
        repeats_element = self.get_element(self.doc, element_name)

        # Check if the 'element_name_repeats' node was found.
        if not repeats_element:
            return

        # Decide which attribute name to use for 'result' elements.
        if 'areas' in element_name:
            group_attribute = 'plate_area'
        elif 'spots' in element_name:
            group_attribute = 'n_spots'
        elif 'ratios' in element_name:
            group_attribute = 'ratio_group'

        # Add the results to the 'results' dictionary.
        results = {}
        for e in repeats_element.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'result':
                group_attribute_value = e.getAttribute(group_attribute)

                # Create a dictionary for this plate area.
                results[group_attribute_value] = {}

                # Get all sub elements for 'result'.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        results[group_attribute_value][e2.localName] = e2.childNodes[0].nodeValue.strip()

        # Add the number of repeats to the 'results' dict as well.
        results['repeats'] = repeats_element.getAttribute('repeats')

        return results

    def get_xml(self):
        """Return the XML source for the XML DOM report."""
        return self.doc.toprettyxml(encoding="utf-8")

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, addindent="\t", newl="\n", encoding="utf-8")
        f.close()

class ExportLatexReport(object):
    """Generate an analysis report in LaTeX format.

    .. todo::
       Complete this class.
    """

    def __init__(self, reader = None):
        self.set_report_reader(reader)

    def set_report_reader(self, reader):
        """Set the report reader."""
        self.reader = reader

    def generate(self, elements=None):
        pass

    def export(self, path, elements=None):
        pass

class ExportTextReport(object):
    """Generate an analysis report in text format.

    .. todo::
       Make this work with the new report model.
    """

    def __init__(self, reader = None):
        self.set_report_reader(reader)

    def set_report_reader(self, reader):
        """Set the report reader."""
        self.reader = reader

    def part(self, header):
        """Return `header` marked up as a header for parts in
        reStructuredText format.
        """
        text = "<hr>\n<h>\n<hr>\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "="*len(header))
        return text

    def chapter(self, header):
        """Return `header` marked up as a header for parts in
        reStructuredText format.
        """
        text = "<hr>\n<h>\n<hr>\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "*"*len(header))
        return text

    def section(self, header):
        """Return `header` marked up as a header for sections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "#"*len(header))
        return text

    def subsection(self, header):
        """Return `header` marked up as a header for subsections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "="*len(header))
        return text

    def subsubsection(self, header):
        """Return `header` marked up as a header for subsubsections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "^"*len(header))
        return text

    def table(self, headers):
        """Return a table header with column names from `headers` in
        reStructuredText format.

        `headers` is a list of strings representing the column names.
        """
        header = ""
        header_lengths = []
        header_placeholders = []
        row_placeholders = []
        predefined_lengths = {"df": 6,
            "Remarks": 40,
            "W": 6,
            }
        predefined_fields = {"Plate Area": "%%-%ds",
            "Area ID": "%%-%ds",
            "P-value": "%%%d.4f",
            "Chi squared": "%%%d.4f",
            "Plate Area": "%%-%ds",
            "Plate Area Surfaces": "%%-%ds",
            "Mean Observed": "%%%d.4f",
            "Mean Expected": "%%%d.4f",
            "Remarks": "%%-%ds",
            }

        # Generate a placeholder strings for the column names and the fields.
        for name in headers:
            if name not in predefined_lengths:
                length = len(name)
            else:
                length = predefined_lengths[name]

            # Save the lengths of all column names. This is needed for
            # generating the table rules.
            header_lengths.append(length)

            # Construct the placeholders for the column names.
            header_placeholders.append("%%-%ds" % length)

            # Construct the placeholders for the fields.
            if name not in predefined_fields:
                row_placeholders.append("%%%ds" % length)
            else:
                row_placeholders.append(predefined_fields[name] % length)

        # Generate top rule for table.
        header += self.table_rule(header_lengths)

        # Generate string with column names.
        header_placeholders = "  ".join(header_placeholders)
        header += header_placeholders % tuple(headers)
        header += "\n"

        # Generate rule below column names.
        header += self.table_rule(header_lengths)

        # Generate placeholder string for table rows.
        row_placeholders = "  ".join(row_placeholders)
        row_placeholders += "\n"

        # Generate rule for the end of the table.
        footer = self.table_rule(header_lengths)

        return (header,row_placeholders,footer)

    def table_rule(self, col_widths):
        """Return a rule for a table with column widths `col_widths`.

        `col_widths` is a list/tuple containing column widths (integers).
        """
        format = []
        for n in col_widths:
            format.append("="*n)
        return "  ".join(format) + "\n"

    def generate(self, elements=None):
        """Generate analysis report in text format."""

        # Get the child element names of the report root.
        report_elements = self.reader.get_child_names()

        # Add the child element names of the 'statistics' element to the
        # list of root element names.
        stats = self.reader.get_element(self.reader.doc, 'statistics')
        if stats:
            report_elements.extend(self.reader.get_child_names(stats))

        # If 'elements' argument was provided, create a new 'report_elements'
        # list containing only the elements that are present in both lists.
        report_elements_new = []
        if elements:
            for element in elements:
                for r_element in report_elements:
                    # Now check if string 'element' is part of string
                    # r_element. Note that they don't have to be exactly the
                    # same, e.g. if 'spot_distances' is present in 'elements',
                    # both 'spot_distances_observed' and
                    # 'spot_distances_expected' will be added to
                    # 'report_elements_new'.
                    if element in r_element:
                        report_elements_new.append(r_element)
            report_elements = report_elements_new

        # Write the header for the report which includes the analysis
        # name.
        header = "SETLyze Analysis Report - %s" % self.reader.get_analysis_name()
        yield self.part(header)

        # Add species selections.
        if 'species_selections' in report_elements:
            yield self.section("Locations and Species Selections")

            species_selection = self.reader.get_species_selection(slot=0)
            yield self.subsection("Species Selection [1]")
            for spe in species_selection:
                if not len(spe['name_latin']):
                    yield "* %s\n" % (spe['name_venacular'])
                elif not len(spe['name_venacular']):
                    yield "* %s\n" % (spe['name_latin'])
                else:
                    yield "* %s (%s)\n" % (spe['name_latin'], spe['name_venacular'])

            if len(list(self.reader.get_species_selection(slot=1))):
                species_selection = self.reader.get_species_selection(slot=1)
                yield self.subsection("Species Selection [2]")
                for spe in species_selection:
                    if not len(spe['name_latin']):
                        yield "* %s\n" % (spe['name_venacular'])
                    elif not len(spe['name_venacular']):
                        yield "* %s\n" % (spe['name_latin'])
                    else:
                        yield "* %s (%s)\n" % (spe['name_latin'], spe['name_venacular'])

        # Add locations selections.
        if 'location_selections' in report_elements:
            yield self.subsection("Locations selection [1]")
            locations_selection = self.reader.get_locations_selection(slot=0)
            for loc in locations_selection:
                yield "* %s\n" % loc['name']

            if len(list(self.reader.get_locations_selection(slot=1))):
                yield self.subsection("Locations selection [2]")
                locations_selection = self.reader.get_locations_selection(slot=1)
                for loc in locations_selection:
                    yield "* %s\n" % loc['name']

        # Add the spot distances.
        if 'spot_distances_observed' in report_elements and \
                'spot_distances_expected' in report_elements:
            yield self.section("Spot Distances")

            t_header, t_row, t_footer = self.table(["Observed","Expected"])

            yield t_header
            observed_distances = self.reader.get_spot_distances_observed()
            expected_distances = self.reader.get_spot_distances_expected()
            for dist_observed in observed_distances:
                yield t_row % (dist_observed, expected_distances.next())
            yield t_footer

        # Add the plate areas definition.
        if 'plate_areas_definition' in report_elements:
            yield self.section(setlyze.locale.text('t-plate-areas-definition'))

            t_header, t_row, t_footer = self.table(["Area ID","Plate Area Surfaces"])

            yield t_header
            spots_definition = self.reader.get_plate_areas_definition()
            for area_id, spots in sorted(spots_definition.iteritems()):
                spots = ", ".join(spots)
                yield t_row % (area_id, spots)
            yield t_footer

        # Add the species totals per plate area.
        if 'area_totals_observed' in report_elements and \
                'area_totals_expected' in report_elements:
            yield self.section(setlyze.locale.text('t-plate-area-totals'))

            t_header, t_row, t_footer = self.table(["Area ID","Observed Totals",
                "Expected Totals"])

            yield t_header
            totals_observed = self.reader.get_area_totals_observed()
            totals_expected = self.reader.get_area_totals_expected()
            for area_id in sorted(totals_observed):
                yield t_row % \
                    (area_id,
                    totals_observed[area_id],
                    totals_expected[area_id],
                    )
            yield t_footer

        # Add the results for the Chi-squared tests (areas).
        if 'chi_squared_areas' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(['P-value','Chi squared','df',
                'Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_areas')
            for attr,items in statistics:
                yield t_row % \
                    (float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    setlyze.std.make_remarks(items,attr),
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, areas).
        if 'wilcoxon_areas' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
                'n (observed species)', 'n (expected species)', 'P-value'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_areas')
            for attr,items in statistics:
                remarks = setlyze.std.make_remarks(items,attr)
                yield t_row % \
                    (attr['plate_area'],
                    int(attr['n']),
                    int(attr['n_sp_observed']),
                    int(attr['n_sp_expected']),
                    float(items['p_value']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Plate Area','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_areas')
            for attr,items in statistics:
                yield t_row % \
                    (attr['plate_area'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    setlyze.std.make_remarks(items,attr),
                    )
            yield t_footer

            # Add the results for the repeated Wilcoxon rank-sum tests.
            if 'wilcoxon_areas_repeats' in report_elements:
                yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

                t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
                    'n (observed species)','n (significant)',
                    'n (non-significant)'])

                yield t_header
                statistics = self.reader.get_statistics('wilcoxon_areas')
                statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_areas')
                for attr,items in statistics:
                    plate_area = attr['plate_area']
                    remarks = setlyze.std.make_remarks(items,attr)
                    yield t_row % \
                        (plate_area,
                        int(attr['n']),
                        int(attr['n_sp_observed']),
                        int(statistics_repeats[plate_area]['n_significant']),
                        int(int(statistics_repeats['repeats']) - int(statistics_repeats[plate_area]['n_significant'])),
                        )
                yield t_footer

                yield "\n(table continued)\n\n"

                t_header, t_row, t_footer = self.table(['Plate Area','n (preference)',
                    'n (rejection)'])

                yield t_header
                statistics = self.reader.get_statistics('wilcoxon_areas')
                statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_areas')
                for attr,items in statistics:
                    plate_area = attr['plate_area']
                    yield t_row % \
                        (plate_area,
                        int(statistics_repeats[plate_area]['n_preference']),
                        int(statistics_repeats[plate_area]['n_rejection']),
                        )
                yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_spots' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    attr['n_plates'],
                    attr['n'],
                    float(items['p_value']),
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    setlyze.std.make_remarks(items,attr)
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_spots_repeats' in report_elements:
            yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','n (significant)','n (non-significant)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_spots')
            for attr,items in statistics:
                n_spots = attr['n_positive_spots']
                yield t_row % \
                    (n_spots,
                    int(attr['n_plates']),
                    int(attr['n']),
                    int(statistics_repeats[n_spots]['n_significant']),
                    int(int(statistics_repeats['repeats']) - int(statistics_repeats[n_spots]['n_significant'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','n (attraction)',
                'n (repulsion)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_spots')
            for attr,items in statistics:
                n_spots = attr['n_positive_spots']
                yield t_row % \
                    (n_spots,
                    int(statistics_repeats[n_spots]['n_attraction']),
                    int(statistics_repeats[n_spots]['n_repulsion']),
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, ratios).
        if 'wilcoxon_ratios' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
                'n (distances)','P-value','Mean Observed','Mean Expected'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    setlyze.std.make_remarks(items,attr)
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_ratios_repeats' in report_elements:
            yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

            t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
            'n (distances)','n (significant)','n (non-significant)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_ratios')
            for attr,items in statistics:
                ratio_group = attr['ratio_group']
                yield t_row % \
                    (ratio_group,
                    int(attr['n_plates']),
                    int(attr['n']),
                    int(statistics_repeats[ratio_group]['n_significant']),
                    int(int(statistics_repeats['repeats']) - int(statistics_repeats[ratio_group]['n_significant'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','n (attraction)',
                'n (repulsion)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_ratios')
            for attr,items in statistics:
                ratio_group = attr['ratio_group']
                yield t_row % \
                    (ratio_group,
                    int(statistics_repeats[ratio_group]['n_attraction']),
                    int(statistics_repeats[ratio_group]['n_repulsion']),
                    )
            yield t_footer

        # Add the results for the Chi-squared tests (spots).
        if 'chi_squared_spots' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','P-value','Chi squared','df'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_spots')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['n_positive_spots']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    setlyze.std.make_remarks(items,attr))
            yield t_footer

        # Add the results for the Chi-squared tests (ratios).
        if 'chi_squared_ratios' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(('Ratio Group','n (plates)',
                'n (distances)','P-value','Chi squared','df'))

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (attr['ratio_group'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    setlyze.std.make_remarks(items,attr)
                    )
            yield t_footer

    def export(self, path, elements=None):
        f = open(path, 'w')
        f.writelines(self.generate(elements))
        f.close()

