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

"""This module is for storing frequently used English lines used
throughout the source-code. The purpose is to have a standard place for
storing English sentences. This was basically meant for convenience so
the developer doesn't have to browse through code just to change a
sentence.

This module wasn't created for adding multi-language support, though
it can be easily expanded to do so.
"""

import sys
import logging

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/10/27"

ENGLISH = [
    ('dummy',
        "And tomorrow's forecast is, %s"),
    ('use-saved-data',
        "The SETL data from the last run is still on your computer. The "
        "data was loaded on %s from %s.\n\nSelect Yes to use this (old) "
        "data, or select No to load up-to-date data from the SETL database "
        "(requires a direct connection with the SETL database server)."),
    ('select-locations',
        "Below are the available locations. Please select the locations "
        "from which you want to select species."),
    ('option-change-source',
        "By default, the data is loaded from the SETL database. To load "
        "data from a different data source, click the \"Change Data "
        "Source\" button below."),
    ('selection-tips',
        "Tip: Hold Ctrl or Shift to select multiple items. To select all "
        "items, press Ctrl+A."),
    ('select-species',
        "Below are the available species for the selected location(s). "
        "Please select the species required for the analysis."),
    ('analysis1',
        'Analysis 1 "Spot preference"'),
    ('analysis1-descr',
        "Determine if a specie has preference for a specific spot on "
        "SETL plates."),
    ('analysis2.1',
        'Analysis 2.1 "Attraction of species (intra-specific)"'),
    ('analysis2.1-descr',
        "Determine if a specie attracts or repels individuals of its "
        "own kind."),
    ('analysis2.2',
        'Analysis 2.2 "Attraction of species (inter-specific)"'),
    ('analysis2.2-descr',
        'Determine if two different species attract or repel each other.'),
    ('analysis3',
        'Analysis 3 "Relation between species"'),
    ('analysis3-descr',
        'Determine if one specie is somehow related to another specie.'),
    ('define-plate-areas',
        "Please define the plate areas for the analysis. You can keep "
        "the default setting, meaning that A, B, C and D are treated as "
        "separate plate areas, or you can combine specific areas by "
        "changing the setting below. Combining areas means that the "
        "combined areas are treated as a single plate area. Empty plate "
        "areas are ignored."),
    ('error-single-plate-area',
        "You've chosen to combine all plate spots together, resulting "
        "in a single plate area. This analysis can't continue with just "
        "a single plate area. Please change your setting so that there "
        "are at least two plate areas."),
    ('change-data-source',
        "Select one of the tabs below to change to a different data "
        "source for your analysis."),
    ('change-data-source-csv',
        "Load SETL data from comma separated files (CSV). These data "
        "files must be exported from the MS Access SETL database in CSV "
        "format. The user manual describes how to export these files."),
    ('change-data-source-db',
        "Load SETL data from the main SETL database. This requires a "
        "direct connection with the SETL database server. Please enter "
        "the host name and port number of the SETL database server "
        "below, then press Connect."),
    ('analysis-running',
        "Please stand by while the analysis is running. This may take "
        "a while..."),
    ]

