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

"""This module contains common classes for analysis modules."""

import threading

import setlyze.config
import setlyze.std

__author__ = ("Serrano Pereira")
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/01"


class PrepareAnalysis(object):
    """Super class for analysis Begin classes."""

    def __init__(self):
        self.lock = threading.Lock()
        self.threads = []
        self.signal_handlers = {}
        self.pdialog_handler = None

    def stop_all_threads(self):
        """Exit all analysis threads."""
        for thread in self.threads:
            thread.stop()

    def unset_signal_handlers(self):
        """Disconnect all signal connections with signal handlers
        created by this analysis.
        """
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def on_analysis_closed(self, sender=None, data=None):
        """Show the main window and unset the signal handler."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.unset_signal_handlers()

class AnalysisWorker(threading.Thread):
    """Super class for analysis Worker classes."""

    def __init__(self, lock):
        super(AnalysisWorker, self).__init__()

        self._stop = threading.Event()
        self._lock = lock
        self.pdialog_handler = None
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.dbfile = setlyze.config.cfg.get('db-file')

    def __del__(self):
        # Release the lock to shared resources.
        if self._lock.locked(): self._lock.release()

    def stop(self):
        """Stop this thread."""
        self._stop.set()

    def stopped(self):
        """Check if this thread needs to be stopped."""
        return self._stop.isSet()

    def set_pdialog_handler(self, handler):
        """Set the progress dialog handler.

        The progress dialog handler is an instance of
        :class:`setlyze.std.ProgressDialogHandler`.
        """
        if not isinstance(handler, setlyze.std.ProgressDialogHandler):
             raise ValueError("Invalid object type passed.")
        self.pdialog_handler = handler

    def set_locations_selection(self, selection):
        """Set the locations selection.

        The locations selection `selection` is a list of integers. Each integer
        is the primary key of the localities table in the database. Only
        species records from the selected locations will be used for the
        analysis.
        """
        self.locations_selection = selection

    def set_species_selection(self, selection):
        """Set the species selection.

        The species selection `selection` is a list of integers. Each integer
        is the primary key of the species table in the database. More than one
        species means that they will be treated as a single species.
        """
        self.species_selection = selection
