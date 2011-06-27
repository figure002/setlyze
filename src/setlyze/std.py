#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
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

"""This module provides standard functions and classes. All functions
and classes that don't belong in any of the other modules are placed
here.
"""

import sys
import os
import math
import itertools
import random
import logging
import time
import xml.dom.minidom
from sqlite3 import dbapi2 as sqlite

import gobject
import rpy

import setlyze.config

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.1.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"

def we_are_frozen():
    """Returns whether we are frozen via py2exe. This will affect how we find
    out where we are located.
    """
    return hasattr(sys, "frozen")

def module_path():
    """This will get us the program's directory, even if we are frozen using
    py2exe.
    """
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

def make_remarks(results, attributes):
    """Return a remarks string that contains a summary of the results
    and attributes of a statistical test.
    """
    remarks = []

    # Decide which conclusions to use based on the attributes.
    if 'plate_area' in attributes:
        conclusions = ('Rejection','Preference')
    elif 'n_positive_spots' in attributes or 'ratios_group' in attributes:
        conclusions = ('Attraction','Repulsion')
    else:
        conclusions = ('Attraction','Repulsion')

    if 'p_value' in results:
        if results['p_value'] == 'nan':
            remarks.append("Not significant")
        elif float(results['p_value']) > setlyze.config.cfg.get('alpha-level'):
            remarks.append("Not significant")
        else:
            remarks.append("Significant")

            # If significant, also add attraction/repulsion.
            if 'mean_observed' in results and 'mean_expected' in results:
                if float(results['mean_observed']) < float(results['mean_expected']):
                    remarks.append(conclusions[0])
                else:
                    remarks.append(conclusions[1])

        if results['p_value'] == 'nan':
            pass
        elif float(results['p_value']) < 0.001:
            remarks.append("P < 0.001")
        elif float(results['p_value']) < 0.01:
            remarks.append("P < 0.01")
        elif float(results['p_value']) < 0.05:
            remarks.append("P < 0.05")
        else:
            remarks.append("P > 0.05")

    if 'n' in attributes:
        if int(attributes['n']) > 20:
            remarks.append("n > 20")
        else:
            remarks.append("n < 20")

    remarks = "; ".join(remarks)
    return remarks

def export_report(reader, path, type, elements=None):
    """Save the data from the XML DOM report to a data file or an
    analysis report document. The file is saved to `path` in a
    format specified by `type`. Possible values for `type` are
    ``xml``, ``txt`` or ``latex``.

    If `type` is ``xml``, all data from the DOM object is
    saved to an XML file. If `type` is ``txt`` or ``latex``,
    the report elements specified by the user will be saved to a
    human readable document.

    .. todo::
       Implement methods for generating text and LaTeX reports.

    Design Part: 1.17
    """

    # Based on the type, decide in which file type to save the
    # report.
    if type == 'xml':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".xml"):
            path += ".xml"
        reader.export_xml(path)

    elif type == 'txt':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".txt"):
            path += ".txt"
        exporter = ExportTextReport(reader)
        exporter.export(path, elements)

    elif type == 'latex':
        # Add the extension if it's missing from the filename.
        if not path.endswith(".tex") and not path.endswith(".latex"):
            path += ".tex"
        exporter = ExportLatexReport(reader)
        exporter.export(path, elements)

    else:
        raise ValueError("Unknow value for 'type'. Must be either "
            "'xml', 'txt' or 'latex'")

    logging.info("Analysis report saved to %s" % path)

def remove_items_from_list(a,b):
    """Remove the items in list `b` from list `a`."""
    for x in b:
        try:
            a.remove(x)
        except:
            pass

def combinations_with_replacement(iterable, r):
    """Return r length subsequences of elements from the input iterable
    allowing individual elements to be repeated more than once.

    Combinations are emitted in lexicographic sort order. So, if the
    input iterable is sorted, the combination tuples will be produced
    in sorted order.

    Elements are treated as unique based on their position, not on their
    value. So if the input elements are unique, the generated
    combinations will also be unique.

    This function was copied from the Python documentation for :mod:`itertools`.

    A simple example:

        >>> import setlyze.std
        >>> i = setlyze.std.combinations_with_replacement('ABCD', 2)
        >>> [x for x in i]
        [('A', 'A'), ('A', 'B'), ('A', 'C'), ('A', 'D'), ('B', 'B'), ('B', 'C'), ('B', 'D'), ('C', 'C'), ('C', 'D'), ('D', 'D')]
    """
    pool = tuple(iterable)
    n = len(pool)
    if not n and r:
        return
    indices = [0] * r
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != n - 1:
                break
        else:
            return
        indices[i:] = [indices[i] + 1] * (r - i)
        yield tuple(pool[i] for i in indices)

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
        combos = itertools.combinations(spots1,2)
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

def t_test(x, y = None, alternative = "two.sided", mu = 0,
            paired = False, var_equal = False, conf_level = 0.95):
    """Performs one and two sample t-tests on sequences of data.

    This is a wrapper function for the ``t.test`` function from R. It
    depends on R and RPy. The latter provides an interface to the R
    Programming Language.

    This function returns a dictionary containing the results. Below
    is the format of the dictionary with example results ::

        {
        'null.value': {'difference in means': 0},
        'method': 'Welch Two Sample t-test',
        'p.value': 0.97053139295765201,
        'statistic': {'t': -0.037113583386291726},
        'estimate': {'mean of y': 2.552142857142857, 'mean of x': 2.5417857142857141},
        'conf.int': [-0.56985924418141154, 0.54914495846712563],
        'parameter': {'df': 53.965197921982607},
        'alternative': 'two.sided'
        }

    .. seealso::

       R Documentation for Student's t-Test
          The R Documentation gives a more extensive documentation of
          this function, its arguments, usage, etc. To view the
          documentation, type ``help(t.test)`` from the R prompt.

    """
    result = rpy.r['t.test'](x, y, alternative, mu, paired,
        var_equal, conf_level)

    return result

def wilcox_test(x, y = None, alternative = "two.sided",
                 mu = 0, paired = False, exact = None, correct = True,
                 conf_int = False, conf_level = 0.95):
    """Performs one and two sample Wilcoxon tests on sequences of data;
    the latter is also known as ‘Mann-Whitney’ test.

    This is a wrapper function for the ``wilcox.test`` function from R.
    It depends on R and RPy. The latter provides an interface to the R
    Programming Language.

    This function returns a dictionary containing the results. Below
    is the format of the dictionary with example results ::

        {
        'estimate': {'difference in location': -2.0000005809455006},
        'null.value': {'location shift': 0},
        'p.value': 0.000810583642587086,
        'statistic': {'W': 1.0},
        'alternative': 'two.sided',
        'conf.int': [-3.1200287512799796, -1.2399735289828238],
        'parameter': None,
        'method': 'Wilcoxon rank sum test with continuity correction'
        }

    .. seealso::

       R Documentation for Wilcoxon Rank Sum and Signed Rank Tests
          The R Documentation gives a more extensive documentation of
          this function, its arguments, usage, etc. To view the
          documentation, type ``help(wilcox.test)`` from the R prompt.
    """
    result = rpy.r['wilcox.test'](x, y, alternative, mu, paired, exact,
        correct, conf_int, conf_level)

    return result

