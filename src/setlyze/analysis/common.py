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

import os
import logging
import multiprocessing
import threading
import time

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
__version__ = "0.3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

def calculate(cls, args):
    """Create an instance of class `cls` and call its run() method.

    Arguments `args` are unpacked and passed to `cls` when it is instantiated.
    Returns the result returned by `cls`.run().
    """
    obj = cls(*args)
    result = obj.run()
    return result

def calculatestar(args):
    """Unpack the argument `args` and pass them to :meth:`calculate`.

    Argument `args` must be a list of two items: a class definition and a list
    of arguments for instantiating the class. Method :meth:`calculate` will
    take care of instantiating the class and passing the arguments.

    Returns the result returned by :meth:`calculate`.
    """
    return calculate(*args)

class Pool(threading.Thread):
    """Create a pool of worker processes.

    An instance of this class provides the convenient :meth:`stop` method for
    stopping all the workers in the pool in an elegant manner. This avoids
    having to call :py:meth:`multiprocessing.Pool.terminate`. A pool instance
    emits the ``pool-finished`` signal once all workers are terminated.

        .. note::

           This class is currently not in use because it is unstable.
           Use of :py:class:`multiprocessing.Pool` is preferred.
   """

    def __init__(self, size=None):
        """Spawn workers.

        Argument `size` is an integer defining the number of workers that
        will be spawned.
        """
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.manager = multiprocessing.Manager()
        self.task_queue = self.manager.Queue()
        self.done_queue = self.manager.Queue()
        self.progress_queue = self.manager.Queue()
        self.workers = []

        # If no pool size is set, default to the number of CPUs.
        assert (isinstance(size, int) and size >= 1) or size is None, \
            "Pool size must me an integer"
        if size is None:
            try:
                size = multiprocessing.cpu_count()
            except:
                size = 1

        # Spawn workers, but don't start them yet.
        for i in range(size):
            w = Worker(self.task_queue, self.done_queue)
            self.workers.append(w)

    def add_task(self, func, *args, **kargs):
        """Add a task to the task queue."""
        self.task_queue.put((func, args, kargs))

    def run(self):
        """Start all workers.

        Only call this method after calling :meth:`add_task` at least once.
        The signal ``pool-finished`` is sent when all workers have finished.
        """
        for w in self.workers:
            w.start()
        # Wait for all workers to finish.
        for w in self.workers:
            w.join()
        # Send the signal that all workers have finished.
        gobject.idle_add(setlyze.std.sender.emit, 'pool-finished', self.done_queue)

    def stop(self, block=True):
        """Stop all workers.

        Default for `block` is True, causing this function to block until
        all workers have been stopped.
        """
        logging.debug("%s: Received stop signal" % self)
        self._stop.set()
        # Stop all workers.
        for w in self.workers:
            w.stop()
        # Wait for all workers to stop.
        if block:
            for w in self.workers:
                w.join()

    def stopped(self):
        """Return True if the pool was stopped."""
        return self._stop.isSet()

class Worker(multiprocessing.Process):
    """Worker process instantiated by :class:`Pool`.

    This class can be used to create a number of workers which will each
    execute tasks from a queue (instance of :py:class:`multiprocessing.Queue`).
    Each task is a tuple with a function followed by arguments and keyword args
    for that function ``(func, *args, **kwargs)``. Each worker will obtain a task
    from the queue and execute the function with the arguments. Results from
    individual tasks are passed to a results queue.

    An instance of this class will terminate immediately when the task queue is
    empty.
    """

    def __init__(self, input, output):
        """Sets the `input` and `output` queue.

        Both `input` and `output` should be different instances of
        :py:class:`multiprocessing.Queue`. Queue `input` will be used to obtain
        tasks from, queue `output` will be used to pass task results to.
        """
        multiprocessing.Process.__init__(self)
        self.input = input
        self.output = output
        self.active = True

    def run(self):
        """Execute tasks in the queue."""
        while self.active:
            # Try to get a task from the queue. If the queue is empty, terminate.
            try:
                func, args, kargs = self.input.get(False)
            except:
                logging.debug("Worker %s got bored and quit" % os.getpid())
                return
            # Execute the task.
            result = func(*args, **kargs)
            # Pass the task result to the output queue.
            self.output.put(result)

    def stop(self):
        """Stop executing tasks.

        You still have to wait for an active task to finish.
        """
        logging.debug("%s: Received stop signal" % self)
        self.active = False

