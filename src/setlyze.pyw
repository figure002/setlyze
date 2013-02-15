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

"""This is SETLyze's executable. Run this script to start SETLyze."""

import sys
import logging
import warnings
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

# Allow only the main thread to touch the GUI (GTK) part, while letting other
# threads do background work. For this to work, first call gobject.threads_init()
# at applicaiton initialization. Then you launch your threads normally, but
# make sure the threads never do any GUI task directly. Instead, you use
# gobject.idle_add() to schedule GUI tasks to executed in the main thread.
gobject.threads_init()

# The following is a workaround for the executable created with py2exe. This
# prevents SETLyze from exiting with an error message when warning messages
# occured.
if setlyze.std.we_are_frozen():
    warnings.simplefilter('ignore')

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__credits__ = ["Jonathan den Boer",
    "Serrano Pereira <serrano.pereira@gmail.com>",
    "Adam van Adrichem <a.v.adrichem@gmail.com>",
    "Fedde Schaeffer <fedde.schaeffer@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"

batch_select_window = None

def main():
    # Registers adapt_str to convert the custom Python type into one of
    # SQLite's supported types. This adds support for Unicode strings.
    sqlite.register_adapter(str, adapt_str)

    # Show all log messages of type INFO (unless we are frozen by py2exe).
    if setlyze.std.we_are_frozen():
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    # Handle the application signals.
    handle_application_signals()

    # Create a log message.
    logging.info("SETLyze %s started." % __version__)

    # Display the main window.
    setlyze.gui.SelectAnalysis()

    # Instantiate other windows.
    global batch_select_window
    batch_select_window = setlyze.gui.SelectBatchAnalysis()

    # Start the GTK main loop, which continuously checks for newly
    # generated events.
    gtk.main()

    # Terminate the application once the main GTK loop is terminated.
    sys.exit()

def handle_application_signals():
    """Respond to signals emitted by the application."""

    # The user wants to start an analysis.
    setlyze.std.sender.connect('on-start-analysis', on_start_analysis)

def on_start_analysis(sender, analysis, data=None):
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
        setlyze.analysis.batch.Begin(batch_select_window)

    return False

def adapt_str(string):
    """Convert the custom Python type into one of SQLite's supported types.
    This allows Unicode characters to be saved to the local database.
    """
    return string.decode("utf-8")

if __name__ == "__main__":
    main()