def shapiro_test(x):
    """Performs the Shapiro-Wilk test of normality.

    This is a wrapper function for the ``shapiro.test`` function from R.
    It depends on R and RPy. The latter provides an interface to the R
    Programming Language.

    The data sequence `x` passed to the ``shapiro.test`` function must
    contain between 3 and 5000 numberic values. If the length of `x` is
    below 3, a ValueError is raised. If the length of `x` is above
    5000, :py:meth:`random.sample` is used to get 5000 random values
    from `x`.

    This function returns a dictionary containing the results. Below
    is the format of the dictionary with example results ::

        {
        'method': 'Shapiro-Wilk normality test',
        'p.value': 6.862712394148655e-08,
        'statistic': {'W': 0.75000003111895985}
        }

    .. seealso::

       R Documentation for Shapiro-Wilk Normality Test
          The R Documentation gives a more extensive documentation of
          this function, its arguments, usage, etc. To view the
          documentation, type ``help(shapiro.test)`` from the R prompt.
    """
    if len(x) > 5000:
        rand_items = random.sample(x, 5000)
        result = rpy.r['shapiro.test'](rand_items)
    elif len(x) < 3:
        raise ValueError("Argument 'x' must contain at least 3 numeric values.")
    else:
        result = rpy.r['shapiro.test'](x)

    return result

def chisq_test(x, y = None, correct = True, p = None,
    rescale_p = False, simulate_p_value = False, b = 2000):
    """Performs chi-squared contingency table tests and
     goodness-of-fit tests.

    This is a wrapper function for the ``chisq.test`` function from R. It
    depends on R and RPy. The latter provides an interface to the R
    Programming Language.

    This function returns a dictionary containing the results. Below
    is the format of the dictionary with example results ::

        {
        'null.value': {'difference in means': 0},
        'method': 'Welch Two Sample t-test',
        'p.value': 0.97053139295765201,
        'statistic': {'t': -0.037113583386291726},
        'estimate': {'mean of y': 2.552142857142857, 'mean of x': 2.5417857142857141},
        'conf.int': [-0.56985924418141154, 0.54914495846712563],
        'parameter': {'df': 53.965197921982607},
        'alternative': 'two.sided'
        }

    .. seealso::

       R Documentation for Pearson's Chi-squared Test for Count Data
          The R Documentation gives a more extensive documentation of
          this function, its arguments, usage, etc. To view the
          documentation, type ``help(chisq.test)`` from the R prompt.

    """
    if not p:
        p = itertools.repeat(1.0/len(x), len(x))
        p = [x for x in p]

    result = rpy.r['chisq.test'](x, y, correct, p, rescale_p,
        simulate_p_value, b)

    return result

def mean(x):
    """Return the arithmetic mean of a sequence of numbers `x`.

    A simple example:

        >>> import setlyze.std
        >>> x = [5.91, 1, 10, 19, 22.1, 16, 3.3, 25, 12, 8, 18.5, 17, 23, 2, 7]
        >>> setlyze.std.mean(x)
        12.654

    """
    return sum(x, 0.0) / len(x)


