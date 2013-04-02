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
        "By default the data is loaded from the SETL database. To load "
        "data from a different data source, click the \"Load Data\" button below."),
    ('selection-tips',
        "Tip: Hold Ctrl or Shift to select multiple items. To select all "
        "items, press Ctrl+A."),
    ('select-species',
        "Below are the available species for the selected location(s). Please "
        "select the species to be included for the analysis.\n\n"
        "It is possible to select more than one species. Selecting more than "
        "one species means that the selected species are treated as one "
        "species for the analysis."),
    ('select-species-batch-mode',
        "Below are the available species for the selected location(s). Please "
        "select the species to be included for the analysis.\n\n"
        "It is possible to select more than one species. Selecting more than "
        "one species means that the analysis is repeated for each of the "
        "selected species."),
    ('select-species-batch-mode-inter',
        "Below are the available species for the selected location(s). Please "
        "select the species to be included for the analysis.\n\n"
        "It is possible to select more than one species. Selecting more than "
        "one species means that the analysis is repeated for each possible "
        "inter species combination of the selected species."),
    ('analysis-spot-preference',
        'Analysis Spot preference'),
    ('analysis-spot-preference-descr',
        "Determine if a species has preference for a specific area on SETL "
        "plates."),
    ('analysis-attraction-intra',
        'Analysis Attraction within Species'),
    ('analysis-attraction-intra-descr',
        "Determine if a species attracts or repels individuals of its "
        "own kind."),
    ('analysis-attraction-inter',
        'Analysis Attraction between Species'),
    ('analysis-attraction-inter-descr',
        "Determine if two different species attract or repel each other."),
]

# Turn the list into a dictionary. This provides easier access to its
# items.
ENGLISH = dict(ENGLISH)

def text(key, *args):
    """Return the text string from the ``ENGLISH`` dictionary where key
    is `key`.

    A simple example:

        >>> import setlyze.locale
        >>> setlyze.locale.text('analysis-spot-preference-descr')
        'Determine if a species has preference for a specific area on SETL plates.'

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
