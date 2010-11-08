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

import os
import sys
import logging

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"


# Path where all data files are stored. The use of os.path.join may seem
# unnecessary, but this is important for cross platform compatibility.
DATA_PATH = os.path.expanduser(os.path.join('~','.setlyze'))

# Path to the local database file.
DB_FILE = os.path.join(DATA_PATH, 'setl_local.db')

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
    # Path to localities CSV file.
    ('localities-file', None),
    # Path to species CSV file.
    ('species-file', None),
    # Path to records CSV file.
    ('records-file', None),
    # Path to plates CSV file.
    ('plates-file', None),
    # Plate areas definition for analysis 1
    # Design Part: 2.24
    ('plate-areas-definition', None),
    # Progress dialog.
    ('progress-dialog', None),
    # Analysis report.
    ('analysis-report', None),
    # Normality test: alpha level.
    ('normality-alpha', 0.05),
    # Significance test: alpha level.
    ('significance-alpha', 0.05),
    # Significance test: confidence level.
    ('significance-confidence', 0.95),
]

class ConfigManager(object):
    """
    There is just one ConfigManager instance, which holds and
    manipulates the configurations and data variables.

    Design Part: 1.57
    """

    def __init__(self):
        self._conf = dict(DEFAULT_CONFIG)

    def set(self, key, value, **kwargs):
        """Set the configure value for a configure key."""
        if key not in self._conf:
            logging.error("ConfigManager: unknown key '%s'" % key)
            sys.exit(1)

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
                logging.error( "ConfigManager: invalid type %s for '%s'. \
                                Must be either of type 'list' or 'None'." %
                    (type(value), key) )
                sys.exit(1)
            return

        # Set the new value for the configuration key.
        self._conf[key] = value

    def get(self, key, **kwargs):
        """Return the configure value for a configure key."""
        if key not in self._conf:
            logging.error("ConfigManager: unknown key '%s'" % key)
            sys.exit(1)

        if key in ('locations-selection', 'species-selection'):
            slot = kwargs.get('slot', 0)
            return self._conf[key][slot]

        return self._conf.get(key)

    def set_data_source(self, source):
        """
        Set the application variable 'data_source' to a new value.
        This variable is used to decide where to get the data from.

        Keyword arguments:
        source - A string representing the new data source.
                 Can be one of "setl-database", "csv-msaccess".
        """

        # Legal data sources.
        legal_sources = ("setl-database", "csv-msaccess")

        if source in legal_sources:
            # Set the new data source.
            self._conf['data-source'] = source

            # A new database file must be created when the data source has
            # changed.
            self.set('make-new-db', True)
        else:
            logging.error("Encountered unknown data source of type '%s'" % source)
            sys.exit(1)

# Create an instance of ConfigManager. This instance is only created
# once, upon the first import. Subsequent imports will use the first
# instance (so it seems). So this instance is accessible between all
# modules.
cfg = ConfigManager()
