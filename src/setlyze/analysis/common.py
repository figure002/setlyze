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

import logging
import threading
import Queue

import gobject
import pygtk
pygtk.require('2.0')
import gtk

import setlyze.config
import setlyze.std

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

# The timeout in seconds a queue get should block when no item are available in
# a queue.
QUEUE_GET_TIMEOUT = 1

class PrepareAnalysis(object):
    """Super class for analysis Begin classes."""

    def __init__(self):
        self.lock = threading.Lock()
        self.queue = Queue.Queue()
        self.threads = []
        self.signal_handlers = {}
        self.pdialog = None

    def stop_all_threads(self, block=True):
        """Exit all analysis threads.

        Default for `block` is True, causing this function to block until all
        threads have been stopped.
        """
        # Clear the job queue.
        with self.queue.mutex:
            self.queue.queue.clear()
        # Stop all threads.
        for thread in self.threads:
            thread.stop()
        # Wait for all threads to stop.
        if block:
            for thread in self.threads:
                thread.join()

    def unset_signal_handlers(self):
        """Disconnect all signal connections with signal handlers
        created by this analysis.
        """
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def on_cancel_button(self, sender):
        """Callback function for the Cancel button.

        * Close the progress dialog.
        * Stop the worker processes.
        * Show an info dialog.
        * Wrap it up and leave.
        """
        # Destroy the progress dialog.
        if self.pdialog:
            self.pdialog.destroy()

        # Stop all analysis threads.
        self.stop_all_threads()

        # Show an info dialog.
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis canceled")
        dialog.format_secondary_text(setlyze.locale.text('cancel-pressed'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Go back to the main window.
        self.on_analysis_closed()

    def on_analysis_closed(self, sender=None, data=None):
        """Show the main window and unset the signal handler."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.unset_signal_handlers()

    def add_job(self, func, *args, **kargs):
        """Add a job to the queue."""
        self.queue.put((func, args, kargs))

class Worker(threading.Thread):
    """Worker thread for usage in a thread pool.

    This class can be used to create a number of worker threads which will each
    execute jobs from a queue (instance of :py:class:`Queue.Queue`). Each job
    is a tuple with function/class pointer followed by arguments (in that
    order). Each instance of this thread will obtain a job from the queue and
    execute the function/instantiate the class that was passed (the first
    item in the tuple) with the arguments from the tuple.

    An instance of this class will wait for a maximum of `QUEUE_GET_TIMEOUT`
    seconds when the queue is empty, after which it will exit.
    """

    def __init__(self, queue, pdialog_handler = None):
        threading.Thread.__init__(self)
        self.queue = queue
        self.pdialog_handler = pdialog_handler
        self.thread = None

    def stop(self):
        """Stop the current job."""
        try:
            self.thread.stop()
        except AttributeError:
            return

    def run(self):
        """Execute jobs in the queue."""
        while True:
            # Get a job from the queue.
            try:
                func, args, kargs = self.queue.get(True, QUEUE_GET_TIMEOUT)
            except:
                # Exit if no jobs are found for `QUEUE_GET_TIMEOUT` seconds.
                logging.info("Worker %d got bored and quit" % self.ident)
                return

            # Execute the job.
            self.thread = func(*args, **kargs)

            # Set the progress dialog handler if one is set.
            if self.pdialog_handler:
                self.thread.set_pdialog_handler(self.pdialog_handler)

            # Start the analysis.
            self.thread.start()
            self.thread.join()

            # Signal to queue that the job is done.
            self.queue.task_done()

class AnalysisWorker(threading.Thread):
    """Super class for Analysis classes."""

    def __init__(self, lock):
        super(AnalysisWorker, self).__init__()

        self._stop = threading.Event()
        self._lock = lock
        self.pdialog_handler = None
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.dbfile = setlyze.config.cfg.get('db-file')

    def __del__(self):
        # Release the lock to shared resources.
        try:
            self._lock.release()
        except:
            return

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
