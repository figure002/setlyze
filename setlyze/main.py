#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010-2015, GiMaRIS <info@gimaris.com>
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

from setlyze import __version__, FROZEN
from setlyze.gui import select_analysis
from setlyze.std import sender
from setlyze.analysis import *

# Allow only the main thread to touch the GUI (GTK) part, while letting other
# threads do background work. For this to work, first call
# gobject.threads_init() at applicaiton initialization. Then you launch your
# threads normally, but make sure the threads never do any GUI task directly.
# Instead, you use gobject.idle_add() to schedule GUI tasks to executed in the
# main thread.
gobject.threads_init()

# Prevent SETLyze from printing warning messages when we are frozen by py2exe.
# Py2exe treats printed messages as error messages, causing it to exit with an
# error message.
if FROZEN:
    warnings.simplefilter('ignore')

def main():
    # Allow this script which uses multiprocessing to be frozen to produce a
    # Windows executable.
    if FROZEN:
        multiprocessing.freeze_support()

    # Initilize the logger.
    if FROZEN:
        level = logging.ERROR
    elif sys.flags.debug:
        # Print debug messages if the PYTHONDEBUG env variable is set. Also
        # print debug messages for the multiprocessing module.
        level = logging.DEBUG
        multiprocessing.log_to_stderr(logging.DEBUG)
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format='%(levelname)s %(message)s')

    # Registers adapt_str to convert the custom Python type into one of SQLite's
    # supported types. This adds support for Unicode strings.
    sqlite.register_adapter(str, adapt_str)

    # Set some signal handlers.
    sender.connect('on-start-analysis', on_start_analysis)

    # Create an info message.
    logging.info("SETLyze %s started." % __version__)

    # Display the main window.
    select_analysis.show()

    # Start the GTK main loop.
    gtk.main()

    # Terminate the application once the main GTK loop is terminated.
    sys.exit()

def adapt_str(string):
    """Convert the custom Python type into one of SQLite's supported types.
    This allows Unicode characters to be saved to the local database.
    """
    return string.decode("utf-8")

def on_start_analysis(sender, name):
    """Begin with the selected analysis."""
    if name == 'spot_preference':
        spot_preference.Begin()
    elif name == 'attraction_intra':
        attraction_intra.Begin()
    elif name == 'attraction_inter':
        attraction_inter.Begin()
    elif name == 'relations':
        relations.Begin()
    elif name == 'batch':
        batch.Begin()
    return False

if __name__ == "__main__":
    main()
