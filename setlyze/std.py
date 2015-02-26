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

"""This module provides standard functions and classes. All functions and
classes that don't belong in any of the other modules are placed here.
"""

import sys
import os
import math
import itertools
import random
import re
import time
import unicodedata

import gobject
import pkg_resources

from setlyze import FROZEN
import setlyze.config

def module_path():
    """Return nodule path even if we are frozen using py2exe."""
    if FROZEN:
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

def resource_filename(resource_name):
    """Return file path for package resource."""
    if FROZEN:
        return os.path.join(module_path(), resource_name)
    return pkg_resources.resource_filename(__name__, resource_name)

def seconds_to_hms(seconds):
    """Returns a duration in the format hours:minutes:seconds.

    Duration `seconds` must be an integer representing seconds. Returns a
    string in the format hours:minutes:seconds.
    """
    seconds = int(seconds)
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    return "%02d:%02d:%02d" % (hours, minutes, seconds)

def make_remarks(results, attributes):
    """Return a remarks string that contains a summary of the results
    and attributes of a statistical test.
    """
    remarks = []

    # Decide which conclusions to use based on the attributes.
    if 'groups' in attributes:
        if attributes['groups'] in ('areas'):
            conclusions = ('Rejection','Preference')
        elif attributes['groups'] in ('ratios','spots'):
            conclusions = ('Attraction','Repulsion')
    else:
        conclusions = ('Attraction','Repulsion')

    if 'p_value' in results:
        try:
            significant = is_significant(results['p_value'], setlyze.config.cfg.get('alpha-level'))
        except ValueError:
            significant = False

        if significant:
            remarks.append("Significant")

            # If significant, also add attraction/repulsion.
            if 'mean_observed' in results and 'mean_expected' in results:
                if results['mean_observed'] < results['mean_expected']:
                    remarks.append(conclusions[0])
                else:
                    remarks.append(conclusions[1])
        else:
            remarks.append("Not significant")

        if math.isnan(results['p_value']):
            pass
        elif results['p_value'] < 0.001:
            remarks.append("P < 0.001")
        elif results['p_value'] < 0.01:
            remarks.append("P < 0.01")
        elif results['p_value'] < 0.05:
            remarks.append("P < 0.05")
        else:
            remarks.append("P > 0.05")

    if 'n_values' in results:
        if results['n_values'] > 20:
            remarks.append("n > 20")
        else:
            remarks.append("n < 20")

    remarks = "; ".join(remarks)
    return remarks

def remove_items_from_list(a,b):
    """Remove the items in list `b` from list `a`."""
    for x in b:
        try:
            a.remove(x)
        except:
            pass

def slugify(value):
    """Normalizes string and removes non-alpha characters."""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s.-]', '-', value))
    return value

def distance_frequency(x, method):
    if method == 'intra':
        frequencies = {
            1: 0,
            1.41: 0,
            2: 0,
            2.24: 0,
            2.83: 0,
            3: 0,
            3.16: 0,
            3.61: 0,
            4: 0,
            4.12: 0,
            4.24: 0,
            4.47: 0,
            5: 0,
            5.66: 0
            }
    elif method == 'inter':
        frequencies = {
            0: 0,
            1: 0,
            1.41: 0,
            2: 0,
            2.24: 0,
            2.83: 0,
            3: 0,
            3.16: 0,
            3.61: 0,
            4: 0,
            4.12: 0,
            4.24: 0,
            4.47: 0,
            5: 0,
            5.66: 0
            }
    else:
        raise ValueError("Unknown method '%s'." % method)

    for dist in x:
        if dist not in frequencies:
            raise ValueError("Unknown spot distance '%s'" % dist)
        else:
            frequencies[dist] += 1
    return frequencies

def uniqify(seq):
    """Remove all duplicates from a list."""
    return {}.fromkeys(seq).keys()

def median(values):
    """Return the median of a series of numbers."""
    values = sorted(values)
    count = len(values)

    if count % 2 == 1:
        return values[(count+1)/2-1]
    else:
        lower = values[count/2-1]
        upper = values[count/2]
        return (float(lower + upper)) / 2

