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

"""This module is for storing and retrieving messages used in SETLyze.
The purpose is to have a standard place for storing these messages. This was
basically meant for convenience so the developer doesn't have to browse
through SETLyze's code base just to change a sentence.

This module wasn't created for adding multi-language support, though
it can be easily expanded to do so.
"""

import sys
import logging

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"

ENGLISH = [
    ('dummy',
        "And tomorrow's forecast is, %s"),
    ('select-locations',
        "Below are the available locations. Please select the locations "
        "from which you want to select species."),
    ('option-change-source',
        "By default, the data is loaded from the remote SETL database. To load "
        "data from a different data source, click the \"Change Data "
        "Source\" button below."),
    ('selection-tips',
        "Tip: Hold Ctrl or Shift to select multiple items. To select all "
        "items, press Ctrl+A."),
    ('select-species',
        "Below are the available species for the selected location(s). Please "
        "select the species to be included for the analysis."),
    ('analysis1',
        'Analysis Spot preference'),
    ('analysis1-descr',
        "Determine if a species has preference for a specific area on SETL "
        "plates."),
    ('analysis2',
        'Analysis Attraction within Species'),
    ('analysis2-descr',
        "Determine if a species attracts or repels individuals of its "
        "own kind."),
    ('analysis3',
        'Analysis Attraction between Species'),
    ('analysis3-descr',
        "Determine if two different species attract or repel each other."),
    ('analysis4',
        'Analysis Relation between Species'),
    ('analysis4-descr',
        "Determine if there is a relation between the presence/absence of two "
        "species in a specific location."),
    ('analysis-batch',
        'Batch mode'),
    ('analysis-batch-descr',
        "Enter batch mode to repeat analyses for a selection of species."),
    ('define-plate-areas',
        "Please define the plate areas for the Chi-squared test. You can keep "
        "the default setting, meaning that A, B, C and D are treated as "
        "separate plate areas, or you can combine specific areas by "
        "changing the setting below. Combining areas means that the "
        "combined areas are treated as a single plate area. Empty plate "
        "areas are ignored. This plate area definition will not be used for the "
        "Wilcoxon test because a fixed set of plate areas will be tested."),
    ('error-single-plate-area',
        "You've chosen to combine all plate areas together, resulting "
        "in a single plate area. This analysis requires at least two plate "
        "areas. Please change your plate areas definition."),
    ('change-data-source',
        "Click on one of the tabs below to change to a different data "
        "source."),
    ('change-data-source-csv',
        "Load SETL data from CSV files. These data files must "
        "be exported from the Microsoft Access SETL database in CSV "
        "format. The user manual describes how to export these files."),
    ('change-data-source-xls',
        "Load SETL data from xls files. "
        "The user manual describes how to export these files."),
    ('change-data-source-db',
        "Load SETL data from the remote SETL database. This requires a "
        "direct connection with the SETL database server. This feature "
        "has not been implemented yet."),
    ('analysis-running',
        "Please stand by while the analysis is running. This may take "
        "a while..."),
    ('invalid-alpha-level',
        "You entered an invalid alpha level. The alpha level must be a "
        "probability between 0 and 1."),
    ('invalid-repeats-number',
        "You entered an invalid repeats number. The number of repeats for "
        "statistical tests must be 2 or higher."),
    ('empty-plate-areas',
        "The selected species weren't found on any SETL plates from the selected "
        "locations. Try again with different locations or select more "
        "locations."),
    ('t-plate-areas-definition',
        "Plate Areas Definition for Chi-squared Test"),
    ('t-plate-area-totals',
        "Species Totals per Plate Area for Chi-squared Test"),
    ('t-results-wilcoxon-rank-sum',
        "Results for Wilcoxon rank-sum tests (non-repeated)"),
    ('t-results-pearson-chisq',
        "Results for Pearson's Chi-squared Tests for Count Data"),
    ('t-results-shapiro-wilk',
        "Results for Shapiro-Wilk tests of normality"),
    ('t-significance-results-repeats',
        "Significance results for repeated %s tests"),
    ('csv-files-not-selected',
        "You didn't select all CSV files. SETLyze requires four CSV files "
        "as input. See the user manual for more information. Please select "
        "all four files and try again."),
    ('xls-files-not-selected',
        "You didn't select all xls files. SETLyze requires four xls files "
        "as input. See the user manual for more information. Please select "
        "all four files and try again."),
    ('csv-import-failed',
        "Failed to load the SETL data from the CSV or XLS files. "
        "This is probably caused by an incorrect format of the input file. "
        "SETLyze requires the input files to be in a specific format. "
        "Please follow the instructions in the user manual on how to "
        "create the CSV files in the required format.\n\n"
        "The error returned was: %s"),
    ('cancel-pressed',
        "Analysis aborted by user."),
    ('no-results',
        "The analysis did not return any results, most likely because there "
        "wasn't enough data for the analysis."),
    ]

# Turn the list into a dictionary. This provides easier access to its
# items.
ENGLISH = dict(ENGLISH)

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
