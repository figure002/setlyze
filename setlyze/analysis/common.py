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

"""Common classes and routines for analysis modules."""

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
__copyright__ = "Copyright 2010-2013, GiMaRIS"
__license__ = "GPL3"
__version__ = "1.0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/03/12"

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

    Returns whatever :meth:`calculate` returns.
    """
    return calculate(*args)

class Pool(threading.Thread):
    """Create a pool of worker processes.

    The pool size `size` defines the number of workers (instances of
    :class:`Worker`) that will be spawned. If the pool size is not set, it
    defaults to the number of CPUs.

    An instance of this class provides the convenient :meth:`stop` method for
    stopping all the workers in the pool in an elegant manner. This avoids
    having to call :py:meth:`multiprocessing.Pool.terminate`. A pool instance
    emits the ``pool-finished`` signal once all workers are terminated.

        .. note::

           This class is currently not in use because it is unstable.
           Use of :py:class:`multiprocessing.Pool` is preferred. This class is
           kept here because it is fun to experiment with.
   """

    def __init__(self, size=None):
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
    execute tasks from a task queue `input` (instance of
    :py:class:`multiprocessing.Queue`). Each task is a tuple with a function
    followed by arguments and keyword arguments for that function
    ``(func, *args, **kwargs)``. Each worker instance will continuously obtain
    a task from the task queue `input` and execute the function with the
    arguments. Results from individual tasks are passed to the results queue
    `output`. Arguments `input` and `output` must be different instances of
    :py:class:`multiprocessing.Queue`.

    An instance of this class will terminate immediately when the task queue is
    empty.

        .. note::

           This class is currently not in use; see the note for :class:`Pool`.
    """

    def __init__(self, input, output):
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

    An instance of this class will constantly check for new execute tasks
    in the queue. If it doesn't find a task in the queue for `timeout`
    seconds, the instance of this class will terminate.

    When an analysis is instantiated, the execute queue `queue` is passed to
    it. Each :class:`Analysis` class inherits the method
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
    """Super class for analysis :class:`Begin` classes."""

    def __init__(self):
        self.alpha_level = None
        self.areas_definition = None
        self.elapsed_time = None
        self.locations_selection = None
        self.locations_selections = [None,None]
        self.n_repeats = None
        self.pdialog = None
        self.pdialog_handler = None
        self.pool = None
        self.n_processes = None
        self.report_prefix = "report_"
        self.results = []
        self.signal_handlers = {}
        self.start_time = None
        self.species_selection = None
        self.species_selections = [None,None]

        self.set_analysis_options()

    def set_analysis_options(self):
        """Set the user defined analysis options.

        This method uses the :mod:`setlyze.config` module to obtain the values.
        """
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.n_processes = setlyze.config.cfg.get('concurrent-processes')
        self.n_repeats = setlyze.config.cfg.get('test-repeats')

    def get_progress_dialog(self):
        """Return a progress dialog and a handler for the dialog."""
        pd = setlyze.gui.ProgressDialog(title="Performing analysis",
            description="Please stand by while the analysis is running. This "
            "may take a while...")
        handler = setlyze.std.ProgressDialogHandler(pd)
        return (pd, handler)

    def in_batch_mode(self):
        """Return True if we are in batch mode, False otherwise."""
        return self.__class__.__name__ == 'BeginBatch'

    def unset_signal_handlers(self, sender=None, data=None):
        """Disconnect all signal handlers set in attribute `signal_handlers`."""
        for handler in self.signal_handlers.values():
            if handler:
                setlyze.std.sender.disconnect(handler)

    def on_analysis_aborted(self, sender, reason):
        """Display an information dialog with the reason for the abortion.

        This method can be set as a handler for the "analysis-aborted"
        signal. When this signal is emitted, a reason for abortion `reason` is
        returned as a string.
        """
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis aborted")
        dialog.format_secondary_text("The analysis was aborted for the "
            "following reason:\n\n%s" % reason)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def on_cancel_button(self, sender):
        """Cancel the analysis.

        This method can be set as a handler for the "analysis-canceled"
        signal. This signal is emitted when the Cancel button of a progress
        dialog is pressed.

        This method does the following:

        * Close the progress dialog.
        * Stop the worker processes.
        * Show an info dialog.
        """
        # Destroy the progress dialog.
        if self.pdialog:
            self.pdialog.destroy()

        # Stop all workers.
        if self.pool:
            # TODO: Find a more elegant way to stop processes.
            self.pool.terminate()
            self.pool.join()

        # Show an info dialog.
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Analysis canceled")
        dialog.format_secondary_text("Analysis aborted by user.")
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Method on_pool_finished() will not be called when calling
        # pool.terminate(), so close manually.
        self.on_analysis_closed()

    def on_analysis_closed(self, sender=None, data=None, timeout=0):
        """Exit an analysis elegantly.

        This method can be set as a handler for application signals, but this
        is optional.

        After `timeout` seconds, this method closes the progress dialog (if
        any), sends the "analysis-closed" signal, and disconnects any signal
        handlers set in this class.
        """
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

    def on_pool_finished(self, results):
        """Collect the analysis results when a process pool is finished.

        This method can be set as a callback for :py:class:`multiprocessing.Pool`
        methods for which a callback can be set (e.g. :py:meth:`map_async`).

        This method collects the results `results`, calculates the elapsed
        time since the start of the analyses, sets the progress of the progress
        to 100%, strips empty reports from the results, exports the reports
        if set by the user, and finally sends the "pool-finished" signal.
        The stripped results list is sent along with the signal. If there are
        no results (or all reports are empty), emit signal
        "no-results" and close the analysis.

        .. warning::

           This callback method cannot do any GUI task directly. While this
           works fine on GNU/Linux systems, this causes the GUI to hang on
           Windows.
        """
        # Set the elapsed time if the start time was set.
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
            logging.info("Time elapsed: %.2f seconds" % (self.elapsed_time))

        # Set the progress dialog to 100%. Since we are using the progress
        # dialog handler to do this, this is thread safe.
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

        # Save the results locally.
        self.results = results

        # Let the signal handler handle the results.
        gobject.idle_add(setlyze.std.sender.emit, 'pool-finished', results)

    def on_save_individual_reports(self, sender=None):
        """Save reports for the individual analyses."""
        if len(self.results) == 0:
            return

        # Let the user select the output folder.
        chooser = gtk.FileChooserDialog(title="Select Output Folder",
            parent=None,
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK),
            backend=None)
        chooser.set_default_response(gtk.RESPONSE_OK)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            self.export_reports(self.results, chooser.get_filename(), self.report_prefix)
        chooser.destroy()

    def on_no_results(self, sender=None):
        """Display an info dialog saying that there were no results.

        This method is usually set as a handler for the "no-results"
        signal.
        """
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="No results")
        dialog.format_secondary_text("The analysis did not return any results, "
            "most likely because there wasn't enough data for the analysis.")
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

    def export_reports(self, results, path, prefix=''):
        """Export all reports from a list of report objects `results`.

        Reports are exported to directory `path`. Argument `prefix` is an
        optional prefix for exported reports. File names are created in the
        format ``[prefix]speciesA[_speciesB].rst``.
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
            # Remove unwanted characters from the filename.
            filename = setlyze.std.slugify(filename)
            # Export the report.
            output_dir = os.path.join(path, filename)
            setlyze.report.export(result, output_dir, 'rst')

    def on_display_results(self, sender, results=[]):
        """Display each report from the list `results` in a report window.

        This method can be set as a handler for the "pool-finished" signal.
        The signal should have a single argument, a list of report objects
        `results`. This signal can be emitted by
        :meth:`~setlyze.analysis.common.PrepareAnalysis.on_pool_finished`.

        This is not a good handler in batch mode because it will open as many
        report windows as there are reports in `results`. So in batch mode
        this method should be redefined in the subclass.
        """
        for report in results:
            setlyze.gui.Report(report)

class AnalysisWorker(object):
    """Super class for :class:`Analysis` classes."""

    def __init__(self, execute_queue=None):
        self._stop = False
        self.alpha_level = setlyze.config.cfg.get('alpha-level')
        self.db = None
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.execute_queue = execute_queue
        self.n_repeats = setlyze.config.cfg.get('test-repeats')
        self.result = setlyze.report.Report()

    def stop(self):
        """Stop the analysis."""
        logging.debug("%s: Received stop signal" % self)
        self._stop = True

    def stopped(self):
        """Return True if the analysis was stopped, False otherwise."""
        return self._stop

    def exec_task(self, task, *args, **kargs):
        """Add a task to the execute queue.

        Tasks from this queue will be executed by :class:`ProcessGateway` in
        the main process.

        Argument `task` must be a string that is understood by
        :class:`ProcessGateway` and can be followed by arguments for the
        specific task. See :class:`ProcessGateway` for details.
        """
        if self.execute_queue:
            self.execute_queue.put((task, args, kargs))

    def on_exit(self):
        """Perform tasks that need to be done before exiting an analysis.

        Tasks:

        * Close the connection to the database.
        """
        if self.db:
            self.db.conn.close()