HTML = [
    ('help-loc-selection', "<body xmlns='http://www.w3.org/1999/xhtml'> \
        <div id='content'> \
            <h1>Locations Selection</h1> \
            <p>The <b>locations selection dialog</b> shows a list of all \
            SETL localities. This dialog allows you to select locations \
            from which you want to select species. The <b>species \
            selection dialog</b> which will be displayed after \
            clicking the Continue button, will <i>only</i> \
            display the species that are recorded in the selected \
            locations. Subsequently this means that <i>only</i> \
            the SETL records that match both the locations \
            and species selection will be used for the analysis. \
            </p> \
            <h2>Making a selection</h2> \
            <p>Just click on one of the locations to select it. To \
            select multiple locations, hold Ctrl or Shift. To select \
            all locations, click on a location and press Ctrl+A.</p> \
        </div> \
        </body>"),
    ('help-spe-selection', "<body xmlns='http://www.w3.org/1999/xhtml'> \
        <div id='content'> \
            <h1>Species Selection</h1> \
            <p>The <b>species selection \
            dialog</b> shows a list of all SETL species that \
            were found in the selected SETL localities. This dialog \
            allows you to select the species to be included in the \
            analysis. Only the SETL records that match both the the \
            locations and species selection will be used for the analysis. \
            </p> \
            <p>It is possible to select more than one specie (see below). \
            Selecting more than one specie means the selected species are \
            threated as one specie for the analysis. However, if the \
            selected analysis requires two or more separate \
            specie(s) selections (i.e. two species are compared), it \
            will display the selection dialog multiple times. In \
            this case, the header of the selection dialog will say \
            \"First Selection\", \"Second Selection\", etc.</p> \
            <h2>Making a selection</h2> \
            <p>Just click on one of the species to select it. To select \
            multiple species, hold Ctrl or Shift. To select all species, \
            click on a specie and press Ctrl+A.</p> \
        </div> \
        </body>"),
    ('help-define-plate-areas', "<body xmlns='http://www.w3.org/1999/xhtml'> \
        <div id='content'> \
            <h1>Define Plate Areas</h1>\
            <p>TODO</p>\
        </div> \
        </body>"),
    ('help-analysis-report', "<body xmlns='http://www.w3.org/1999/xhtml'>\
        <div id='content'>\
            <h1>Analysis Report</h1>\
            <p>The <b>analysis report dialog</b> shows the results for\
                the anaylysis. The report is divided into sub elements. Each\
                analysis element is described below.</p>\
                <h2>Locations and Species Selections</h2>\
                <p>Displays the locations and species selections. If\
                multiple selections were made, each element is suffixed by\
                a number. For example \"Species selection (2)\" stands\
                for the second species selection.</p>\
                <h2>Spot Distances</h2>\
                <p>Displays the observed and expected spot distances.</p>\
                <h2>Results for Wilcoxon signed-rank test</h2>\
                <p>Shows the results for the Wilcoxon signed-rank test.\
                First the records are grouped by positive spots numbers.\
                Then the test is performed on each group. Each row contains\
                the result of one test. Each row contains the following\
                elements:\
                <dl>\
                    <dt>Positive Spots</dt>\
                    <dd>A number representing the number of positive\
                    spots. For this test only records matching that\
                    number of positive spots (spots on which the selected\
                    specie was found) were used. The test is first performed\
                    on records with 2 to 24 positive spots. 1 is not excluded\
                    because we can't calculate spot distances with just one\
                    positive spot. 25 is excluded because the results\
                    based on these records will never be significant.\
                    A negative number actually means 'up to that number\
                    of positive spots excluding 1'</dd>\
                    <dt>n (plates)</dt>\
                    <dd>The number of plates that match the number of\
                    positive spots.</dd>\
                    <dt>n (distances)</dt>\
                    <dd>The number of spot distances derived from the\
                    records matching the positive spots number.</dd>\
                    <dt>P-value</dt>\
                    <dd>The P-value for the test.</dd>\
                    <dt>Mean Observed</dt>\
                    <dd>The mean of the observed spot distances.</dd>\
                    <dt>Mean Expected</dt>\
                    <dd>The mean of the expected spot distances.</dd>\
                    <dt>Conf. interval start</dt>\
                    <dd>The start of the confidence interval for the test.</dd>\
                    <dt>Conf. interval end</dt>\
                    <dd>The end of the confidence interval for the test.</dd>\
                    <dt>Remarks</dt>\
                    <dd>A summary of the results. Shows whether the p-value\
                    is significant, and if so, decides based on the mean\
                    if species attract or repel.</dd>\
                </dl>\
            </p>\
            <h2>Results for Pearson's Chi-squared Test for Count Data</h2>\
            <p></p>\
        </div>\
        </body>"),
    ]

HTML_SUBSTITUTIONS = [
    ("<div id='content'>","<div id='content' style='margin-left:5px; margin-right:5px; font-size:110%; font-family:sans-serif,verdana'>"),
    ("<h1>","<p style='font-size:150%; text-decoration:underline; font-weight:bold'>"),
    ("</h1>","</p>"),
    ("<h2>","<p style='font-size:120%; font-weight:bold'>"),
    ("</h2>","</p>"),
    ("<b>","<span style='font-weight:bold'>"),
    ("</b>","</span>"),
    ("<i>","<span style='font-style:italic'>"),
    ("</i>","</span>"),
    ("<dl>","<div style='margin-left:15px'>"),
    ("</dl>","</div>"),
    ("<dt>","<p style='font-weight:bold'>"),
    ("</dt>","</p>"),
    ("<dd>","<p>"),
    ("</dd>","</p>"),
    ]

# Turn the lists into a dictionaries. This provides easier access to items.
ENGLISH = dict(ENGLISH)
HTML = dict(HTML)

def text(key, *args):
    """Return the text string from the ``ENGLISH`` dictionary where key
    is `key`.

    A simple example:

        >>> import setlyze.locale
        >>> setlyze.locale.text('analysis-running')
        'Please stand by while the analysis is running. This may take a while...'

    Substitution is also supported:

        >>> import setlyze.locale
        >>> setlyze.locale.text('dummy', "windy with a slight chance of rain")
        "And tomorrow's forecast is, windy with a slight chance of rain"
    """
    if key not in ENGLISH:
        raise ValueError("Unknown key '%s'" % key)
    if args:
        text = ENGLISH[key] % (args)
    else:
        text = ENGLISH[key]

    return text

def html(key, *args):
    """Return the XHTML code from the ``HTML`` dictionary where key is
    `key`.

    Usage is the same as :meth:`text`.
    """
    if key not in HTML:
        raise ValueError("Unknown key '%s'" % key)
    if args:
        html_code = HTML[key] % (args)
    else:
        html_code = HTML[key]

    # Replace some HTML tags by alternative tags, as not all HTML tags
    # are supported by the third party HTML module we're using.
    for old,new in HTML_SUBSTITUTIONS:
        html_code = html_code.replace(old,new)

    return html_code