def distance(p1, p2):
    """Use the Pythagorean theorem to calculate the distance between
    two spots.
    """
    val = math.sqrt(p1**2 + p2**2)

    # Round the value to the second decimal. High precision is useless
    # for spot distances and takes too much space in the local database.
    val = round(val, 2)

    return val

def get_spot_combinations_from_record(record1, record2=None):
    """Return all possible positive spot combinations for `record1` or
    if both are provided, between `record1` and `record2`. Each record
    must be a sequence of 25 spot booleans.

    This function returns an iterable object, which returns the
    combinations as tuples with two items. Each item in the tuple is the
    spot number of a positive spot.

    If just `record1` was provided, return all possible positive spot
    combinations within this record. If both `record1` and `record2` are
    given, return all possible positive spot combinations between the
    the two records. If no combinations are possible (i.e. not enough
    positive spots), the iterable object returns nothing.

    An example with one record

        >>> import setlyze.std
        >>> record = (4567,1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
        >>> combos = setlyze.std.get_spot_combinations_from_record(record[1:])
        >>> for spot1,spot2 in combos:
        ...     print spot1,spot2
        ...
        1 2
        1 5
        1 15
        2 5
        2 15
        5 15

    An example with two records

        >>> import setlyze.std
        >>> record1 = (4567,1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
        >>> record2 = (4538,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1)
        >>> combos = setlyze.std.get_spot_combinations_from_record(record1[1:], record2[1:])
        >>> for spot1,spot2 in combos:
        ...     print spot1,spot2
        ...
        1 3
        1 25
        2 3
        2 25
        5 3
        5 25
        15 3
        15 25

    """
    spots1 = get_spots_from_record(record1)

    if not record2:
        # Create a generator with all the possible positive spot
        # combinations within a record.
        try:
            combos = itertools.combinations(spots1,2)
        except:
            # In Python 2.6, itertools.combinations() will raise an exception
            # if `iterable` has less than two items.
            combos = []
    else:
        spots2 = get_spots_from_record(record2)
        # Create a generator with the Cartesian product of the
        # positive spots in two records.
        combos = itertools.product(spots1,spots2)

    # Return the generator that contains all combinations.
    return combos

def get_spots_from_record(record):
    """Return a list containing all spot numbers of the positive spots
    from `record`, a sequence of 25 spot booleans.

    A simple usage example

        >>> import setlyze.std
        >>> record = (1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0)
        >>> print setlyze.std.get_spots_from_record(record)
        [1, 2, 5, 15]
    """
    spots = []
    for i, spot in enumerate(record, start=1):
        if spot:
            spots.append(i)
    return spots

def get_spot_coordinate(spot_num):
    """Return a tuple ``(row,col)`` representing on which row and column
    a spot with number `spot_num` is located on a 5x5 SETL plate.
    The possible values for `spot_num` are integers from 1 to 25.

    If this is not clear, picture this 5x5 SETL plate and compare it
    with the examples below:

    +---+---+---+---+---+
    | 1 | 2 | 3 | 4 | 5 |
    +---+---+---+---+---+
    | 6 | 7 | 8 | 9 | 10|
    +---+---+---+---+---+
    | 11| 12| 13| 14| 15|
    +---+---+---+---+---+
    | 16| 17| 18| 19| 20|
    +---+---+---+---+---+
    | 21| 22| 23| 24| 25|
    +---+---+---+---+---+

    Some examples:

        >>> import setlyze.std
        >>> setlyze.std.get_spot_coordinate(1)
        (1, 1)
        >>> setlyze.std.get_spot_coordinate(5)
        (1, 5)
        >>> setlyze.std.get_spot_coordinate(14)
        (3, 4)
        >>> setlyze.std.get_spot_coordinate(24)
        (5, 4)
    """
    if not 1 <= spot_num <= 25:
        raise ValueError("The value for 'spot_num' must be an integer from 1 to "
            "25. Instead got '%s'" % spot_num)

    rows = [(1,2,3,4,5),
            (6,7,8,9,10),
            (11,12,13,14,15),
            (16,17,18,19,20),
            (21,22,23,24,25)]

    cols = [(1,6,11,16,21),
            (2,7,12,17,22),
            (3,8,13,18,23),
            (4,9,14,19,24),
            (5,10,15,20,25)]

    # Figure out the row number of the spot number.
    for row_num,row in enumerate(rows, start=1):
        if spot_num in row:
            row = row_num
            break
    # Figure out the column number of the spot number.
    for col_num,col in enumerate(cols, start=1):
        if spot_num in col:
            col = col_num
            break

    return (row,col)

