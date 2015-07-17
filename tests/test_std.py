#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unit test for :mod:`setlyze.std`."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('.'))

import setlyze.std as std

class TestStd(unittest.TestCase):

    """Unit tests for :mod:`setlyze.std`."""

    def test_get_spots_from_record(self):
        test_data = (
            (
                (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
                ()
            ),
            (
                (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1),
                (25,)
            ),
            (
                (1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0),
                (1, 2, 5, 15)
            ),
        )

        for record, expected in test_data:
            spots = std.get_spots_from_record(record)
            self.assertEqual(set(spots), set(expected))

    def test_get_spot_combinations_from_record(self):
        # Test with one record.
        test_data = (
            (
                (0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
                (),
            ),
            (
                (0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1),
                (
                    (3,25),
                )
            ),
            (
                (1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0),
                (
                    (1,2),
                    (1,5),
                    (1,15),
                    (2,5),
                    (2,15),
                    (5,15),
                )
            ),
        )

        for record, expected in test_data:
            combos = std.get_spot_combinations_from_record(record)
            self.assertEqual(set(combos), set(expected))

        # Test with two records.
        test_data = (
            (
                (
                    (0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0),
                    (0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
                ),
                ()
            ),
            (
                (
                    (0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
                    (0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0),
                ),
                (
                    (8,12),
                )
            ),
            (
                (
                    (1,1,0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0),
                    (0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1)
                ),
                (
                    (1,3),
                    (1,25),
                    (2,3),
                    (2,25),
                    (5,3),
                    (5,25),
                    (15,3),
                    (15,25),
                )
            ),
        )

        for (a, b), expected in test_data:
            combos = std.get_spot_combinations_from_record(a, b)
            self.assertEqual(set(combos), set(expected))

if __name__ == '__main__':
    unittest.main()