class ProcessGateway(threading.Thread):
    """Execute child process tasks in the main process.

    An instance of this class provides a public attribute `queue` which can be
    passed to child processes. Child processes can use it to submit tasks for
    execution in the main process. This is to overcome the restriction of
    letting child processes communicate with the main process. An instance of
    this class runs in the main process and will execute tasks submitted to
    `queue` by child processes.

    When an analysis is instantiated, the execute queue `queue` is passed to
    it. Each ``Analysis`` class inherits the method
    :meth:`AnalysisWorker.exec_task` which is used to submit execution tasks
    to this queue. Thus an analysis process can submit tasks as follows::

        self.exec_task('task_string'[, arguments, ..])

    For example, to increase the progress bar with one step and setting an
    optional progress string::

        self.exec_task('progress.increase', "Performing statistical tests...")

    This results in a call to attribute `pdialog_handler` which is an instance
    of :class:`~setlyze.std.ProgressDialogHandler`. The task string for
    accessing the progress dialog handler has the format ``progress.method``,
    which translates to a call to ``self.pdialog_handler.method()`` from this
    class. Thus the above example translates to::

        self.pdialog_handler.increase("Performing statistical tests...")

    This mechanism can also be used to emit application signals. For example::

        self.exec_task('emit', 'analysis-aborted', "Not enough data for this species")

    Translates to::

        gobject.idle_add(setlyze.std.sender.emit, 'analysis-aborted', "Not enough data for this species")

    Use method :meth:`set_pdialog_handler` to set the progress dialog handler
    if progress dialogs need to be updated by child processes. Typical usage of
    this class looks like this::

        pdialog = setlyze.gui.ProgressDialog(title="Performing analysis",
            description="Running the analysis...")
        pdialog_handler = setlyze.std.ProgressDialogHandler(pdialog)
        pdialog_handler.set_total_steps(10)

        gw = setlyze.analysis.common.ProcessGateway()
        gw.set_pdialog_handler(pdialog_handler)
        gw.start()

        pool = multiprocessing.Pool()
        pool.apply_async(Analysis, locations, species, gw.queue)
    """
    def __init__(self, timeout=5):
        """Create an instance of an execute queue.

        An instance of this class will constantly check for new execute tasks
        in the queue. If it doesn't find a task in the queue for `timeout`
        seconds, the instance of this class will terminate.
        """
        threading.Thread.__init__(self)
        self.manager = multiprocessing.Manager()
        self.queue = self.manager.Queue()
        self.pdialog_handler = None
        self.timeout = timeout

    def __str__(self):
        return self.__class__.__name__

    def run(self):
        """Constantly get and execute tasks from the queue."""
        while True:
            try:
                task, args, kargs = self.queue.get(True, self.timeout)
            except:
                logging.debug("%s quitted" % self)
                return
            if task == 'emit':
                # Emit a signal.
                gobject.idle_add(setlyze.std.sender.emit, *args)
            elif task.startswith('progress.'):
                # Call a ProgressDialogHandler method. The value of `task`
                # has the format `progress.method`, which translates to
                # `self.pdialog_handler.method()`.
                if self.pdialog_handler:
                    task = task.split('.').pop()
                    getattr(self.pdialog_handler, task)(*args, **kargs)

    def set_pdialog_handler(self, handler):
        """Set a progress dialog handler `handler`.

        Argument `handler` must be an instance of
        :class:`~setlyze.std.ProgressDialogHandler`.
        """
        if not isinstance(handler, setlyze.std.ProgressDialogHandler):
            raise ValueError("Argument is not an instance of ProgressDialogHandler")
        self.pdialog_handler = handler

    def get_queue(self):
        """Returns the execute queue."""
        return self.queue