def get_spot_position_difference(s1, s2):
    """Return a tuple ``(h,v)`` containing the horizontal and vertical
    difference (delta x and y) between spots `s1` and `s2`. `s1` and
    `s2` are spot numbers with possible values from 1 to 25.

    Picture a 5x5 grid with spots numbered from 1 to 25:

    +---+---+---+---+---+
    | 1 | 2 | 3 | 4 | 5 |
    +---+---+---+---+---+
    | 6 | 7 | 8 | 9 | 10|
    +---+---+---+---+---+
    | 11| 12| 13| 14| 15|
    +---+---+---+---+---+
    | 16| 17| 18| 19| 20|
    +---+---+---+---+---+
    | 21| 22| 23| 24| 25|
    +---+---+---+---+---+

    If you got two spot numbers that are right next to eachother (say 1
    and 2), the horizontal difference would be 1, and the vertical
    difference 0. A few more examples:

        >>> print setlyze.std.get_spot_position_difference(3,3)
        (0, 0)
        >>> print setlyze.std.get_spot_position_difference(1,2)
        (1, 0)
        >>> print setlyze.std.get_spot_position_difference(3,5)
        (2, 0)
        >>> print setlyze.std.get_spot_position_difference(6,11)
        (0, 1)
        >>> print setlyze.std.get_spot_position_difference(9,25)
        (1, 3)
        >>> print setlyze.std.get_spot_position_difference(1,25)
        (4, 4)
    """

    # Calculate the coordinates for both spots.
    s1 = get_spot_coordinate(s1)
    s2 = get_spot_coordinate(s2)

    # Calculate the vertical and horizontal difference between the spot
    # coordinates.
    v = abs(s1[0]-s2[0])
    h = abs(s1[1]-s2[1])

    return (h,v)

def get_random_for_plate(n):
    """Return a `n` length list of random integers with a range from 1
    to 25. So naturally `n` can have a value from 0 to 25. The list of
    integers returned represents random selected spots from a 25 spots
    SETL plate.

    We make use of the :py:meth:`random.sample` function from the Python
    standard library. As described in the Python documentation, this
    function is bound to an instance of :py:class:`random.Random` which
    uses the :py:meth:`random.random` method. In turn this method uses
    the Mersenne Twister (:ref:`Matsumoto & Nishimura <ref-matsumoto>`)
    as the core generator. The Mersenne Twister is one of the most
    extensively tested random number generators in existence.

    .. seealso::

       Module :py:mod:`random`
          Documentation of the :py:mod:`random` standard module.
    """
    spots = random.sample(xrange(1,26), n)
    return spots

