#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010-2013, GiMaRIS <info@gimaris.com>
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

"""This modules provides application-wide access to SETLyze's configuration
variables.

This module provides an object *cfg* for handling a fixed set of configuration
variables for SETLyze. The big advantage is that this makes the variables
available across all modules. Here is a small usage example,

    >>> import setlyze.config
    >>> setlyze.config.cfg.set('alpha-level', 0.01)
    >>> print "The alpha level for statistical tests is set to %s" % setlyze.config.cfg.get('alpha-level')
    The alpha level for statistical tests is set to 0.01

Importing this module in a different module gives access to the same *cfg*
object, and thus its variables can be obtained or manipulated using its
:meth:`ConfigManager.get` and :meth:`ConfigManager.set` methods.
"""

import os
import multiprocessing
import ConfigParser

import appdirs

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010-2013, GiMaRIS"
__license__ = "GPL3"
__version__ = "1.0"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"


# Path where all user data files are stored.
DATA_PATH = appdirs.user_data_dir("SETLyze", "GiMaRIS")

# Path to the local database file.
DB_FILE = os.path.join(DATA_PATH, 'setl_local.db')

# Path to the configurations file.
CONF_FILE = os.path.join(DATA_PATH, 'setlyze.conf')

# Set the default number of processes for batch mode from the CPU count.
# By default use 90% of the number of CPUs.
try:
    CPU_COUNT = multiprocessing.cpu_count()
except:
    # Default to 1 if the CPU count can't be defined.
    CPU_COUNT = 1
processes = int(CPU_COUNT*0.9)
if processes < 1: processes = 1

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
    # Minimum database version required.
    ('minimum-db-version', 0.4),
    # Path to localities file.
    ('localities-file', None),
    # Path to species file.
    ('species-file', None),
    # Path to records file.
    ('records-file', None),
    # Path to plates file.
    ('plates-file', None),
    # Alpha level for significance tests. The confidence level is calculated
    # with "1 - alpha-level".
    ('alpha-level', 0.05),
    # Probabilities for each spot distance.
    ('spot-dist-to-prob-intra', SPOT_DIST_TO_PROB_INTRA),
    # Probabilities for each spot distance.
    ('spot-dist-to-prob-inter', SPOT_DIST_TO_PROB_INTER),
    # Number of repeats to perform for statistical tests.
    ('test-repeats', 20),
    # Number of CPUs.
    ('cpu-count', CPU_COUNT),
    # Number of concurrent processes for batch mode.
    ('concurrent-processes', processes),
]

class ConfigManager(object):
    """Class for managing SETLyze's configuration variables.

    An instance of this class provides access to a fixed set of variables
    that need to be accessable across SETLyze's modules. By importing this
    module, one instance of this class is created. Subsequent imports in other
    modules provides access to that same instance.

    The method :meth:`set` is used to change the value of variables. The
    method :meth:`get` is used to get the value of a variable.

    All configurations and their default values can be found in global variable
    `DEFAULT_CONFIG` of this module.

    Design Part: 1.57
    """

    def __init__(self):
        self._conf = dict(DEFAULT_CONFIG)
        # Try to read configurations from a config file.
        self.read_from_file()

    def read_from_file(self):
        """Try to read settings from a configuration file.

        The default location of the configuration file is
        ``~/.setlyze/setlyze.cfg``.
        """
        ints = ('test-repeats','concurrent-processes')
        floats = ('alpha-level')
        parser = ConfigParser.SafeConfigParser()
        files = parser.read(CONF_FILE)
        if len(files) > 0:
            for section in ['general']:
                for name in parser.options(section):
                    try:
                        if name in ints:
                            self.set(name, parser.getint(section, name))
                        elif name in floats:
                            self.set(name, parser.getfloat(section, name))
                        else:
                            self.set(name, parser.get(section, name))
                    except:
                        # Skip the configuration if we fail to set it.
                        continue

    def save_to_file(self):
        """Save user customizable settings to a configuration file.

        The configuration file is by default saved to
        ``~/.setlyze/setlyze.cfg``.
        """
        parser = ConfigParser.SafeConfigParser()
        # The configurations that need to be saved to a configuration file.
        configs = {
            'general': ('alpha-level','test-repeats','concurrent-processes')
        }
        # Set the configurations.
        for section in configs:
            parser.add_section(section)
            for option in configs[section]:
                parser.set(section, option, str(self.get(option)))
        # Check if the data folder exists. If not, create it.
        if not os.path.exists(DATA_PATH):
            os.mkdir(DATA_PATH)
        # Create new configurations file.
        f = open(CONF_FILE, 'w')
        parser.write(f)
        f.close()

    def set(self, key, value):
        """Set the configuration with name `key` to `value`."""
        if key not in self._conf:
            raise KeyError("'%s' is not a configuration key" % key)
        if key == 'data-source':
            self.set_data_source(value)
            return
        self._conf[key] = value

    def set_data_source(self, source):
        """Set the configuration with name ``data-source`` to `source`.

        Possible values for `source` are ``setl-database`` and
        ``data-files``. The value of this configuration tells the
        application where to look for SETL data. This is especially used
        by the database module.

        If an unknown data source is given, an error is printed.
        """
        if source in ("setl-database", "data-files"):
            # Set the new data source.
            self._conf['data-source'] = source
            # A new database file must be created when the data source has
            # changed.
            self.set('make-new-db', True)
        else:
            raise ValueError("Encountered unknown data source '%s'" % source)

    def get(self, key):
        """Return the value for the configuration with name `key`."""
        if key not in self._conf:
            raise KeyError("'%s' is not a configuration key" % key)
        return self._conf.get(key)

# Create an instance of ConfigManager. This instance is only created once,
# upon the first import. Subsequent imports of this module will use the
# same instance. So this instance is accessible between all modules.
cfg = ConfigManager()
