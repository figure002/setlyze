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

"""This modules provides application-wide access to SETLyze's
configuration and data variables.

This module provides an object ``cfg`` for handling a fixed set of
configuration and data variables for SETLyze. The big advantage is that
this makes the variables available across all modules. Here is a small
usage example,

    >>> import setlyze.config
    >>> setlyze.config.cfg.set('alpha-level', 0.01)
    >>> setlyze.config.cfg.set('species-selection', [11, 12, 13, 14], slot=0)
    >>> setlyze.config.cfg.set('species-selection', [15, 16, 17], slot=1)
    >>> print "The alpha level for the t-test and Wilcoxon test is set to", setlyze.config.cfg.get('alpha-level')
    The alpha level for the t-test and Wilcoxon test is set to 0.01
    >>> print "The first species selection is", setlyze.config.cfg.get('species-selection', slot=0)
    The first species selection is [11, 12, 13, 14]
    >>> print "The second species selection is", setlyze.config.cfg.get('species-selection', slot=1)
    The second species selection is [15, 16, 17]

Importing this module in a different module gives access to the same
``cfg`` object, and thus its variables can be obtained or manipulated
using its get() and set() methods.
"""

import os
import sys
import logging

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"


# Path where all data files are stored. The use of os.path.join may seem
# unnecessary, but this is important for cross platform compatibility.
DATA_PATH = os.path.expanduser(os.path.join('~','.setlyze'))

# Path to the local database file.
DB_FILE = os.path.join(DATA_PATH, 'setl_local.db')

# The probability for each spot distance on a 5x5 SETL plate
# (intra-specific).
# Format of the dictionary: {distance: probability, ...}
SPOT_DIST_TO_PROB_INTRA = {
    1: 40/300.0,
    1.41: 32/300.0,
    2: 30/300.0,
    2.24: 48/300.0,
    2.83: 18/300.0,
    3: 20/300.0,
    3.16: 32/300.0,
    3.61: 24/300.0,
    4: 10/300.0,
    4.12: 16/300.0,
    4.24: 8/300.0,
    4.47: 12/300.0,
    5: 8/300.0,
    5.66: 2/300.0,
    }

# The probability for each spot distance on a 5x5 SETL plate
# (inter-specific).
# Format of the dictionary: {distance: probability, ...}
SPOT_DIST_TO_PROB_INTER = {
    0: 25/625.0,
    1: 80/625.0,
    1.41: 64/625.0,
    2: 60/625.0,
    2.24: 96/625.0,
    2.83: 36/625.0,
    3: 40/625.0,
    3.16: 64/625.0,
    3.61: 48/625.0,
    4: 20/625.0,
    4.12: 32/625.0,
    4.24: 16/625.0,
    4.47: 24/625.0,
    5: 16/625.0,
    5.66: 4/625.0,
    }

# Default configurations.
DEFAULT_CONFIG = [
    # Current data source.
    # Design Part: 2.22
    ('data-source', "setl-database"),
    # Did we already make a local database?
    ('has-local-db', False),
    # Make a new database file?
    ('make-new-db', True),
    # Absolute path where all data file are stored.
    ('data-path', DATA_PATH),
    # Absolute path to the local database file.
    ('db-file', DB_FILE),
    # Location selections.
    # Design Part: 2.6
    ('locations-selection', [None,None]),
    # Species selections.
    # Design Part: 2.7
    ('species-selection', [None,None]),
    # Path to localities CSV or XLS file.
    ('localities-file', None),
    # Path to species CSV or XLS file.
    ('species-file', None),
    # Path to records CSV or XLS file.
    ('records-file', None),
    # Path to plates CSV or XLS file.
    ('plates-file', None),
    # Plate areas definition for analysis 1
    # Design Part: 2.24
    ('plate-areas-definition', None),
    # Progress dialog.
    ('progress-dialog', None),
    # Analysis report.
    ('analysis-report', None),
    # Alpha level for normality tests.
    ('alpha-level-normality', 0.05),
    # Alpha level for significance tests. The confidence level is calculated
    # with "1 - alpha-level".
    ('alpha-level', 0.05),
    # Probabilities for each spot distance.
    ('spot-dist-to-prob-intra', SPOT_DIST_TO_PROB_INTRA),
    # Probabilities for each spot distance.
    ('spot-dist-to-prob-inter', SPOT_DIST_TO_PROB_INTER),
    # Number of repeats to perform for statistical tests.
    ('test-repeats', 20),
    # The number of concurrent threads for batch analyses.
    ('thread-pool-size', 1),
    # Save individual batch results.
    ('save-batch-job-results', False),
    # Save path for individual batch results.
    ('job-results-save-path', None),
]

