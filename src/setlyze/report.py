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

import datetime
import logging
from sqlite3 import dbapi2 as sqlite

import setlyze.config
from setlyze.std import make_remarks

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/26"

def export(report, path, type):
    """Export the data from a :class:`Report` object `report` to a data file.

    The file is saved to `path` in a format specified by `type`. The following
    values for `type` are currently supported:

        * ``rst`` (reStructuredText)

    Design Part: 1.17
    """
    if type == 'rst':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".rst"):
            path += ".rst"
        exporter = ExportRstReport(report)
        exporter.export(path)
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
        self.options = {}
        self.definitions = {}

    def is_empty(self):
        """Return True if this is an empty report."""
        return self.statistics == {}

    def set_option(self, name, value):
        """Set an analysis option `name` to value `value`.

        This can be used for things like alpha level and the number of repeats
        for the analysis. They will appear in exported reports.
        """
        self.options[name] = value

    def set_definitions(self, definitions):
        """Set the definitions dictionary `definitions`.

        This is used to print a definition list in the report.
        """
        self.definitions = definitions

    def get_option(self, name):
        """Return the value for an analysis option `name`."""
        return self.options[name]

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
        """Set statistics results `data` under key `name` in self.statistics.

        This method is used to save results from statistical tests. The results
        must be supplied with the `data` argument. The `data` argument is a
        list containing dictionaries in the format
        {'attr': {'<key>': <value>, ...}, 'results': {'<key>': <value>, ...}}
        where the value for 'attr' is a dictionary with the attributes for the
        test and 'results' is a dictionary with elements of the results.

        If the 'attr' key is not set in `data` (or equals None/False), the
        results are assumed to be absent/incomplete, and the results are not
        stored.

        The value for ``data['attr']['groups']`` tells what the dictionary keys
        for ``data['results']`` represent. Possible groups are ``areas`` for
        plate areas, ``spots`` for total positive spots, and ``ratios`` for
        total positive spots ratio groups. If ``data['attr']['groups']`` is not
        set, there are no groups, meaning that the ``data['results']``
        dictionary contains results for a single statistical test.

        Example of `data` without groups ::

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

        Examples of `data` with groups ::

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
        if not data.get('attr'):
            return
        if name in self.statistics:
            self.statistics[name].append(data)
        else:
            self.statistics[name] = [data]

class ExportRstReport(object):
    """Export an analysis report in reStructuredText format.

    The input is a :class:`Report` object.
    """

    def __init__(self, report):
        self.report = None
        self.set_report(report)
        self.predefined_col_widths = {
            "df": 6,
            "Remarks": 40,
            "Species": 50,
            "Species A": 50,
            "Species B": 50,
            "W": 6,
        }
        self.predefined_fields = {
            "Plate Area": "%%-%ds",
            "Area ID": "%%-%ds",
            "P-value": "%%%d.4f",
            "Chi squared": "%%%d.4f",
            "Plate Area": "%%-%ds",
            "Plate Area Surfaces": "%%-%ds",
            "Mean Observed": "%%%d.4f",
            "Mean Expected": "%%%d.4f",
            "Remarks": "%%-%ds",
            "Species": "%%-%ds",
            "Species A": "%%-%ds",
            "Species B": "%%-%ds",
        }

    def set_report(self, report):
        """Set the report object `report`."""
        if isinstance(report, setlyze.report.Report):
            self.report = report
        else:
            ValueError("Report must be an instance of setlyze.report.Report")

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

    def deflist(self, definitions):
        """Return a definition list from the dictionary `definitions`."""
        yield self.section("Definitions")
        for term, definition in definitions.iteritems():
            yield "%s\n  %s\n\n" % (term,definition)

    def table(self, headers, mincolwidth=1):
        """Return a table header with column names from `headers` in
        reStructuredText format.

        `headers` is a list of strings representing the column names.
        """
        header = ""
        header_lengths = []
        header_placeholders = []
        row_placeholders = []

        # Generate a placeholder strings for the column names and the fields.
        for name in headers:
            if name not in self.predefined_col_widths:
                length = len(name)
            else:
                length = self.predefined_col_widths[name]

            if length < mincolwidth:
                length = mincolwidth

            # Save the lengths of all column names. This is needed for
            # generating the table rules.
            header_lengths.append(length)

            # Construct the placeholders for the column names.
            header_placeholders.append("%%-%ds" % length)

            # Construct the placeholders for the fields.
            if name not in self.predefined_fields:
                row_placeholders.append("%%%ds" % length)
            else:
                row_placeholders.append(self.predefined_fields[name] % length)

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
        footer = self.table_rule(header_lengths)+"\n"

        return (header,row_placeholders,footer)

    def get_column_widths(self, headers, mincolwidth=1):
        """Return the column widths for a list of column names.

        Argument `headers` is a list of strings representing the column names.
        """
        col_widths = []
        for name in headers:
            if name not in self.predefined_col_widths:
                length = len(name)
            else:
                length = self.predefined_col_widths[name]
            if length < mincolwidth:
                length = mincolwidth
            col_widths.append(length)
        return col_widths

    def table_span_header(self, col_widths, headers, spans):
        """Return a table header row with main columns spanned headers.

        Argument `col_widths` is a list of widths for the main table columns,
        `headers` is a list of column names that need to be spanned over
        the main columns, `spans` is a list of integers, each integer
        indicating the number of columns the corresponding column in `headers`
        should span, hence `headers` and `spans` must have the same number
        of items.
        """
        assert len(headers) == len(spans), \
            "Length of arguments 'headers' and 'spans' are not equal."

        # Calculate the width for each spanned column.
        spanned_col_widths = []
        last_col = 0
        for span in spans:
            assert span < len(col_widths), \
                "Cannot span outside the table boundaries."
            width = 0
            for s in range(last_col, last_col+span):
                width += col_widths[s]
            width += 2*(span-1)
            spanned_col_widths.append(width)
            last_col += span

        # Construct the column names row.
        header_row = []
        for i,header in enumerate(headers):
            assert len(header) <= spanned_col_widths[i], \
                ("The width of a header (%s) cannot exceed the width "
                "of the spanned column (%d)") % (header, spanned_col_widths[i])
            if header == '..':
                header_row.append(header.ljust(spanned_col_widths[i]))
            else:
                header_row.append(header.center(spanned_col_widths[i]))
        header_str = "  ".join(header_row) + "\n"

        # Construct the column span underlines row.
        header_str += self.table_rule(spanned_col_widths, char='-')

        return header_str

    def table_rule(self, col_widths, char='='):
        """Return a rule for a table with column widths `col_widths`.

        Argument `col_widths` is a list with column widths (integers), and
        `char` the character used to make rules.
        """
        row = []
        for w in col_widths:
            row.append(char*w)
        return "  ".join(row) + "\n"

    def get_lines(self):
        """Return the analysis report in reStructuredText format."""

        # Title
        analysis_name = getattr(self.report, 'analysis_name', None)
        if analysis_name:
            yield self.part("SETLyze Analysis Report - %s" % analysis_name)
        else:
            yield self.part("SETLyze Analysis Report")

        # Info
        for line in self.add_info():
            yield line

        # Locations and species selections
        locations_selections = getattr(self.report, 'locations_selections', None)
        species_selections = getattr(self.report, 'species_selections', None)
        if locations_selections and species_selections:
            for line in self.add_selections(locations_selections, species_selections):
                yield line

        # Plate areas definition
        plate_areas_definition = getattr(self.report, 'plate_areas_definition', None)
        if plate_areas_definition:
            for line in self.add_plate_areas_definition(plate_areas_definition):
                yield line

        # Species Totals per Plate Area
        area_totals_observed = getattr(self.report, 'area_totals_observed', None)
        area_totals_expected = getattr(self.report, 'area_totals_expected', None)
        if area_totals_observed and area_totals_expected:
            for line in self.add_area_totals(area_totals_observed,area_totals_expected):
                yield line

        # chi_squared_areas
        chi_squared_areas = self.report.statistics.get('chi_squared_areas', [])
        for stats in chi_squared_areas:
            for line in self.add_statistics_chisq_areas(stats):
                yield line

        # wilcoxon_spots
        wilcoxon_spots = self.report.statistics.get('wilcoxon_spots', [])
        for stats in wilcoxon_spots:
            for line in self.add_statistics_wilcoxon_spots(stats):
                yield line

        # wilcoxon_spots_repeats
        wilcoxon_spots_repeats = self.report.statistics.get('wilcoxon_spots_repeats', [])
        for stats in wilcoxon_spots_repeats:
            for line in self.add_statistics_repeats_spots(stats):
                yield line

        # wilcoxon_ratios
        wilcoxon_ratios = self.report.statistics.get('wilcoxon_ratios', [])
        for stats in wilcoxon_ratios:
            for line in self.add_statistics_wilcoxon_ratios(stats):
                yield line

        # wilcoxon_ratios_repeats
        wilcoxon_ratios_repeats = self.report.statistics.get('wilcoxon_ratios_repeats', [])
        for stats in wilcoxon_ratios_repeats:
            for line in self.add_statistics_repeats_ratios(stats):
                yield line

        # wilcoxon_areas
        wilcoxon_areas = self.report.statistics.get('wilcoxon_areas', [])
        for stats in wilcoxon_areas:
            for line in self.add_statistics_wilcoxon_areas(stats):
                yield line

        # wilcoxon_areas_repeats
        wilcoxon_areas_repeats = self.report.statistics.get('wilcoxon_areas_repeats', [])
        for stats in wilcoxon_areas_repeats:
            for line in self.add_statistics_repeats_areas(stats):
                yield line

        # chi_squared_spots
        chi_squared_spots = self.report.statistics.get('chi_squared_spots', [])
        for stats in chi_squared_spots:
            for line in self.add_statistics_chisq_spots(stats):
                yield line

        # chi_squared_ratios
        chi_squared_ratios = self.report.statistics.get('chi_squared_ratios', [])
        for stats in chi_squared_ratios:
            for line in self.add_statistics_chisq_ratios(stats):
                yield line

        # plate_areas_summary
        plate_areas_summary = self.report.statistics.get('plate_areas_summary', [])
        for stats in plate_areas_summary:
            for line in self.add_batch_summary(stats, "Spot Preference"):
                yield line

        # positive_spots_summary
        positive_spots_summary = self.report.statistics.get('positive_spots_summary', [])
        for stats in positive_spots_summary:
            for line in self.add_batch_summary(stats, "Attraction within Species"):
                yield line

        # ratio_groups_summary
        ratio_groups_summary = self.report.statistics.get('ratio_groups_summary', [])
        for stats in ratio_groups_summary:
            for line in self.add_batch_summary(stats, "Attraction between Species"):
                yield line

        # Print definitions.
        definitions = getattr(self.report, 'definitions', None)
        if definitions:
            for line in self.deflist(definitions):
                yield line

    def add_info(self, toc=False):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %z (%a, %d %b %Y)")
        yield "\n"
        yield ":Generator: SETLyze %s\n" % (__version__)
        yield ":Date: $Date: %s $\n" % (date)
        for name, val in self.report.options.iteritems():
            yield ":%s: %s\n" % (name, val)
        yield "\n"
        if toc:
            yield ".. contents::\n"
            yield "\n"

    def add_selections(self, locations_selections, species_selections):
        yield self.section("Locations and Species Selections")
        for i, selection in enumerate(species_selections, start=1):
            yield self.subsection("Species Selection (%d)" % i)
            for spe_id, species in selection.iteritems():
                if len(species['name_latin']) ==  0:
                    yield "- %s\n" % (species['name_common'])
                elif len(species['name_common']) ==  0:
                    yield "- *%s*\n" % (species['name_latin'])
                else:
                    yield "- *%s* (%s)\n" % (species['name_latin'], species['name_common'])

        for i, selection in enumerate(locations_selections, start=1):
            yield self.subsection("Locations Selection (%d)" % i)
            for loc_id, loc in selection.iteritems():
                yield "- %s\n" % loc['name']

    def add_plate_areas_definition(self, definition):
        yield self.section("Plate Areas Definition for Chi-squared Test")
        t_header, t_row, t_footer = self.table(["Area ID","Plate Area Surfaces"])
        yield t_header
        for area_id, spots in sorted(definition.iteritems()):
            spots = ", ".join(spots)
            yield t_row % (area_id, spots)
        yield t_footer

    def add_area_totals(self, observed, expected):
        yield self.section("Species Totals per Plate Area for Chi-squared Test")

        t_header, t_row, t_footer = self.table(["Area ID","Observed Totals",
            "Expected Totals"])
        yield t_header
        for area_id in sorted(observed):
            yield t_row % (
                area_id,
                observed[area_id],
                expected[area_id],
            )
        yield t_footer

    def add_statistics_wilcoxon_spots(self, statistics):
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
        'n (distances)','P-value','Mean Observed','Mean Expected'])

        yield t_header
        for positive_spots,stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['mean_observed'],
                stats['mean_expected'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Positive Spots','Remarks'])

        yield t_header
        for positive_spots,stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                make_remarks(stats, statistics['attr']),
            )
        yield t_footer

    def add_statistics_wilcoxon_ratios(self, statistics):
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected'])

        yield t_header
        for ratio_group,stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['mean_observed'],
                stats['mean_expected'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Ratio Group','Remarks'])

        yield t_header
        for ratio_group,stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                make_remarks(stats, statistics['attr']),
            )
        yield t_footer

    def add_statistics_wilcoxon_areas(self, statistics):
        """Add the statistic results to the report dialog."""
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
            'n (observed species)', 'n (expected species)', 'P-value'])

        yield t_header
        for area, stats in statistics['results'].iteritems():
            yield t_row % (
                area,
                stats['n_values'],
                stats['n_sp_observed'],
                stats['n_sp_expected'],
                stats['p_value'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Plate Area','Mean Observed',
            'Mean Expected','Remarks'])

        yield t_header
        for area, stats in statistics['results'].iteritems():
            yield t_row % (
                area,
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            )
        yield t_footer

    def add_statistics_chisq_spots(self, statistics):
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
        'n (distances)','P-value','Chi squared','df'])

        yield t_header
        for positive_spots,stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['chi_squared'],
                stats['df'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Positive Spots','Mean Observed',
            'Mean Expected','Remarks'])

        yield t_header
        for positive_spots,stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            )
        yield t_footer

    def add_statistics_chisq_areas(self, statistics):
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['P-value','Chi squared','df',
            'Remarks'])

        yield t_header
        yield t_row % (
            statistics['results']['p_value'],
            statistics['results']['chi_squared'],
            statistics['results']['df'],
            make_remarks(statistics['results'],statistics['attr']),
        )
        yield t_footer

    def add_statistics_chisq_ratios(self, statistics):
        yield self.section(statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(('Ratio Group','n (plates)',
            'n (distances)','P-value','Chi squared','df'))

        yield t_header
        for ratio_group, stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['chi_squared'],
                stats['df'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Ratio Group','Mean Observed',
            'Mean Expected','Remarks'])

        yield t_header
        for ratio_group, stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
                )
        yield t_footer

    def add_statistics_repeats_areas(self, statistics):
        yield self.section("%s (repeated)" % statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
            'n (observed species)','n (significant)',
            'n (non-significant)'])

        yield t_header
        for plate_area, stats in statistics['results'].iteritems():
            yield t_row % (
                plate_area,
                stats['n_values'],
                stats['n_sp_observed'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Plate Area','n (preference)',
            'n (rejection)'])

        yield t_header
        for plate_area, stats in statistics['results'].iteritems():
            yield t_row % (
                plate_area,
                stats['n_preference'],
                stats['n_rejection'],
            )
        yield t_footer

    def add_statistics_repeats_spots(self, statistics):
        yield self.section("%s (repeated)" % statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
        'n (distances)','n (significant)','n (non-significant)'])

        yield t_header
        for positive_spots, stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Positive Spots','n (attraction)',
            'n (repulsion)'])

        yield t_header
        for positive_spots, stats in statistics['results'].iteritems():
            yield t_row % (
                positive_spots,
                stats['n_attraction'],
                stats['n_repulsion'],
            )
        yield t_footer

    def add_statistics_repeats_ratios(self, statistics):
        yield self.section("%s (repeated)" % statistics['attr']['method'])

        t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
        'n (distances)','n (significant)','n (non-significant)'])

        yield t_header
        for ratio_group, stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
            )
        yield t_footer

        yield "\n(table continued)\n\n"

        t_header, t_row, t_footer = self.table(['Ratio Group','n (attraction)',
            'n (repulsion)'])

        yield t_header
        for ratio_group, stats in statistics['results'].iteritems():
            yield t_row % (
                ratio_group,
                stats['n_attraction'],
                stats['n_repulsion'],
                )
        yield t_footer

    def add_batch_summary(self, statistics, title):
        """Generate a batch summary report."""
        yield self.section("Batch summary - %s" % title)
        t_header, t_row, t_footer = self.table(statistics['attr']['columns'], mincolwidth=2)

        # Figure out which columns display species names.
        species_cols = []
        for col,val in enumerate(statistics['attr']['columns']):
            if "Species" in val:
                species_cols.append(col)

        # Return a complicated table header consisting of two rows and cells
        # that span multiple rows. Used instead of the simple `t_header`.
        col_widths = self.get_column_widths(statistics['attr']['columns'], mincolwidth=2)
        yield self.table_rule(col_widths)
        yield self.table_span_header(col_widths,
            statistics['attr']['columns_over'],
            statistics['attr']['columns_over_spans']
        )
        yield t_row % tuple(statistics['attr']['columns'])
        yield self.table_rule(col_widths)

        # Return the data rows.
        for row in statistics['results']:
            c_row = []
            for col,val in enumerate(row):
                if val is True:
                    c_row.append('y')
                elif val is False:
                    c_row.append('n')
                elif val is None:
                    c_row.append('na')
                elif col in species_cols:
                    c_row.append("*%s*" % val)
                else:
                    c_row.append(val)
            yield t_row % tuple(c_row)
        yield t_footer

    def export(self, path, elements=None):
        """Generate and export the report to a file."""
        f = open(path, 'w')
        f.writelines(self.get_lines())
        f.close()
