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

"""This is a standalone script for generating a SQLite database file
with random generated spot distances. This script was used to calculate
the probabilities for all spot distances (both intra- and inter-specific).

The probabilities calculated by this script have been hard-coded into
SETLyze (:mod:`setlyze.config`).

The probabilities have been calculated with the following settings:

For intra-specific spot distances: ::

    METHOD = 1
    SPOTS = 25
    RUNS = 1

For inter-specific spot distances: ::

    METHOD = 2
    RATIO = (25,25)
    RUNS = 1

The calculated spot distances saved in the database file can be exported
to a CSV file with the following command: ::

    sqlite3 -csv -separator ',' spot_distances.sqlite "SELECT distance FROM spot_distances;" > spot_distances.csv

This CSV file can be used to generate histograms in R.

"""

import os
from sqlite3 import dbapi2 as sqlite
import itertools
import tempfile

import setlyze.config
import setlyze.std

# 1 = Generate intra-specific spot distances.
# 2 = Generate inter-specific spot distances.
METHOD = 1

# For method 1: Number of random spots to put on a plate.
SPOTS = 25

# For method 2: Ratios to generate (e.g. (1,2) means ratio 1:2).
RATIO = (25,25)

# How many times to run the randomizer. Each run creates:
# - Method 1: One fictional SETL plate with SPOTS random spots.
# - Method 2: Two fictional SETL plates with random spots. One plate
#   has RATIO[0] random spots, the other plate has RATIO[1] random
#   spots.
RUNS = 1

# Path to the temporary database file.
DBFILE = os.path.join('.', 'spot_distances.sqlite')

def create_table_distances():
    # Make a connection with the local database.
    connection = sqlite.connect(DBFILE)
    cursor = connection.cursor()

    # Design Part: 2.12
    cursor.execute("CREATE TABLE spot_distances (\
        id INTEGER PRIMARY KEY, \
        distance REAL \
    )")

    # Commit the transaction.
    connection.commit()

    # Close connection with the local database.
    cursor.close()
    connection.close()

def calculate_distances():
    connection = sqlite.connect(DBFILE)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM spot_distances")
    connection.commit()

    for x in range(RUNS):
        if METHOD == 1:
            random_spots = setlyze.std.get_random_for_plate(SPOTS)

            combos = itertools.combinations(random_spots, 2)
        elif METHOD == 2:
            random_spots1 = setlyze.std.get_random_for_plate(RATIO[0])
            random_spots2 = setlyze.std.get_random_for_plate(RATIO[1])

            combos = itertools.product(random_spots1,random_spots2)
        else:
            raise ValueError("Unknown method.")

        for spot1,spot2 in combos:
            h,v = setlyze.std.get_spot_position_difference(spot1,spot2)

            distance = setlyze.std.distance(h,v)

            cursor.execute( "INSERT INTO spot_distances "
                             "VALUES (null,?)", (distance,) )

    connection.commit()

    cursor.close()
    connection.close()

def info():
    if METHOD == 1:
        possible_distances = (1,1.41,2,2.24,2.83,3,3.16,3.61,4,4.12,4.24,4.47,5,5.66)
    elif METHOD == 2:
        possible_distances = (0,1,1.41,2,2.24,2.83,3,3.16,3.61,4,4.12,4.24,4.47,5,5.66)

    connection = sqlite.connect(DBFILE)
    cursor = connection.cursor()


    cursor.execute("SELECT COUNT(distance) FROM spot_distances")
    total = cursor.fetchone()[0]

    print "\nResults"
    print "-------------------------"
    print "Total distances:", total
    print "%10s %10s %11s" % ("Distance","Fequency","Probability")
    for dist in possible_distances:
        cursor.execute("SELECT COUNT(distance) FROM spot_distances WHERE distance = ?", (dist,))
        f = cursor.fetchone()[0]
        print "%10s %10d %11f" % (dist, f, float(f)/total)

    cursor.close()
    connection.close()

def dictionary():
    if METHOD == 1:
        possible_distances = (1,1.41,2,2.24,2.83,3,3.16,3.61,4,4.12,4.24,4.47,5,5.66)
    elif METHOD == 2:
        possible_distances = (0,1,1.41,2,2.24,2.83,3,3.16,3.61,4,4.12,4.24,4.47,5,5.66)

    connection = sqlite.connect(DBFILE)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(distance) FROM spot_distances")
    total = cursor.fetchone()[0]

    print "\nPython dictionary"
    print "-------------------------"
    print "{"
    for dist in possible_distances:
        cursor.execute("SELECT COUNT(distance) FROM spot_distances WHERE distance = ?", (dist,))
        f = cursor.fetchone()[0]
        print "%-5s: %d/%.1f," % (dist, f, total)
    print "}"

    cursor.close()
    connection.close()

if not os.path.isfile(DBFILE):
    create_table_distances()

print "Calculating distances..."

calculate_distances()
info()
dictionary()
