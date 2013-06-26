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

"""This is SETLyze's executable. Run this script to start SETLyze."""

import sys
import logging
import warnings
import multiprocessing
from sqlite3 import dbapi2 as sqlite

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import setlyze.std
import setlyze.gui
import setlyze.analysis.spot_preference
import setlyze.analysis.attraction_intra
import setlyze.analysis.attraction_inter
import setlyze.analysis.relations
import setlyze.analysis.batch

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010-2013, GiMaRIS"
__credits__ = ["Jonathan den Boer",
    "Serrano Pereira <serrano.pereira@gmail.com>",
    "Adam van Adrichem <a.v.adrichem@gmail.com>",
    "Fedde Schaeffer <fedde.schaeffer@gmail.com>"]
__license__ = "GPL3"
__version__ = "1.0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/24"

# Allow only the main thread to touch the GUI (GTK) part, while letting other
# threads do background work. For this to work, first call gobject.threads_init()
# at applicaiton initialization. Then you launch your threads normally, but
# make sure the threads never do any GUI task directly. Instead, you use
# gobject.idle_add() to schedule GUI tasks to executed in the main thread.
gobject.threads_init()

# Prevent SETLyze from printing warning messages when we are frozen by py2exe.
# Py2exe treats printed messages as error messages, causing it to exit with an
# error message.
if setlyze.std.we_are_frozen():
    warnings.simplefilter('ignore')

def main():
    # Allow this script which uses multiprocessing to be frozen to produce a
    # Windows executable.
    multiprocessing.freeze_support()

    # Only print error messages if we are frozen (i.e. by py2exe).
    if setlyze.std.we_are_frozen():
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s %(message)s')
    # Print debug messages if the -d flag is set for the Python interpreter.
    elif sys.flags.debug:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s %(message)s')
        # Also print debug messages for the multiprocessing module.
        logger = multiprocessing.log_to_stderr(logging.DEBUG)
    # Otherwise just show log messages of type INFO.
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    # Registers adapt_str to convert the custom Python type into one of
    # SQLite's supported types. This adds support for Unicode strings.
    sqlite.register_adapter(str, adapt_str)

    # Set some signal handlers.
    setlyze.std.sender.connect('on-start-analysis', on_start_analysis)

    # Create an info message.
    logging.info("SETLyze %s started." % __version__)

    # Display the main window.
    setlyze.gui.select_analysis.show()

    # Start the GTK main loop, which continuously checks for newly
    # generated events.
    gtk.main()

    # Terminate the application once the main GTK loop is terminated.
    sys.exit()

def adapt_str(string):
    """Convert the custom Python type into one of SQLite's supported types.
    This allows Unicode characters to be saved to the local database.
    """
    return string.decode("utf-8")

def on_start_analysis(sender, analysis):
    """Begin with the selected analysis."""
    if analysis == 'spot_preference':
        setlyze.analysis.spot_preference.Begin()
    elif analysis == 'attraction_intra':
        setlyze.analysis.attraction_intra.Begin()
    elif analysis == 'attraction_inter':
        setlyze.analysis.attraction_inter.Begin()
    elif analysis == 'relations':
        setlyze.analysis.relations.Begin()
    elif analysis == 'batch':
        setlyze.analysis.batch.Begin()
    return False

if __name__ == "__main__":
    main()
