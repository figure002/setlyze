#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010-2015, GiMaRIS <info@gimaris.com>
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

"""Statistics related functions."""

import itertools
import random

from pandas.core.series import Series
from pandas.rpy.common import convert_robj
import rpy2
import rpy2.robjects as robjects
from rpy2.rinterface import NULL
from rpy2.robjects import FloatVector
from rpy2.robjects.packages import importr

# Get the R singleton.
r = robjects.r
stats = importr('stats')

# Suppress warnings from R. Last occurred warnings can still be obtained with
# the `warnings` function.
r['options'](warn=-1)

class ListVectorAsDict(object):

    """Function decorator to return type ``ListVector`` as ``dict``."""

    def __init__(self, f):
        self.f = f

    def __call__(self, *args, **kwargs):
        out = self.f(*args, **kwargs)
        if isinstance(out, robjects.vectors.ListVector):
            return self.simplify( convert_robj(out) )
        return out

    def simplify(self, obj):
        """Return a simplified version of the statistics dictionary `obj`.

        Lists containing only a single item are returned as single items and
        ``rpy2.rinterface.NULL`` values are converted to None.
        """
        if obj is NULL:
            return None
        if isinstance(obj, Series):
            obj = dict(obj)

        # Return the original object if it is not iterable.
        try:
            _ = (x for x in obj)
        except TypeError:
            return obj

        if isinstance(obj, dict):
            # Recurse into dictionary values.
            for k in obj:
                obj[k] = self.simplify(obj[k])
        elif len(obj) == 1:
            # Return the first item if the list contains just one object.
            if obj[0] is NULL:
                return None
            return obj[0]
        elif isinstance(obj, list):
            # Recurse into the list items.
            for i, e in enumerate(obj):
                obj[i] = self.simplify(e)

        return obj

@ListVectorAsDict
def t_test(x, y=NULL, **kwargs):
    """Performs one and two sample t-tests on sequences of data.

    This is a wrapper function for the ``t.test`` function from R. It depends on
    R and RPy. The latter provides an interface to the R Programming Language.

    This function returns a dictionary containing the results. Below is the
    format of the dictionary with example results ::

        {
            'null.value': {
                'difference in means': 0
            },
            'method': 'Welch Two Sample t-test',
            'p.value': 0.97053139295765201,
            'statistic': {
                't': -0.037113583386291726
            },
            'estimate': {
                'mean of y': 2.552142857142857,
                'mean of x': 2.5417857142857141
            },
            'conf.int': [-0.56985924418141154, 0.54914495846712563],
            'parameter': {'df': 53.965197921982607},
            'alternative': 'two.sided'
        }
    """
    x = FloatVector(x)
    if y:
        y = FloatVector(y)
    return stats.t_test(x, y, **kwargs)

@ListVectorAsDict
def wilcox_test(x, y=NULL, **kwargs):
    """Performs one and two sample Wilcoxon tests on sequences of data;
    the latter is also known as ‘Mann-Whitney’ test.

    This is a wrapper function for the ``wilcox.test`` function from R. It
    depends on R and RPy. The latter provides an interface to the R Programming
    Language.

    This function returns a dictionary containing the results. Below is the
    format of the dictionary with example results ::

        {
            'estimate': {
                'difference in location': -2.0000005809455006
            },
            'null.value': {
                'location shift': 0
            },
            'p.value': 0.000810583642587086,
            'statistic': {
                'W': 1.0
            },
            'alternative': 'two.sided',
            'conf.int': [-3.1200287512799796, -1.2399735289828238],
            'parameter': None,
            'method': 'Wilcoxon rank sum test with continuity correction'
        }
    """
    x = FloatVector(x)
    if y:
        y = FloatVector(y)
    return stats.wilcox_test(x, y, **kwargs)

@ListVectorAsDict
def shapiro_test(x):
    """Performs the Shapiro-Wilk test of normality.

    This is a wrapper function for the ``shapiro.test`` function from R. It
    depends on R and RPy. The latter provides an interface to the R Programming
    Language.

    The data sequence `x` passed to the ``shapiro.test`` function must contain
    between 3 and 5000 numberic values. If the length of `x` is below 3, a
    ValueError is raised. If the length of `x` is above 5000,
    :py:meth:`random.sample` is used to get 5000 random values from `x`.

    This function returns a dictionary containing the results. Below is the
    format of the dictionary with example results ::

        {
            'method': 'Shapiro-Wilk normality test',
            'p.value': 6.862712394148655e-08,
            'statistic': {'W': 0.75000003111895985}
        }
    """
    if len(x) > 5000:
        x = random.sample(x, 5000)
    elif len(x) < 3:
        raise ValueError("Argument 'x' must contain at least 3 numeric values.")

    return stats.shapiro_test( FloatVector(x) )

@ListVectorAsDict
def chisq_test(x, y=NULL, **kwargs):
    """Performs chi-squared contingency table tests and
     goodness-of-fit tests.

    This is a wrapper function for the ``chisq.test`` function from R. It
    depends on R and RPy. The latter provides an interface to the R
    Programming Language.

    This function returns a dictionary containing the results. Below
    is the format of the dictionary with example results ::

        {
            'null.value': {
                'difference in means': 0
            },
            'method': 'Welch Two Sample t-test',
            'p.value': 0.97053139295765201,
            'statistic': {
                't': -0.037113583386291726
            },
            'estimate': {
                'mean of y': 2.552142857142857,
                'mean of x': 2.5417857142857141
            },
            'conf.int': [-0.56985924418141154, 0.54914495846712563],
            'parameter': {
                'df': 53.965197921982607
            },
            'alternative': 'two.sided'
        }
    """
    if 'p' not in kwargs:
        kwargs['p'] = itertools.repeat(1.0 / len(x), len(x))
    kwargs['p'] = FloatVector( list(kwargs['p']) )

    x = FloatVector(x)
    if y:
        y = FloatVector(y)

    return stats.chisq_test(x, y, **kwargs)