def combine_records(records):
    """Return a combined SETL records from a list of multiple SETL
    records with the same plate ID.

    `records` is a list containing multiple SETL records where each
    record is a sequence with the plate ID as the first item followed by
    25 spot booleans. As this function is used for combining records
    from different species found on the same plate, the plate ID of all
    records must be equal.

    A basic usage example:

        >>> import setlyze.std
        >>> rec1 = (4567,1,1,0,0,1,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0)
        >>> rec2 = (4567,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1)
        >>> rec3 = (4567,0,0,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0)
        >>> records = [rec1,rec2,rec3]
        >>> setlyze.std.combine_records(records)
        [4567, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    """
    combined = [None,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    # Set the plate ID.
    if len(records):
        combined[0] = records[0][0]

    for record in records:
        # Make sure all plate IDs are the same.
        if combined[0] != record[0]:
            raise ValueError("Argument 'records' must contain records with equal plate ID.")

        # For each positive spot we find, set that spot in the combined
        # record to 1. We skip the first item, as that's the plate ID.
        for i, spot in enumerate(record[1:], start=1):
            # If spot is positive, set the same spot in 'combined' to 1.
            if spot:
                combined[i] = 1

    return combined

def mean(x):
    """Return the arithmetic mean of a sequence of numbers `x`.

    A simple example:

        >>> import setlyze.std
        >>> x = [5.91, 1, 10, 19, 22.1, 16, 3.3, 25, 12, 8, 18.5, 17, 23, 2, 7]
        >>> setlyze.std.mean(x)
        12.654

    """
    return sum(x, 0.0) / len(x)

def is_significant(p_value, alpha_level=0.05):
    """Returns True if the p-value `p_value` is significant, False otherwise.

    The p-value is significant if it is less or equal to the alpha level
    `alpha_level`. The default value for the alpha level is 0.05.

    Will raise ValueError if the p-value is NaN, or TypeError if one of the
    arguments are not of type 'float'.
    """
    if math.isnan(p_value):
        raise ValueError("The p-value is not a number")
    if not isinstance(p_value, float):
        raise TypeError("The p-value is not a float")
    if not isinstance(alpha_level, float):
        raise TypeError("The alpha level is not a float")
    return p_value <= alpha_level

class Sender(gobject.GObject):
    """Custom GObject for emitting SETLyze specific application signals.

    This module creates a single instance of this class. Subsequent
    imports of this module gives access to the same instance. Thus only
    one instance is created for each run.

    The ``__gsignals__`` class attribute is a dictionary containing all
    custom signals an instance of this class can emit. To emit a signal,
    use the :meth:`~setlyze.std.Sender.emit` method. To signal
    that an analysis has started for example, use: ::

        setlyze.std.sender.emit('analysis-started')

    If you want to emit a signal from a separate thread, you must use
    :meth:`gobject.idle_add` as only the main thread is allowed to touch
    the GUI. Emitting a signal from a separate thread looks like this: ::

        gobject.idle_add(setlyze.std.sender.emit, 'analysis-started')

    Anywhere in your application you can add a function to be called
    when this signal is emitted. This function is called a callback
    method. To add a callback method for a specific signal, use the
    :meth:`~setlyze.std.Sender.connect` method: ::

        self.handler = setlyze.std.sender.connect('analysis-started',
            self.on_analysis_started)

    When you are done using that handler, be sure to destroy it as
    the handler will continue to exist if the callback function does not
    return ``False``. To destroy a signal handler, use
    the :meth:`~setlyze.std.Sender.disconnect` method: ::

        setlyze.std.sender.disconnect(self.handler)

    .. warning::

       Remember to use :meth:`gobject.idle_add` if you decide to emit
       signals from separate threads. If you don't do this, the
       application becomes unstable resulting in crashes.

    .. seealso::

       `Theory of Signals and Callbacks <http://www.pygtk.org/pygtk2tutorial/sec-TheoryOfSignalsAndCallbacks.html>`_
          It's recommended to study this subject of the PyGTK
          documentation to get a better understanding of signals and
          callbacks.

       `Advanced Event and Signal Handling <http://www.pygtk.org/pygtk2tutorial/ch-AdvancedEventAndSignalHandling.html>`_
          It's recommended to study this subject of the PyGTK
          documentation to get a better understanding of event and
          signal handling.

       `Sub-classing GObject in Python <http://www.pygtk.org/articles/subclassing-gobject/sub-classing-gobject-in-python.htm>`_
          Or how to create custom properties and signals with PyGTK.

       `gobject.idle_add <http://www.pygtk.org/pygtk2reference/gobject-functions.html#function-gobject--idle-add>`_
          PyGTK documentation for :meth:`gobject.idle_add`.

    """

    __gproperties__ = {
        'save-slot' : (gobject.TYPE_INT, # type
            "Save slot", # nick name
            "Save slot for selections. There are two slots possible (0 and 1).", # description
            0, # minimum value
            1, # maximum value
            0, # default value
            gobject.PARAM_READWRITE), # flags
        'analysis' : (gobject.TYPE_STRING, # type
            "Analysis name", # nick name
            "Name of the analysis to be started. Possible values are \
            'spot_preference', 'attraction_intra', 'attraction_inter' \
            and 'relations'.", # description
            '', # default value
            gobject.PARAM_READWRITE), # flags
        'error-message' : (gobject.TYPE_STRING, # type
            "Error message", # nick name
            "The error message returned by a function or class.", # description
            '', # default value
            gobject.PARAM_READWRITE), # flags
    }

    # Create custom application signals.
    __gsignals__ = {
        'on-start-analysis': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'file-import-failed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),

        'beginning-analysis': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-started': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'pool-job-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'pool-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),

        'locations-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'species-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'define-areas-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'select-batch-analysis-window-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'local-db-created': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'locations-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_INT)),
        'species-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,gobject.TYPE_INT)),
        'plate-areas-defined': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
        'batch-analysis-selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),

        'analysis-aborted': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        'analysis-canceled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'selection-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'define-areas-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'report-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'no-results': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'repeat-analysis': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'save-individual-reports': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.save_slot = 0
        self.analysis = ''
        self.error_message = ''

    def do_get_property(self, property):
        if property.name == 'save-slot':
            return self.save_slot
        elif property.name == 'analysis':
            return self.analysis
        elif property.name == 'error-message':
            return self.error_message
        else:
            raise AttributeError('Unknown property %s' % property.name)

    def do_set_property(self, property, value):
        if property.name == 'save-slot':
            self.save_slot = value
        elif property.name == 'analysis':
            self.analysis = value
        elif property.name == 'error-message':
            self.error_message = value
        else:
            raise AttributeError('Unknown property %s' % property.name)

class ProgressDialogHandler(object):
    """This class allows you to control the progress dialog from a separate
    thread.

    Follow these steps to get the progress dialog working:

    1) Somewhere in the main thread, create a progress dialog ::

            pd = setlyze.gui.ProgressDialog(title="Analyzing",
                description="Performing heavy calculations, please wait...")

    2) Edit the worker process to automatically update the progress dialog.
       Create an instance of this class as follows (notice that the progress
       dialog is passed as its only argument) ::

            self.pdialog_handler = setlyze.std.ProgressDialogHandler(pd)

    3) Then you need to tell the handler how many times you're going to update
       the progress dialog (which is the number of times you'll call the
       :meth:`increase` method) ::

            self.pdialog_handler.set_total_steps(8)

    4) Then call the :meth:`increase` method in you worker class at the moments
       you want to update the progress dialog. Notice that :meth:`increase`
       will be called 8 times in the example below (hence total steps was set
       to 8) ::

            self.pdialog_handler.set_action("Calculating this...")
            self.some_heavy_function()

            self.pdialog_handler.increase("Still calculating...")
            for x in range(5):
                self.pdialog_handler.increase()
                self.calculate_this(x)

            self.pdialog_handler.increase("Calculating that...")
            self.more_heavy_calculations()

            self.pdialog_handler.increase("Finished!")

    5) Then start your worker process in a separate thread (if you're new to
       threading, start with the `threading documentation
       <http://docs.python.org/library/threading.html>`_) ::

        t = Worker()
        t.start()

    The progress bar should now increase while the worker process is running.
    For more examples you can look at the sources of the analysis modules (e.g.
    :mod:`setlyze.analysis.spot_preference`).

    """

    def __init__(self, pdialog=None):
        self.total_steps = None
        self.current_step = 0
        self.autoclose = True
        self.pdialog = None

        if pdialog: self.set_pdialog(pdialog)

    def set_pdialog(self, pdialog):
        """Set the progress dialog.

        The progress dialog must be an instance of
        :class:`setlyze.gui.ProgressDialog`.
        """
        if not isinstance(pdialog, setlyze.gui.ProgressDialog):
             raise ValueError("Invalid object type passed.")
        self.pdialog = pdialog

    def set_total_steps(self, number):
        """Set the total number of steps for the progress."""
        if not isinstance(number, int):
            raise ValueError("Value for 'number' should be an integer, not '%s'." %
                (type(number).__name__))

        # Reset the current step so we start with 0% again.
        self.current_step = 0

        # Set the new value for total steps. This number must be saved as a
        # float, because we want to calculate fractions.
        self.total_steps = float(number)

    def set_action(self, action):
        """Set the progress dialog's action string to `action`. This action
        string is showed in italics below the progress bar.
        """
        action = "<span style='italic'>%s</span>" % (action)
        gobject.idle_add(self.pdialog.action.set_markup, action)

    def increase(self, action=None):
        """Increase the progress bar's fraction. Calling this method causes
        the progress bar to fill a portion of the bar. This method takes care
        of calculating the right fraction. If `action` is supplied, the
        progress dialog's action string is set to `action`.
        """
        if not self.pdialog:
            return

        if not self.total_steps:
            raise ValueError("You didn't set the total number of steps. Use "
                "'set_total_steps()'.")

        # Calculate the new fraction.
        self.current_step += 1
        fraction = self.current_step / self.total_steps

        # Check if the fraction has a logical value.
        if 0.0 > fraction > 1.0:
            raise ValueError("Incorrect fraction '%f' encountered. You "
                "probably didn't set the correct total steps." % fraction)

        # Update the progress dialog.
        self.update(fraction, action)

    def complete(self, action=None):
        """Set the progress dialog to 100%."""
        if not self.pdialog:
            return
        gobject.idle_add(self.__update_progress_dialog, 1.0, action)

    def update(self, fraction, action=None):
        """Set the progress dialog's progress bar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.
        """
        if not self.pdialog:
            return

        # In case this is always called from a separate thread, so we must use
        # gobject.idle_add to access the GUI.
        gobject.idle_add(self.__update_progress_dialog, fraction, action)

    def destroy(self):
        """Destroy the progress dialog."""
        gobject.idle_add(self.__close_progress_dialog)

    def __update_progress_dialog(self, fraction, action=None):
        """Set the progress dialog's progressbar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.

        Don't call this function manually; use :meth:`increase` instead.
        """
        if not self.pdialog:
            return False

        # Update fraction.
        self.pdialog.pbar.set_fraction(fraction)

        # Set percentage text for the progress bar.
        percent = fraction * 100.0
        self.pdialog.pbar.set_text("%.1f%%" % percent)

        # Show the current action below the progress bar.
        if isinstance(action, str):
            action = "<span style='italic'>%s</span>" % (action)
            self.pdialog.action.set_markup(action)

        if fraction == 1.0:
            self.pdialog.pbar.set_text("Finished!")
            self.pdialog.button_cancel.set_sensitive(False)

            # Close the progress dialog when finished. We set a delay
            # of 1 second before closing it, so the user gets to see the
            # dialog when an analysis finishes very fast.
            if self.autoclose:
                gobject.idle_add(self.__close_progress_dialog, 1)

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

    def __close_progress_dialog(self, delay=0):
        """Close the progress dialog. Optionally set a delay of `delay`
        seconds before it's being closed.

        There's no need to call this function manually, as it is called
        by :meth:`__update_progress_dialog` when needed.
        """
        if not self.pdialog:
            return False

        # If a delay is set, sleep 'delay' seconds.
        if delay: time.sleep(delay)

        # Close the progress dialog.
        self.pdialog.destroy()
        self.pdialog = None

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

# Register the Sender class as an official GType.
gobject.type_register(Sender)

# Create a sender object which will send all the application signals.
sender = Sender()