class ConfigManager(object):
    """Class for managing SETLyze's data and configuration variables.

    An instance of this class provides access to a fixed set of
    variables that need to be accessable across SETLyze's modules. By
    importing this module, one instance of this class is created.
    Subsequent imports in other modules provides access to that same
    instance.

    The method set() is used to change the value of variables. The
    method get() is used to get the value of a variable.

    All variables and their default values can be found in the variable
    ``DEFAULT_CONFIG`` of this module.

    Design Part: 1.57
    """

    def __init__(self):
        self._conf = dict(DEFAULT_CONFIG)

    def set(self, key, value, **kwargs):
        """Set the configuration with name `key` to `value`.

        Some configurations have extra keyword arguments. These
        arguments are handled by `kwargs`. The configurations that have
        extra arguments are as follows:

            ``locations-selection``, ``species-selection``
                If `slot` is set to 0 (default), the value is saved
                as the first selection. If set to 1, the value is saved
                as the second selection.
        """
        if key not in self._conf:
            raise ValueError("ConfigManager: unknown key '%s'" % key)

        if key == 'data-source':
            self.set_data_source(value)
            return

        if key in ('locations-selection', 'species-selection'):
            if value == None:
                # To reset the selection variables, use 'None' as the
                # value. If value is 'None', save it as [None,None].
                self._conf[key] = [None,None]
            elif isinstance(value, list):
                # The selection variable is a list, containing lists
                # of selected items. At the moment a selection variable
                # can contain up to two selection lists (two slots).
                # Default, insert the selection list in the first
                # slot (slot=0). If a slot is provided, use that slot
                # instead.
                slot = kwargs.get('slot', 0)
                self._conf[key][slot] = value
            else:
                raise TypeError( "ConfigManager: invalid type %s for '%s'. \
                                Must be either of type 'list' or 'None'." %
                    (type(value), key) )
            return

        # Set the new value for the configuration key.
        self._conf[key] = value

    def set_data_source(self, source):
        """Set the configuration with name ``data-source`` to `source`.

        Possible values for `source` are ``setl-database``, ``xls`` and
        ``csv-msaccess``. The value of this configuration tells the
        application where to look for SETL data. This is especially used
        by the database module.

        If an unknown data source is given, an error is printed.
        """

        # Legal data sources.
        legal_sources = ("setl-database", "csv-msaccess", "xls")

        if source in legal_sources:
            # Set the new data source.
            self._conf['data-source'] = source

            # A new database file must be created when the data source has
            # changed.
            self.set('make-new-db', True)
        else:
            raise ValueError("Encountered unknown data source '%s'" % source)

    def get(self, key, **kwargs):
        """Return the value for the configuration with name `key`.

        Some configurations have extra keyword arguments. These
        arguments are handled by `kwargs`. The configurations that have
        extra arguments are as follows:

            ``locations-selection``, ``species-selection``
                If `slot` is set to 0 (default), the value of the
                first selection is returned. If set to 1,the second
                selection is returned.
        """
        if key not in self._conf:
            raise ValueError("Unknown key '%s'" % key)

        if key in ('locations-selection', 'species-selection'):
            slot = kwargs.get('slot', None)
            if isinstance(slot, int):
                return self._conf[key][slot]

        return self._conf.get(key)

# Create an instance of ConfigManager. This instance is only created
# once, upon the first import. Subsequent imports will use the first
# instance (so it seems). So this instance is accessible between all
# modules.
cfg = ConfigManager()