class Sender(gobject.GObject):
    """Custom GObject for emitting SETLyze specific application signals.

    This module creates a single instance of this class. Subsequent
    imports of this module gives access to the same instance. Thus only
    one instance is created for each run.

    The ``__gsignals__`` class attribute is a dictionary containing all
    custom signals an instance of this class can emit. To emit a signal,
    use the :meth:`~setlyze.std.Sender.emit` method. To signal
    that an analysis has started for example, use: ::

        setlyze.std.sender.emit('analysis-finished')

    If you want to emit a signal from a separate thread, you must use
    :meth:`gobject.idle_add` as only the main thread is allowed to touch
    the GUI. Emitting a signal from a separate thread looks like this: ::

        gobject.idle_add(setlyze.std.sender.emit, 'analysis-finished')

    Anywhere in your application you can add a function to be called
    when this signal is emitted. This function is called a callback
    method. To add a callback method for a specific signal, use the
    :meth:`~setlyze.std.Sender.connect` method: ::

        self.handler_id = setlyze.std.sender.connect('analysis-finished',
            self.on_analysis_finished)

    When you are done using that handler, be sure to destroy it as
    the handler will continue to exist if the callback function does not
    return ``False``. To destroy a signal handler, use
    the :meth:`~setlyze.std.Sender.disconnect` method: ::

        setlyze.std.sender.disconnect(self.handler_id)

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
        'csv-import-failed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),

        'beginning-analysis': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-started': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'locations-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'species-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'define-areas-dialog-back': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'local-db-created': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'locations-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'species-selection-saved': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,)),
        'plate-areas-defined': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),

        'analysis-aborted': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'analysis-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'selection-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'define-areas-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'report-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'progress-dialog-closed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
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

class ReportGenerator(object):
    """Create a XML DOM (Document Object Model) object of the analysis
    settings, data and results. The DOM can then be exported to an XML
    file containing all data for the analysis.

    Using XML DOM objects for storing analysis data has great
    advantages. Because the object can contain all analysis data, it's
    easy to use Python's XML parser to generate analysis reports. We can
    allow the user to choose which elements of the XML DOM object to
    export to say a LaTeX document. Also, :py:mod:`xml.dom.minidom`
    provides methods for exporting this object to an XML file. This file
    by default contains all analysis data. This file can be easily
    loaded in SETLyze so we can display a dialog showing the analysis
    data and results present in that XML file. The XML file can be used
    as a backup file of the analysis data.

    So too the class :class:`ReportReader` uses this XML DOM object
    to access the analysis data.

    Design Part: 1.48
    """

    def __init__(self):
        self.ns = "http://www.gimaris.com/setlyze/"
        self.dbfile = setlyze.config.cfg.get('db-file')

        # Create a new XML DOM object (Design Part: 2.17).
        self.doc = xml.dom.minidom.Document()
        # Create the top report element.
        self.report = self.doc.createElementNS(self.ns, "setlyze:report")
        # Manually add the namespace to the top element.
        self.report.setAttribute("xmlns:setlyze", self.ns)
        self.doc.appendChild(self.report)

    def create_element(self, parent, name, child_elements={}, attributes={}, text=None):
        """Add a new child element with name `name` to the element
        `parent` for the XML DOM object.

        Usually you'll start by adding child elements to the
        root element ``self.report``. In this case `parent` would be
        ``self.report``. It's then possible to add child elements for
        for those by setting `parent` to the newly created child
        elements.

        Optionally you can easily add child elements by setting
        `child_elements` to a dictionary. The dictionary keys will be
        the names of the child elements, and the corresponding
        dictionary values will be the values for the elements.

        This method also allows you to easily add attributes. To add
        attributes, set `attributes` to a dictionary. The dictionary
        keys will be the names of attributes, and the corresponding
        dictionary values will be the values for the attributes.

        The `text` argument gives the element a value. The value of
        `text` can be anything.

        This method returns the newly created element. This allows you
        to set the returned element object as the parent element
        for other elements.

        We shall clarify with some usage examples. First we add an
        empty child element to the root element: ::

            location_selections_element = self.create_element(
                parent=self.report,
                name="location_selections"
                )

        Then we add some child elements to the just created element: ::

            self.create_element(
                parent=location_selections_element,
                name="location",
                child_elements={'nr':1, 'name':"Aquadome, Grevelingen"},
                attributes={'id':1}
                )

            self.create_element(
                parent=location_selections_element,
                name="location",
                child_elements={'nr':2, 'name':"Colijnsplaat, floating dock, Oosterschelde"},
                attributes={'id':2}
                )

        Would this be exported to an XML file, the contents of the file
        would look like this: ::

            <?xml version="1.0" encoding="utf-8"?>
            <setlyze:report xmlns:setlyze="http://www.gimaris.com/setlyze/">
                <location_selections>
                    <location id="1">
                        <nr>
                            1
                        </nr>
                        <name>
                            Aquadome, Grevelingen
                        </name>
                    </location>
                    <location id="2">
                        <nr>
                            2
                        </nr>
                        <name>
                            Colijnsplaat, floating dock, Oosterschelde
                        </name>
                    </location>
                </location_selections>
            </setlyze:report>
        """

        # Create a new element.
        element = self.doc.createElementNS(self.ns, name)

        # Make this new element a child of the provided parent element.
        if parent:
            parent.appendChild(element)

        # Add attributes.
        for key,val in attributes.iteritems():
            element.setAttribute(str(key), str(val))

        # Add child elements.
        for key,val in child_elements.iteritems():
            child_element = self.doc.createElementNS(self.ns, key)
            text_node = self.doc.createTextNode(str(val))
            child_element.appendChild(text_node)
            element.appendChild(child_element)

        # Add a text element.
        if text != None:
            text_node = self.doc.createTextNode(str(text))
            element.appendChild(text_node)

        return element

    def get_element(self, parent, name):
        """Return the element object with name `name` from a parent
        element `parent`.
        """
        element = None
        for e in parent.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == name:
                element = e
                break
        return element

    def set_analysis(self, name):
        """Add the element ``analysis`` with value `name` to the XML DOM
        report.

        This element describes to which analysis this report belongs. So
        `name` is just a string with the title of an analysis. However,
        if the value of `name` exists as a key in the ``analysis_names``
        dictionary, the corresponding value from that dictionary will
        be used as the value for the element instead.

        Design Part: 1.72
        """

        # A dictinary with all the known analysis.
        analysis_names = {'spot_preference': "Spot Preference",
            'attraction_intra': "Attraction within Species",
            'attraction_inter': "Attraction between Species",
            'relations': "Relation between Species",
            }

        # Check if the provided name is present in the list of
        # analysis names. If so, use the name from the list.
        # If 'name' is not in the list, do nothing and just use the
        # name as it is.
        if name in analysis_names:
            name = analysis_names[name]

        # Create the element.
        self.create_element(parent=self.report,
            name="analysis",
            text=name
            )

    def set_location_selections(self):
        """Add the element ``location_selections`` to the XML DOM
        report.

        This element will be filled with the locations selections. If
        two locations selections were made, both will be added to the
        element.

        The XML representation looks like this: ::

            <location_selections>
                <selection slot="0">
                    <location id="1">
                        <nr>
                            1
                        </nr>
                        <name>
                            Aquadome, Grevelingen
                        </name>
                    </location>
                </selection>
                <selection slot="1">
                    <location id="2">
                        <nr>
                            2
                        </nr>
                        <name>
                            Colijnsplaat, floating dock, Oosterschelde
                        </name>
                    </location>
                </selection>
            </location_selections>

        Design Part: 1.50
        """

        # Create a new element to save the location selections in.
        location_selections = self.create_element(
            parent=self.report,
            name='location_selections'
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for slot in (0,1):
            # Get the locations selection for each slot.
            loc_ids = setlyze.config.cfg.get('locations-selection',
                slot=slot)

            # Skip to the next slot if this selection is not set.
            if not loc_ids:
                continue

            # Create a 'locations_selection' child element for each
            # selection. We give each selection element a 'slot'
            # attribute.
            loc_selection_element = self.create_element(
                parent=location_selections,
                name="selection",
                attributes={'slot': slot}
                )

            # Fetch all information about the locations selection.
            loc_ids_str = ",".join([str(id) for id in loc_ids])
            cursor.execute( "SELECT loc_id,loc_name,loc_nr "
                            "FROM localities "
                            "WHERE loc_id IN (%s)" %
                            (loc_ids_str)
                            )

            for row in cursor:
                self.create_element(parent=loc_selection_element,
                    name="location",
                    child_elements={'name':row[1], 'nr':row[2]},
                    attributes={'id':row[0]}
                    )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_species_selections(self):
        """Add the element ``species_selections`` to the XML DOM
        report.

        This element will be filled with the species selections. If
        two species selections were made, both will be added to the
        element.

        The XML representation looks like this: ::

            <species_selections>
                <selection slot="0">
                    <species id="2">
                        <name_latin>
                            Ectopleura larynx
                        </name_latin>
                        <name_venacular>
                            Gorgelpijp
                        </name_venacular>
                    </species>
                </selection>
                <selection slot="1">
                    <species id="6">
                        <name_latin>
                            Metridium senile
                        </name_latin>
                        <name_venacular>
                            Zeeanjelier
                        </name_venacular>
                    </species>
                </selection>
            </species_selections>

        Design Part: 1.51
        """

        # Create a new element to save the species selections in.
        species_selections = self.create_element(
            parent=self.report,
            name="species_selections"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        for slot in (0,1):
            # Get the species selection for each slot.
            spe_ids = setlyze.config.cfg.get('species-selection',
                slot=slot)

            # Skip to the next slot if this selection is not set.
            if not spe_ids:
                continue

            # Create a 'species_selection' child element for each
            # selection. We give each selection element a 'slot'
            # attribute.
            spe_selection_element = self.create_element(
                parent=species_selections,
                name="selection",
                attributes={'slot': slot}
                )

            # Fetch all information about the species selection.
            spe_ids_str = ",".join([str(id) for id in spe_ids])
            cursor.execute( "SELECT spe_id,spe_name_venacular,spe_name_latin "
                            "FROM species "
                            "WHERE spe_id IN (%s)" %
                            (spe_ids_str)
                            )

            for row in cursor:
                self.create_element(parent=spe_selection_element,
                    name="species",
                    child_elements={'name_venacular': row[1],'name_latin': row[2]},
                    attributes={'id':row[0]}
                    )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_observed(self):
        """Add the element ``spot_distances_observed`` to the XML DOM
        report.

        This element will be filled with the observed spot distances.

        The XML representation looks like this: ::

            <spot_distances_observed>
                <distance plate_id="63">
                    1.0
                </distance>
                <distance plate_id="63">
                    2.0
                </distance>
                <distance plate_id="229">
                    3.16
                </distance>
            </spot_distances_observed>

        Design Part: 1.52
        """

        # Create a new child element for the report.
        distances_observed_element = self.create_element(
            parent=self.report,
            name="spot_distances_observed"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the observed distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_observed"
                        )

        for row in cursor:
            self.create_element(parent=distances_observed_element,
                name="distance",
                attributes={'plate_id': row[0]},
                text=row[1]
                )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_spot_distances_expected(self):
        """Add the element ``spot_distances_expected`` to the XML DOM
        report.

        This element will be filled with the expected spot distances.

        The XML representation looks like this: ::

            <spot_distances_expected>
                <distance plate_id="62">
                    1.0
                </distance>
                <distance plate_id="62">
                    3.16
                </distance>
                <distance plate_id="228">
                    4.47
                </distance>
            </spot_distances_expected>

        Design Part: 1.53
        """

        # Create a new child element for the report.
        distances_expected_element = self.create_element(
            parent=self.report,
            name="spot_distances_expected"
            )

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Fetch all the observed distances.
        cursor.execute( "SELECT rec_pla_id,distance "
                        "FROM spot_distances_expected"
                        )

        for row in cursor:
            self.create_element(parent=distances_expected_element,
                name="distance",
                attributes={'plate_id': row[0]},
                text=row[1]
                )

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_plate_areas_definition(self):
        """Add the element ``plate_areas_definition`` to the XML DOM
        report.

        This element will be filled with the user defined spot areas
        definition.

        The XML representation looks like this: ::

            <plate_areas_definition>
                <area id="area1">
                    <spot>
                        A
                    </spot>
                </area>
                <area id="area2">
                    <spot>
                        B
                    </spot>
                </area>
                <area id="area3">
                    <spot>
                        C
                    </spot>
                    <spot>
                        D
                    </spot>
                </area>
            </plate_areas_definition>

        Design Part: 1.54
        """

        # Get the spot areas definition.
        definition = setlyze.config.cfg.get('plate-areas-definition')

        # Create a new element for the areas definition.
        areas_definition_element = self.create_element(
            parent=self.report,
            name="plate_areas_definition"
            )

        for area, spots in definition.iteritems():
            area_element = self.create_element(
                parent=areas_definition_element,
                name="area",
                attributes={'id':area}
                )
            for spot in spots:
                self.create_element(
                    parent=area_element,
                    name="spot",
                    text=spot
                    )

    def set_area_totals_observed(self, totals_observed):
        """Add the element ``area_totals_observed`` to the XML DOM
        report.

        This element will be filled with the observed species totals per
        plate area.

        The XML representation looks like this: ::

            <area_totals_observed>
                <area id="area1">
                    27
                </area>
                <area id="area2">
                    75
                </area>
                <area id="area3">
                    52
                </area>
            </area_totals_observed>

        Design Part: 1.55
        """

        # Create a new child element for the report.
        species_totals_element = self.create_element(
            parent=self.report,
            name="area_totals_observed"
            )

        for area, total in totals_observed.iteritems():
            self.create_element(parent=species_totals_element,
                name="area",
                attributes={'id': area},
                text=total
                )

    def set_area_totals_expected(self, totals_observed):
        """Add the element ``area_totals_expected`` to the XML DOM
        report.

        This element will be filled with the expected species totals per
        plate area.

        The XML representation looks like this: ::

            <area_totals_expected>
                <area id="area1">
                    24.64
                </area>
                <area id="area2">
                    73.92
                </area>
                <area id="area3">
                    55.44
                </area>
            </area_totals_expected>

        Design Part: 1.56
        """

        # Create a new child element for the report.
        species_totals_element = self.create_element(
            parent=self.report,
            name="area_totals_expected"
            )

        for area, total in totals_observed.iteritems():
            self.create_element(parent=species_totals_element,
                name="area",
                attributes={'id': area},
                text=total
                )

    def set_statistics(self, name, data):
        """Add the element ``statistics`` with child element
        ``name`` to the XML DOM report.

        This element will be filled with the results of the performed
        statistical tests. The results must be supplied with the
        `data` argument. The `data` argument is a list containing
        dictionaries in the format {'attr': {'<name>': <value>, ...},
        'results': {'<name>': <value>, ...}} where the value for 'attr' is
        a dictionary with the attributes and 'results' is a dictionary
        with child elements for the ``statistics`` element.

        An XML representation: ::

            <statistics>
                <wilcoxon alternative="two.sided" conf_level="0.95" method="Wilcoxon rank sum test with continuity correction" n="3" n_plates="1" n_positive_spots="3" paired="False">
                    <conf_int_start>
                        -2.16
                    </conf_int_start>
                    <p_value>
                        0.353678517318
                    </p_value>
                    <mean_expected>
                        2.13333333333
                    </mean_expected>
                    <conf_int_end>
                        1.0
                    </conf_int_end>
                    <mean_observed>
                        1.33333333333
                    </mean_observed>
                </wilcoxon>
            </statistics>

        Design Part: 1.70
        """

        # Create the 'statistics' element if it doesn't exist.
        statistics_element = self.get_element(self.report, 'statistics')
        if not statistics_element:
            statistics_element = self.create_element(
                parent=self.report,
                name='statistics'
                )

        for x in data:
            self.create_element(
                parent=statistics_element,
                name=name,
                attributes=x['attr'],
                child_elements=x['results'],
                )

    def set_statistics_repeats(self, name, results):
        """Add the element "significance_test_repeats_areas" to the XML DOM
        report.

        This element will be filled with the number of significant results
        per plate area group.

        The XML representation looks like this: ::

            <wilcoxon_areas_repeats alpha_level="0.05" repeats="100">
                <result plate_area="A">
                    <n_preference>
                        100
                    </n_preference>
                    <n_rejection>
                        0
                    </n_rejection>
                    <n_significant>
                        100
                    </n_significant>
                </result>
                <plate_area id="B+C+D">
                    <n_preference>
                        0
                    </n_preference>
                    <n_rejection>
                        100
                    </n_rejection>
                    <n_significant>
                        100
                    </n_significant>
                </plate_area>
            </significance_test_repeats_areas>

        Design Part: 1.71
        """

        # Make sure the testid is valid.
        valid_names = ('wilcoxon_areas','wilcoxon_spots','wilcoxon_ratios')
        if name not in valid_names:
            raise ValueError("Possible values for 'name' are %s. You gave '%s'." %
                (", ".join(testids), name))

        # Decide which attribute name to use for 'result' elements.
        if 'areas' in name:
            group_attribute = 'plate_area'
        elif 'spots' in name:
            group_attribute = 'n_spots'
        elif 'ratios' in name:
            group_attribute = 'ratio_group'

        # Create a new child element for the report.
        repeats_element = self.create_element(
            parent=self.report,
            name="%s_repeats" % (name),
            attributes={'repeats': setlyze.config.cfg.get('test-repeats'),
                'alpha_level': setlyze.config.cfg.get('alpha-level')},
            )

        for group_attribute_value, items in results.iteritems():
            result_element = self.create_element(parent=repeats_element,
                name='result',
                attributes={group_attribute: group_attribute_value},
                )

            for name, value in items.iteritems():
                self.create_element(parent=result_element,
                    name=name,
                    text=value,
                    )

    def get_report(self):
        """Return the XML DOM report object."""
        return self.doc

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, encoding="utf-8")
        f.close()

class ReportReader(object):
    """Provide standard methods for extracting data from the XML
    DOM object containing analysis data.

    This class can also export the XML DOM object to an XML document.

    Design Part: 1.49
    """

    def __init__(self, report = None):
        self.ns = "http://www.gimaris.com/setlyze/"
        self.doc = None

        if report:
            self.set_report(report)

    def set_report(self, report):
        """Set the XML DOM report object `report` generated by
        :class:`ReportGenerator`. `report` can also be the path to an
        XML file containing an analysis report.
        """
        if isinstance(report, xml.dom.minidom.Document):
            # 'report' is an XML DOM object.
            self.doc = report
        elif isinstance(report, str) and os.path.isfile(report):
            # 'report' is path to an XML file. So parse its contents.
            self.doc = xml.dom.minidom.parse(report)
        else:
            raise ValueError("Argument 'report' must be either a XML "
                "DOM object or the path to an XML file containing "
                "analysis data.")

        # Check if the report contains a 'report' element.
        if not self.doc.childNodes[0].localName == "report":
            raise ValueError("The XML DOM object is missing a setlyze report.")

    def get_element(self, parent, name):
        """Return the element object with name `name` from a parent
        element `parent`.
        """
        element = None
        for e in parent.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == name:
                element = e
                break
        return element

    def get_child_names(self, parent=None):
        """Return a list with all child element names from the XML DOM
        object. The child elements for the report elements are excluded.

        Use this as a quick way to find out which elements are present
        in a XML DOM report object.
        """
        report_elements = []
        if parent:
            for e in parent.childNodes:
                if e.nodeType == e.ELEMENT_NODE:
                    report_elements.append(e.localName)
        else:
            for e in self.doc.childNodes[0].childNodes:
                if e.nodeType == e.ELEMENT_NODE:
                    report_elements.append(e.localName)
        return uniqify(report_elements)

    def get_analysis_name(self):
        """Return the value of the `analysis` element. This element
        contains the name of the analysis.
        """
        analysis_name = None

        # Find the 'species_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == 'analysis':
                # Found the 'species_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                analysis_name = e.childNodes[0].nodeValue.strip()
                break

        return analysis_name

    def get_locations_selection(self, slot=0):
        """Return the locations selection from the selection slot with
        number `slot` from the XML DOM report. Possible values for
        `slot` are ``0`` and ``1``.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns dictionaries in the format
        ``{'nr': <value>, 'name': <value>}``.

        Usage example: ::

            locations_selection = reader.get_locations_selection(slot=0)
            for loc in locations_selection:
                print loc['nr'], loc['name']
        """
        locations_selection = None

        # Find the 'location_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "location_selections":
                # Found the 'location_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE and \
                            e2.localName == "selection" and \
                            e2.getAttribute("slot") == str(slot):
                        locations_selection = e2
                        break

        # Check if the 'selection' element was found. If not, yield
        # None and exit.
        if not locations_selection:
            return

        # Return each location from the 'locations_selection' node.
        for e in locations_selection.childNodes:
            location = {}
            if e.nodeType == e.ELEMENT_NODE and e.localName == "location":
                # Save each 'location' element to the location
                # dictionary as: location[node_name] = node_value
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        location[e2.localName] = e2.childNodes[0].nodeValue.strip()

            yield location

    def get_species_selection(self, slot=0):
        """Return the species selection from the selection slot with
        number `slot` from the XML DOM report. Possible values for
        `slot` are ``0`` and ``1``.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns dictionaries in the format
        ``{'name_latin': <value>, 'name_venacular': <value>}``.

        Usage example: ::

            species_selection = reader.get_species_selection(slot=0)
            for spe in species_selection:
                print spe['name_latin'], spe['name_venacular']
        """
        species_selection = None

        # Find the 'species_selections' element in the XML DOM object.
        for e in self.doc.childNodes[0].childNodes:
            if e.nodeType == e.ELEMENT_NODE and \
                    e.localName == "species_selections":
                # Found the 'species_selections' element. Now get one
                # of the 'selection' child elements that matches the
                # slot number.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE and \
                            e2.localName == "selection" and \
                            e2.getAttribute("slot") == str(slot):
                        species_selection = e2
                        break

        # Check if the 'selection' element was found. If not, yield
        # None and exit.
        if not species_selection:
            return

        # Return each species from the 'species_selection' node.
        for e in species_selection.childNodes:
            species = {}
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'species':
                # Save each 'species' element to the species
                # dictionary as: species[node_name] = node_value
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        species[e2.localName] = e2.childNodes[0].nodeValue.strip()

            yield species

    def get_spot_distances_observed(self):
        """Return the observed spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. The iterator returns the distances.

        Usage example: ::

            observed_distances = reader.get_spot_distances_observed()
            for dist in observed_distances:
                print dist
        """

        # Find the 'spot_distances_observed' node in the XML DOM object.
        spot_distances_observed = self.get_element(self.doc, 'spot_distances_observed')

        # Check if the 'spot_distances_observed' node was found.
        if not spot_distances_observed:
            return

        # Return each distance from the 'spot_distances_observed' node.
        for e in spot_distances_observed.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'distance':
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_spot_distances_expected(self):
        """Return the expected spot distances from the XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. The iterator returns the distances.

        Usage example: ::

            expected_distances = reader.get_spot_distances_expected()
            for dist in expected_distances:
                print dist
        """

        # Find the 'spot_distances_expected' node in the XML DOM object.
        spot_distances_expected = self.get_element(self.doc, 'spot_distances_expected')

        # Check if the 'spot_distances_expected' node was found.
        if not spot_distances_expected:
            return

        # Return each distance from the 'spot_distances_expected' node.
        for e in spot_distances_expected.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'distance':
                # Return the value for the distance element.
                yield e.childNodes[0].nodeValue.strip()

    def get_plate_areas_definition(self):
        """Return the spot areas definition from the XML DOM report.
        This method returns a dictionary. For example: ::

            {
            'area1': ['A'],
            'area2': ['B'],
            'area3': ['C', 'D']
            }

        or: ::

            {
            'area1': ['A'],
            'area2': ['B'],
            'area3': ['C'],
            'area4': ['D']
            }
        """

        # Find the 'spots_definition' node in the XML DOM object.
        areas_definition = self.get_element(self.doc, 'plate_areas_definition')

        # Check if the 'spots_definition' node was found.
        if not areas_definition:
            return

        # Fill this dictionary with the spots definition.
        definition = {}

        # Return each area from the 'spots_definition' node.
        for e in areas_definition.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                # Add each area to the 'definition' dictionary.
                area_id = e.getAttribute("id")
                if not area_id in definition:
                    definition[area_id] = []

                # Now put each spot from that area in the definition.
                for e2 in e.childNodes:
                    definition[area_id].append( e2.childNodes[0].nodeValue.strip() )

        return definition

    def get_area_totals_observed(self):
        """Return the observed species totals per plate area from the
        XML DOM report.

        This method returns a dictionary. For example: ::

            {
            'area1': 24.64,
            'area2': 73.92,
            'area3': 55.44
            }
        """

        # Find the 'area_totals_observed' node in the XML DOM object.
        area_totals = self.get_element(self.doc, "area_totals_observed")

        # Check if the 'area_totals_observed' node was found.
        if not area_totals:
            return

        # Add each area total to the 'totals' dictionary.
        totals = {}
        for e in area_totals.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                area_id = e.getAttribute("id")

                totals[area_id] = e.childNodes[0].nodeValue.strip()

        return totals

    def get_area_totals_expected(self):
        """Return the expected species totals per area from the XML DOM
        report.

        This method returns a dictionary. For example: ::

            {
            'area1': 23.12,
            'area2': 60.10,
            'area3': 40.44
            }
        """

        # Find the 'area_totals_expected' node in the XML DOM object.
        area_totals = self.get_element(self.doc, "area_totals_expected")

        # Check if the 'area_totals_expected' node was found.
        if not area_totals:
            return

        # Add each area total to the 'totals' dictionary.
        totals = {}
        for e in area_totals.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == "area":
                area_id = e.getAttribute("id")

                totals[area_id] = e.childNodes[0].nodeValue.strip()

        return totals

    def get_statistics(self, element_name):
        """Return the statistics elements with name `name` from the
        XML DOM report.

        This is a generator, meaning that this function returns an
        iterator. This iterator returns tuples in the format
        ``({'<name>': <value>, ...}, {'<name>': <value>, ...})`` where
        the first dictionary contains the attributes and the second
        the results.
        """

        # Find the 'statistics' element in the XML DOM object.
        statistics = self.get_element(self.doc, 'statistics')

        # Check if the 'statistics' element was returned.
        if not statistics:
            return

        # Return each element with name `name` from the 'statistics' node.
        for e in statistics.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == element_name:
                attributes = {}
                results = {}

                # Get all attributes for this result element.
                for key in e.attributes.keys():
                    # Save each attribute to the attributes dictionary.
                    attributes[key] = e.getAttribute(key)

                # Get all sub elements for this result element.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        # Save each item of the result element to the
                        # items dictionary.
                        results[e2.localName] = e2.childNodes[0].nodeValue.strip()

                # Return a tuple.
                yield (attributes,results)

    def get_statistics_repeats(self, element_name):
        """Return the repeated statistical test results for `element_name`
        from the XML DOM report. `element_name` is the element name of the
        non-repeated variant. Possible values for `element_name` are
        "wilcoxon_areas", "wilcoxon_spots", "wilcoxon_ratios",
        "chi_squared_areas", "chi_squared_spots" and "chi_squared_ratios".

        This method returns a dictionary. For example: ::

            {
                'A': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0},
                'B': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'C': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'D': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'A+B': {'n_significant': 0, 'n_preference': 0, 'n_rejection': 0,
                'repeats': 100,
            }
        """

        # Find the 'element_name_repeats' node in the XML DOM object.
        element_name = '%s_repeats' % element_name
        repeats_element = self.get_element(self.doc, element_name)

        # Check if the 'element_name_repeats' node was found.
        if not repeats_element:
            return

        # Decide which attribute name to use for 'result' elements.
        if 'areas' in element_name:
            group_attribute = 'plate_area'
        elif 'spots' in element_name:
            group_attribute = 'n_spots'
        elif 'ratios' in element_name:
            group_attribute = 'ratio_group'

        # Add the results to the 'results' dictionary.
        results = {}
        for e in repeats_element.childNodes:
            if e.nodeType == e.ELEMENT_NODE and e.localName == 'result':
                group_attribute_value = e.getAttribute(group_attribute)

                # Create a dictionary for this plate area.
                results[group_attribute_value] = {}

                # Get all sub elements for 'result'.
                for e2 in e.childNodes:
                    if e2.nodeType == e2.ELEMENT_NODE:
                        results[group_attribute_value][e2.localName] = e2.childNodes[0].nodeValue.strip()

        # Add the number of repeats to the 'results' dict as well.
        results['repeats'] = repeats_element.getAttribute('repeats')

        return results

    def get_xml(self):
        """Return the XML source for the XML DOM report."""
        return self.doc.toprettyxml(encoding="utf-8")

    def export_xml(self, filename):
        """Export the XML source of the XML DOM report to a file."""
        f = open(filename, 'w')
        self.doc.writexml(f, addindent="\t", newl="\n", encoding="utf-8")
        f.close()

class ExportLatexReport(object):
    """Generate an analysis report in LaTeX format.

    Design Part:
    """

    def __init__(self, reader = None):
        self.set_report_reader(reader)

    def set_report_reader(self, reader):
        """Set the report reader."""
        self.reader = reader

    def generate(self, elements=None):
        pass

    def export(self, path, elements=None):
        pass

class ExportTextReport(object):
    """Generate an analysis report in text format.

    Design Part:
    """

    def __init__(self, reader = None):
        self.set_report_reader(reader)

    def set_report_reader(self, reader):
        """Set the report reader."""
        self.reader = reader

    def part(self, header):
        """Return `header` marked up as a header for parts in
        reStructuredText format.
        """
        text = "<hr>\n<h>\n<hr>\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "="*len(header))
        return text

    def chapter(self, header):
        """Return `header` marked up as a header for parts in
        reStructuredText format.
        """
        text = "<hr>\n<h>\n<hr>\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "*"*len(header))
        return text

    def section(self, header):
        """Return `header` marked up as a header for sections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "#"*len(header))
        return text

    def subsection(self, header):
        """Return `header` marked up as a header for subsections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "="*len(header))
        return text

    def subsubsection(self, header):
        """Return `header` marked up as a header for subsubsections in
        reStructuredText format.
        """
        text = "\n<h>\n<hr>\n\n"
        text = text.replace('<h>', header)
        text = text.replace('<hr>', "^"*len(header))
        return text

    def table(self, headers):
        """Return a table header with column names from `headers` in
        reStructuredText format.

        `headers` is a list of strings representing the column names.
        """
        header = ""
        header_lengths = []
        header_placeholders = []
        row_placeholders = []
        predefined_lengths = {"df": 6,
            "Remarks": 40,
            "W": 6,
            }
        predefined_fields = {"Plate Area": "%%-%ds",
            "Area ID": "%%-%ds",
            "P-value": "%%%d.4f",
            "Chi squared": "%%%d.4f",
            "Plate Area": "%%-%ds",
            "Plate Area Surfaces": "%%-%ds",
            "Mean Observed": "%%%d.4f",
            "Mean Expected": "%%%d.4f",
            "Remarks": "%%-%ds",
            }

        # Generate a placeholder strings for the column names and the fields.
        for name in headers:
            if name not in predefined_lengths:
                length = len(name)
            else:
                length = predefined_lengths[name]

            # Save the lengths of all column names. This is needed for
            # generating the table rules.
            header_lengths.append(length)

            # Construct the placeholders for the column names.
            header_placeholders.append("%%-%ds" % length)

            # Construct the placeholders for the fields.
            if name not in predefined_fields:
                row_placeholders.append("%%%ds" % length)
            else:
                row_placeholders.append(predefined_fields[name] % length)

        # Generate top rule for table.
        header += self.table_rule(header_lengths)

        # Generate string with column names.
        header_placeholders = "  ".join(header_placeholders)
        header += header_placeholders % tuple(headers)
        header += "\n"

        # Generate rule below column names.
        header += self.table_rule(header_lengths)

        # Generate placeholder string for table rows.
        row_placeholders = "  ".join(row_placeholders)
        row_placeholders += "\n"

        # Generate rule for the end of the table.
        footer = self.table_rule(header_lengths)

        return (header,row_placeholders,footer)

    def table_rule(self, col_widths):
        """Return a rule for a table with column widths `col_widths`.

        `col_widths` is a list/tuple containing column widths (integers).
        """
        format = []
        for n in col_widths:
            format.append("="*n)
        return "  ".join(format) + "\n"

    def generate(self, elements=None):
        """Generate analysis report in text format."""

        # Get the child element names of the report root.
        report_elements = self.reader.get_child_names()

        # Add the child element names of the 'statistics' element to the
        # list of root element names.
        stats = self.reader.get_element(self.reader.doc, 'statistics')
        if stats:
            report_elements.extend(self.reader.get_child_names(stats))

        # If 'elements' argument was provided, create a new 'report_elements'
        # list containing only the elements that are present in both lists.
        report_elements_new = []
        if elements:
            for element in elements:
                for r_element in report_elements:
                    # Now check if string 'element' is part of string
                    # r_element. Note that they don't have to be exactly the
                    # same, e.g. if 'spot_distances' is present in 'elements',
                    # both 'spot_distances_observed' and
                    # 'spot_distances_expected' will be added to
                    # 'report_elements_new'.
                    if element in r_element:
                        report_elements_new.append(r_element)
            report_elements = report_elements_new

        # Write the header for the report which includes the analysis
        # name.
        header = "SETLyze Analysis Report - %s" % self.reader.get_analysis_name()
        yield self.part(header)

        # Add species selections.
        if 'species_selections' in report_elements:
            yield self.section("Locations and Species Selections")

            species_selection = self.reader.get_species_selection(slot=0)
            yield self.subsection("Species Selection [1]")
            for spe in species_selection:
                if not len(spe['name_latin']):
                    yield "* %s\n" % (spe['name_venacular'])
                elif not len(spe['name_venacular']):
                    yield "* %s\n" % (spe['name_latin'])
                else:
                    yield "* %s (%s)\n" % (spe['name_latin'], spe['name_venacular'])

            if len(list(self.reader.get_species_selection(slot=1))):
                species_selection = self.reader.get_species_selection(slot=1)
                yield self.subsection("Species Selection [2]")
                for spe in species_selection:
                    if not len(spe['name_latin']):
                        yield "* %s\n" % (spe['name_venacular'])
                    elif not len(spe['name_venacular']):
                        yield "* %s\n" % (spe['name_latin'])
                    else:
                        yield "* %s (%s)\n" % (spe['name_latin'], spe['name_venacular'])

        # Add locations selections.
        if 'location_selections' in report_elements:
            yield self.subsection("Locations selection [1]")
            locations_selection = self.reader.get_locations_selection(slot=0)
            for loc in locations_selection:
                yield "* %s\n" % loc['name']

            if len(list(self.reader.get_locations_selection(slot=1))):
                yield self.subsection("Locations selection [2]")
                locations_selection = self.reader.get_locations_selection(slot=1)
                for loc in locations_selection:
                    yield "* %s\n" % loc['name']

        # Add the spot distances.
        if 'spot_distances_observed' in report_elements and \
                'spot_distances_expected' in report_elements:
            yield self.section("Spot Distances")

            t_header, t_row, t_footer = self.table(["Observed","Expected"])

            yield t_header
            observed_distances = self.reader.get_spot_distances_observed()
            expected_distances = self.reader.get_spot_distances_expected()
            for dist_observed in observed_distances:
                yield t_row % (dist_observed, expected_distances.next())
            yield t_footer

        # Add the plate areas definition.
        if 'plate_areas_definition' in report_elements:
            yield self.section(setlyze.locale.text('t-plate-areas-definition'))

            t_header, t_row, t_footer = self.table(["Area ID","Plate Area Surfaces"])

            yield t_header
            spots_definition = self.reader.get_plate_areas_definition()
            for area_id, spots in sorted(spots_definition.iteritems()):
                spots = ", ".join(spots)
                yield t_row % (area_id, spots)
            yield t_footer

        # Add the species totals per plate area.
        if 'area_totals_observed' in report_elements and \
                'area_totals_expected' in report_elements:
            yield self.section(setlyze.locale.text('t-plate-area-totals'))

            t_header, t_row, t_footer = self.table(["Area ID","Observed Totals",
                "Expected Totals"])

            yield t_header
            totals_observed = self.reader.get_area_totals_observed()
            totals_expected = self.reader.get_area_totals_expected()
            for area_id in sorted(totals_observed):
                yield t_row % \
                    (area_id,
                    totals_observed[area_id],
                    totals_expected[area_id],
                    )
            yield t_footer

        # Add the results for the Chi-squared tests (areas).
        if 'chi_squared_areas' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(['P-value','Chi squared','df',
                'Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_areas')
            for attr,items in statistics:
                yield t_row % \
                    (float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    make_remarks(items,attr),
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, areas).
        if 'wilcoxon_areas' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
                'n (observed species)', 'n (expected species)', 'P-value'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_areas')
            for attr,items in statistics:
                remarks = make_remarks(items,attr)
                yield t_row % \
                    (attr['plate_area'],
                    int(attr['n']),
                    int(attr['n_sp_observed']),
                    int(attr['n_sp_expected']),
                    float(items['p_value']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Plate Area','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_areas')
            for attr,items in statistics:
                yield t_row % \
                    (attr['plate_area'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    make_remarks(items,attr),
                    )
            yield t_footer

            # Add the results for the repeated Wilcoxon rank-sum tests.
            if 'wilcoxon_areas_repeats' in report_elements:
                yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

                t_header, t_row, t_footer = self.table(['Plate Area','n (totals)',
                    'n (observed species)','n (significant)',
                    'n (non-significant)'])

                yield t_header
                statistics = self.reader.get_statistics('wilcoxon_areas')
                statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_areas')
                for attr,items in statistics:
                    plate_area = attr['plate_area']
                    remarks = make_remarks(items,attr)
                    yield t_row % \
                        (plate_area,
                        int(attr['n']),
                        int(attr['n_sp_observed']),
                        int(statistics_repeats[plate_area]['n_significant']),
                        int(int(statistics_repeats['repeats']) - int(statistics_repeats[plate_area]['n_significant'])),
                        )
                yield t_footer

                yield "\n(table continued)\n\n"

                t_header, t_row, t_footer = self.table(['Plate Area','n (preference)',
                    'n (rejection)'])

                yield t_header
                statistics = self.reader.get_statistics('wilcoxon_areas')
                statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_areas')
                for attr,items in statistics:
                    plate_area = attr['plate_area']
                    yield t_row % \
                        (plate_area,
                        int(statistics_repeats[plate_area]['n_preference']),
                        int(statistics_repeats[plate_area]['n_rejection']),
                        )
                yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_spots' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    attr['n_plates'],
                    attr['n'],
                    float(items['p_value']),
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    make_remarks(items,attr)
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_spots_repeats' in report_elements:
            yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','n (significant)','n (non-significant)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_spots')
            for attr,items in statistics:
                n_spots = attr['n_positive_spots']
                yield t_row % \
                    (n_spots,
                    int(attr['n_plates']),
                    int(attr['n']),
                    int(statistics_repeats[n_spots]['n_significant']),
                    int(int(statistics_repeats['repeats']) - int(statistics_repeats[n_spots]['n_significant'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','n (attraction)',
                'n (repulsion)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_spots')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_spots')
            for attr,items in statistics:
                n_spots = attr['n_positive_spots']
                yield t_row % \
                    (n_spots,
                    int(statistics_repeats[n_spots]['n_attraction']),
                    int(statistics_repeats[n_spots]['n_repulsion']),
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, ratios).
        if 'wilcoxon_ratios' in report_elements:
            yield self.section(setlyze.locale.text('t-results-wilcoxon-rank-sum'))

            t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
                'n (distances)','P-value','Mean Observed','Mean Expected'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    make_remarks(items,attr)
                    )
            yield t_footer

        # Add the results for the Wilcoxon (non-repreated, spots).
        if 'wilcoxon_ratios_repeats' in report_elements:
            yield self.section(setlyze.locale.text('t-significance-results-repeats', 'Wilcoxon'))

            t_header, t_row, t_footer = self.table(['Ratio Group','n (plates)',
            'n (distances)','n (significant)','n (non-significant)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_ratios')
            for attr,items in statistics:
                ratio_group = attr['ratio_group']
                yield t_row % \
                    (ratio_group,
                    int(attr['n_plates']),
                    int(attr['n']),
                    int(statistics_repeats[ratio_group]['n_significant']),
                    int(int(statistics_repeats['repeats']) - int(statistics_repeats[ratio_group]['n_significant'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','n (attraction)',
                'n (repulsion)'])

            yield t_header
            statistics = self.reader.get_statistics('wilcoxon_ratios')
            statistics_repeats = self.reader.get_statistics_repeats('wilcoxon_ratios')
            for attr,items in statistics:
                ratio_group = attr['ratio_group']
                yield t_row % \
                    (ratio_group,
                    int(statistics_repeats[ratio_group]['n_attraction']),
                    int(statistics_repeats[ratio_group]['n_repulsion']),
                    )
            yield t_footer

        # Add the results for the Chi-squared tests (spots).
        if 'chi_squared_spots' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(['Positive Spots','n (plates)',
            'n (distances)','P-value','Chi squared','df'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_spots')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['n_positive_spots']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Positive Spots','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_spots')
            for attr,items in statistics:
                yield t_row % \
                    (attr['n_positive_spots'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    make_remarks(items,attr))
            yield t_footer

        # Add the results for the Chi-squared tests (ratios).
        if 'chi_squared_ratios' in report_elements:
            yield self.section(setlyze.locale.text('t-results-pearson-chisq'))

            t_header, t_row, t_footer = self.table(('Ratio Group','n (plates)',
                'n (distances)','P-value','Chi squared','df'))

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (int(attr['ratio_group']),
                    int(attr['n_plates']),
                    int(attr['n']),
                    float(items['p_value']),
                    float(items['chi_squared']),
                    int(float(items['df'])),
                    )
            yield t_footer

            yield "\n(table continued)\n\n"

            t_header, t_row, t_footer = self.table(['Ratio Group','Mean Observed',
                'Mean Expected','Remarks'])

            yield t_header
            statistics = self.reader.get_statistics('chi_squared_ratios')
            for attr,items in statistics:
                yield t_row % \
                    (attr['ratio_group'],
                    float(items['mean_observed']),
                    float(items['mean_expected']),
                    make_remarks(items,attr)
                    )
            yield t_footer

    def export(self, path, elements=None):
        f = open(path, 'w')
        f.writelines(self.generate(elements))
        f.close()

class ProgressDialogHandler(object):
    """This class allows you to control the progress dialog from a separate
    thread.

    Follow these steps to get the progress dialog working:

    1) In the main thread, create a progress dialog, ::

        pd = setlyze.gui.ProgressDialog(title="Analyzing",
            description="Performing heavy calculations, please wait...")

    2) Make the progress dialog global using the :mod:`setlyze.config` module, ::

        setlyze.config.cfg.set('progress-dialog', pd)

    3) Edit the worker process to automatically update the progress dialog.
       First create an instance of this class in the __init__() of your class: ::

            self.pdialog_handler = setlyze.std.ProgressDialogHandler()

    4) Then you need to tell the handler how many times you're going to update
       the progress dialog (which is the number of times you'll call the
       :meth:`increase` method): ::

            self.pdialog_handler.set_total_steps(8)

    5) Then call the :meth:`increase` method in you worker class at the moments
       you want to update the progress dialog. Notice that :meth:`increase`
       will be called 8 times in the example below (hence total steps was set
       to 8): ::

            self.pdialog_handler.set_action("Calculating this...")
            self.some_heavy_function()

            self.pdialog_handler.increase("Still calculating...")
            for x in range(5):
                self.pdialog_handler.increase()
                self.calculate_this(x)

            self.pdialog_handler.increase("Calculating that...")
            self.more_heavy_calculations()

            self.pdialog_handler.increase("Finished!")

    6) Then start your worker process in a separate thread (if you're new to
       threading, start with the `threading documentation
       <http://docs.python.org/library/threading.html>`_) ::

        t = WorkerClass()
        t.start()

    The progress bar should now increase while the worker process is running.
    For more examples you can look at the sources of the analysis modules (e.g.
    :mod:`setlyze.analysis.spot_preference`).

    """

    def __init__(self):
        self.total_steps = None
        self.current_step = 0
        self.autoclose = True
        self.pdialog = setlyze.config.cfg.get('progress-dialog')

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

    def update(self, fraction, action=None):
        """Set the progress dialog's progress bar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.

        The "progress-dialog" configuration must be set to an instance of
        :class:`setlyze.gui.ProgressDialog` for this to work. If no progress
        dialog is set, nothing will happen.
        """
        # If no progress dialog is set, do nothing.
        if not self.pdialog:
            return

        # In case this is always called from a separate thread, so we must use
        # gobject.idle_add to access the GUI.
        gobject.idle_add(self.__update_progress_dialog, fraction, action)

    def __update_progress_dialog(self, fraction, action=None):
        """Set the progress dialog's progressbar fraction to `fraction`.
        The value of `fraction` should be between 0.0 and 1.0. Optionally set
        the current action to `action`, a short string explaining the current
        action.

        Don't call this function manually; use :meth:`increase` instead.
        """

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
            self.pdialog.button_close.set_sensitive(True)

            if self.autoclose:
                # Close the progress dialog when finished. We set a delay
                # of 1 second before closing it, so the user gets to see the
                # dialog when an analysis finishes very fast.

                # This is always called from a separate thread, so we must
                # use gobject.idle_add to access the GUI.
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

        # If a delay is set, sleep 'delay' seconds.
        if delay: time.sleep(delay)

        # Close the progress dialog.
        self.pdialog.destroy()

        # This callback function must return False, so it is
        # automatically removed from the list of event sources.
        return False

# Register the Sender class as an official GType.
gobject.type_register(Sender)

# Create a sender object which will send all the application signals.
sender = Sender()