class PrepareAnalysis(object):
    """Super class for analysis Begin classes."""

    def __init__(self):
        self.signal_handlers = {}
        self.pdialog = None
        self.pdialog_handler = None
        self.pool = None
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.save_individual_results = False
        self.start_time = None
        self.elapsed_time = None
        self.results = []
        self.save_individual_results = setlyze.config.cfg.get('save-batch-job-results')
        self.save_path = setlyze.config.cfg.get('job-results-save-path')
        self.report_prefix = "report_"

    def in_batch_mode(self):
        """Return True if we are in batch mode."""
        return self.__class__.__name__ == 'BeginBatch'

    def unset_signal_handlers(self, sender=None, data=None):
        """Disconnect all signal connections with signal handlers
        created by this analysis.
        """
        for handler in self.signal_handlers.values():
            if handler:
                setlyze.std.sender.disconnect(handler)

    def on_analysis_aborted(self, sender, reason):
        """Display an information dialog with the reason for the abortion."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis aborted")
        dialog.format_secondary_text("The analysis was aborted for the "
            "following reason:\n\n%s" % reason)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

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
            # TODO: Find a more elegant way to stop processes.
            self.pool.terminate()
            self.pool.join()

        # Show an info dialog.
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis canceled")
        dialog.format_secondary_text(setlyze.locale.text('cancel-pressed'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Method on_pool_finished() will not be called when calling
        # pool.terminate(), so close manually.
        self.on_analysis_closed()

    def on_analysis_closed(self, sender=None, data=None, timeout=0):
        """Show the main window and unset the signal handler."""
        if timeout:
            time.sleep(timeout)

        # Destroy the progress dialog.
        if self.pdialog:
            gobject.idle_add(self.pdialog.destroy)

        # This causes the main window to show.
        gobject.idle_add(setlyze.std.sender.emit, 'analysis-closed')

        # Make sure all handlers are destroyed when this object is
        # finished. If we don't do this, the same handlers will be
        # created again, resulting in copies of the same handlers, with
        # the result that callback functions are called multiple times.
        self.unset_signal_handlers()

    def on_select_save_path(self, sender, data):
        """Let the user decide whether individual job results should be saved."""
        setlyze.gui.SelectReportSavePath()

    def on_pool_finished(self, results):
        """Display the results in graphical window.

        If there are no results, return to the main window.

        .. note::

           This callback method cannot do any GUI task directly. While this
           works fine on GNU/Linux systems, this causes the GUI to hang on
           Windows.
        """
        # Set the elapsed time if the start time was set.
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            logging.info("Time elapsed: %.2f seconds" % (self.elapsed_time))

        # Set the progress dialog to 100%. This is thread safe.
        if self.pdialog_handler:
            self.pdialog_handler.complete()

        # Only keep the non-empty results.
        results[:] = [r for r in results if r and not r.is_empty()]

        # Check if there are any reports to display. If not, close the
        # analysis after a short timeout. The timeout gives signal handlers
        # a chance to catch any last minute signals from the analysis.
        if len(results) == 0:
            gobject.idle_add(setlyze.std.sender.emit, 'no-results')
            logging.info("No results to show.")
            self.on_analysis_closed(timeout=2)
            return

        # Save reports for the individual analyses if desired.
        if self.in_batch_mode() and self.save_individual_results:
            self.export_reports(results, self.save_path, self.report_prefix)

        # Let the signal handler handle the results.
        gobject.idle_add(setlyze.std.sender.emit, 'pool-finished', results)

    def on_no_results(self, sender=None):
        """Display a message dialog saying that there were no results."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="No results")
        dialog.format_secondary_text(setlyze.locale.text('no-results'))
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def export_reports(self, results, path, prefix=''):
        """Export all reports from the reports list `results`.

        Reports are exported to directory `path`. Argument `prefix` is an
        optional prefix for exported reports.
        """
        if not os.path.isdir(path):
            return

        for result in results:
            species_list = []
            for selection in result.species_selections:
                species_selection = [s for s in selection.values()]
                # In batch mode there should be just one species per selection.
                species = species_selection[0]['name_latin']
                if not species: species = species_selection[0]['name_common']
                species_list.append(species)

            if len(species_list) == 2:
                filename = "%s%s_%s.rst" % (prefix, species_list[0], species_list[1])
            else:
                filename = "%s%s.rst" % (prefix, species_list[0])
            output_dir = os.path.join(path, filename)
            setlyze.report.export(result, output_dir, 'rst')

    def on_display_results(self, sender, results=[]):
        """Display each report in a separate window.

        This is not a good idea for batch mode, in which case it should be
        redefined in the subclass.
        """
        for report in results:
            setlyze.gui.Report(report)

class AnalysisWorker(object):
    """Super class for Analysis classes."""

    def __init__(self, execute_queue=None):
        self._stop = False
        self.db = None
        self.execute_queue = execute_queue
        self.result = setlyze.report.Report()
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.exception = None

    def stop(self):
        """Stop the analysis."""
        logging.debug("%s: Received stop signal" % self)
        self._stop = True

    def stopped(self):
        """Return True if the analysis was stopped."""
        return self._stop

    def exec_task(self, task, *args, **kargs):
        """Add a task to the execute queue.

        Tasks from this queue will be executed by :class:`ProcessGateway` in
        the main process.

        Argument `task` must be a string that is understood by
        :class:`ProcessGateway` and can be followed by arguments for the
        specific task.
        """
        if self.execute_queue:
            self.execute_queue.put((task, args, kargs))

    def on_exit(self):
        """Properly exit the thread.

        Tasks:
        * Close the connection to the database.
        """
        if self.db:
            self.db.conn.close()
