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

"""The module is for storing frequently used English lines throughout the
application. The purpose is to easily change english sentences in the
application without having to look them up in the different modules.

This module wasn't created for adding multi-language support, though
this module can be easily expanded to do so.

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
    ('use-saved-data', "The SETL data from the last run is still on your computer. The data was loaded on %s from %s.\n\nSelect Yes to use this (old) data, or select No to load up-to-date data from the SETL database (requires a direct connection with the SETL database server)."),
    ('select-locations', "Below are the available locations. Please select the locations from which you want to select species."),
    ('option-change-source', "By default, the data is loaded from the SETL database. To load data from a different data source, click the \"Change Data Source\" button below."),
    ('selection-tips', "Tip: Hold Ctrl or Shift to select multiple items. To select all items, press Ctrl+A."),
    ('select-species', "Below are the available species for the selected location(s). Please select the species required for the analysis."),
    ('analysis1', 'Analysis 1 "Spot preference"'),
    ('analysis1-descr', 'Determine if a specie has preference for a specific spot on SETL plates.'),
    ('analysis2.1', 'Analysis 2.1 "Attraction of species (intra-specific)"'),
    ('analysis2.1-descr', 'Determine if a specie attracts or repels individuals of its own kind.'),
    ('analysis2.2', 'Analysis 2.2 "Attraction of species (inter-specific)"'),
    ('analysis2.2-descr', 'Determine if two different species attract or repel each other.'),
    ('analysis3', 'Analysis 3 "Relation between species"'),
    ('analysis3-descr', 'Determine if one specie is somehow related to another specie.'),
    ('define-plate-areas', "Please define the plate areas for the analysis. You can keep the default setting, meaning that A, B, C and D are treated as separate plate areas, or you can combine specific areas by changing the setting below. Combining areas means that the combined areas are treated as a single plate area. Empty plate areas are ignored."),
    ('error-single-plate-area', "You've chosen to combine all plate spots together, resulting in a single plate area. This analysis can't continue with just a single plate area. Please change your setting so that there are at least two plate areas."),
    ('change-data-source', "Select one of the tabs below to change to a different data source for your analysis."),
    ('change-data-source-csv', "Load SETL data from comma separated files (CSV). These data files must be exported from the MS Access SETL database in CSV format. The user manual describes how to export these files."),
    ('change-data-source-db', "Load SETL data from the main SETL database. This requires a direct connection with the SETL database server. Please enter the host name and port number of the SETL database server below, then press Connect."),
    ('analysis-running', "Please stand by while the analysis is running. This may take a while..."),
]

# Turn the list into a dictionary. This provides easy access to items.
ENGLISH = dict(ENGLISH)

def text(key, *args):
    """Return the full text string from the dictionary."""
    if key not in ENGLISH:
        logging.error("setlyze.locale.text: unknown key '%s'" % key)
        sys.exit(1)

    if args:
        text = ENGLISH[key] % (args)
    else:
        text = ENGLISH[key]

    return text
