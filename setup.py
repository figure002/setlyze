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

import os
import glob

from setuptools import setup

"""Installer script for SETLyze. For installation instructions, see the
INSTALL file.
"""

def recursive_get_folder_patterns(pattern):
    patterns = []
    ls = glob.glob(pattern)
    for f in ls:
        if os.path.isdir(f):
            pattern = "%s/*" % f
            patterns.append(pattern)
    for pattern in patterns:
        patterns.extend(recursive_get_folder_patterns(pattern))
    return patterns

def transform_folder_patterns(patterns):
    for i, p in enumerate(patterns):
        # Make sure we only get files with extensions.
        if p.endswith('/*'):
            p = p.replace('/*', '/*.*')
        # Leave out the 'setlyze/' part at the beginning.
        if p.startswith('setlyze/'):
            patterns[i] = p[8:]
        else:
            patterns[i] = p
    return patterns

# Compile a list of patterns pointing to SETLyze's package data.
package_data_setlyze = recursive_get_folder_patterns('setlyze/docs/*')
package_data_setlyze = transform_folder_patterns(package_data_setlyze)
package_data_setlyze.extend(['docs/*.*'])
package_data_setlyze.extend(['images/*.*'])

setup(name = 'setlyze',
    version = '0.1',
    description = "A tool for analyzing the settlement of species on SETL plates.",
    long_description = "A tool for analyzing the settlement of species on SETL plates.",
    author = 'Serrano Pereira',
    author_email = 'serrano.pereira@gmail.com',
    license = 'GPL3',
    platforms = ['GNU/Linux','Windows'],
    scripts = ['setlyze.pyw'],
    url = 'http://www.gimaris.com/',
    keywords = 'gimaris invasive species settlement setl analysis',
    classifiers = [
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ],
    install_requires = [
        'setuptools',
        'pygtk >= 2.22',
        'pygobject >= 2.26',
        'pycairo >= 1.8.6',
        'rpy >= 1.0.3',
        'pywin32',
        ],
    packages = [
        'setlyze',
        'setlyze.analysis'
        ],
    package_data = {
        'setlyze': package_data_setlyze
        },
)
