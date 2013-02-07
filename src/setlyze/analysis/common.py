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
import setlyze.report

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"


class Pool(threading.Thread):
    """Primitive thread pool."""

    def __init__(self, size, pdialog_handler=None):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.queue = Queue.Queue()
        self.threads = []

        # Spawn threads, but don't start them yet.
        for i in range(size):
            t = Worker(self.queue, pdialog_handler)
            self.threads.append(t)

    def add_job(self, func, *args, **kargs):
        """Add a job to the queue."""
        self.queue.put((func, args, kargs))

    def run(self):
        """Start all threads.

        Only call this method after calling :meth:`add_job` at least once.
        The signal ``thread-pool-finished`` is sent when all threads have
        finished.
        """
        for thread in self.threads:
            thread.start()
        # Wait for all threads to finish.
        for thread in self.threads:
            thread.join()
        # Send the signal that all threads have finished.
        gobject.idle_add(setlyze.std.sender.emit, 'thread-pool-finished')

    def stop(self, block=True):
        """Stop all threads.

        Default for `block` is True, causing this function to block until
        all threads have been stopped.
        """
        logging.debug("%s: Received stop signal" % self)
        self._stop.set()
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

    def stopped(self):
        """Return True if the pool was stopped forcefully."""
        return self._stop.isSet()

class Worker(threading.Thread):
    """Worker thread for usage in a thread pool.

    This class can be used to create a number of worker threads which will each
    execute jobs from a queue (instance of :py:class:`Queue.Queue`). Each job
    is a tuple with function/class pointer followed by arguments (in that
    order). Each instance of this thread will obtain a job from the queue and
    execute the function/instantiate the class that was passed (the first
    item in the tuple) with the arguments from the tuple.

    An instance of this class will exit immediately when the queue is empty.
    """

    def __init__(self, queue, pdialog_handler = None):
        threading.Thread.__init__(self)
        self.queue = queue
        self.pdialog_handler = pdialog_handler
        self.thread = None

    def run(self):
        """Execute jobs in the queue."""
        while True:
            # Get a job from the queue.
            try:
                func, args, kargs = self.queue.get(False)
            except:
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

            # Emit the signal that a job was completed. Send the results along
            # with the signal.
            if not self.thread.result.is_empty():
                gobject.idle_add(setlyze.std.sender.emit, 'thread-pool-job-completed', self.thread.result)

            # Signal to queue that the job is done.
            self.queue.task_done()

    def stop(self):
        """Stop the current job."""
        logging.debug("%s: Received stop signal" % self)
        try:
            self.thread.stop()
        except AttributeError:
            return

class PrepareAnalysis(object):
    """Super class for analysis Begin classes."""

    def __init__(self):
        self.lock = threading.Lock()
        self.thread_pool_size = 1
        self.signal_handlers = {}
        self.pdialog = None
        self.pool = None
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.results = []

    def in_batch_mode(self):
        """Return True if we are in batch mode."""
        return self.__class__.__name__ == 'BeginBatch'

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
        """
        # Destroy the progress dialog.
        if self.pdialog:
            self.pdialog.destroy()

        # Stop all analysis jobs.
        if self.pool:
            self.pool.stop()

        # Show an info dialog.
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis canceled")
        dialog.format_secondary_text(setlyze.locale.text('cancel-pressed'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def on_analysis_closed(self, sender=None, data=None):
        """Show the main window and unset the signal handler."""

        # This causes the main window to show.
        setlyze.std.sender.emit('analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.unset_signal_handlers()

    def on_thread_pool_job_completed(self, sender, result):
        """Save the results of individual thread pool jobs."""
        self.results.append(result)

    def on_thread_pool_finished(self, sender=None):
        """Display the results.

        If there are no results, return to the main window.
        """
        # Check if there are any reports to display. If not, leave.
        if len(self.results) == 0:
            self.on_analysis_closed()
            return
        # Display the reports.
        for report in self.results:
            setlyze.gui.Report(report)

class AnalysisWorker(threading.Thread):
    """Super class for Analysis classes."""

    def __init__(self, lock):
        super(AnalysisWorker, self).__init__()

        self._stop = threading.Event()
        self._lock = lock
        self.pdialog_handler = None
        self.result = setlyze.report.Report()
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.dbfile = setlyze.config.cfg.get('db-file')

    def stop(self):
        """Stop this thread."""
        logging.debug("%s: Received stop signal" % self)
        self._stop.set()

    def stopped(self):
        """Return True if this thread needs to be stopped."""
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
