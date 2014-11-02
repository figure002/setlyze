#!/usr/bin/env python

import os
import timeit
from sqlite3 import dbapi2 as sqlite

import setlyze.std

connection = sqlite.connect(os.path.expanduser('~/.setlyze/setl_local.db'))
cursor = connection.cursor()

test_record = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]

def test1():
    """Get pre-calculated spot distances from the local database."""
    combos = setlyze.std.get_spot_combinations_from_record(test_record)

    for spot1,spot2 in combos:
        h,v = setlyze.std.get_spot_position_difference(spot1,spot2)
        cursor.execute( "SELECT distance "
                         "FROM spot_distances "
                         "WHERE delta_x = ? "
                         "AND delta_y = ?",
                         (h,v))
        distance = cursor.fetchone()

def test2():
    """Calculate spot distances on run time."""
    combos = setlyze.std.get_spot_combinations_from_record(test_record)

    for spot1,spot2 in combos:
        h,v = setlyze.std.get_spot_position_difference(spot1,spot2)
        distance = setlyze.std.distance(h,v)

# Time both tests.
runs = 1000
t = timeit.Timer("test1()", "from __main__ import test1")
print "test1: %f seconds" % (t.timeit(runs)/runs)

t = timeit.Timer("test2()", "from __main__ import test2")
print "test2: %f seconds" % (t.timeit(runs)/runs)

cursor.close()
connection.close()
