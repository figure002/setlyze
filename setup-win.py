#!/usr/bin/env python

import glob

from distutils.core import setup
import py2exe

"""This setup script is used to create the py2exe executable of SETLyze. Do
*not* use this script to install SETLyze. To install SETLyze, use 'setup.py'
instead.
"""

setup(name='setlyze',
    version='0.1',
    description='A tool for analyzing the settlement of species.',
    long_description='A tool for analyzing the settlement of species.',
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    platforms=['GNU/Linux','Windows'],
    url='http://www.gimaris.com/',
    packages=['setlyze','setlyze.analysis'],

    scripts=['setlyze.pyw'],
    windows = [
        {'script': 'setlyze.pyw',
        'icon_resources': [(1, 'icon.ico')],
        }
    ],
    options= {
        'py2exe': {
            'includes': 'pango,atk,gobject,gio,cairo,pangocairo,_rpy2091',
            'dll_excludes': [],
            },
    },
    data_files=[('test-data', glob.glob('test-data/*.*')),
        ('tests', glob.glob('tests/*.*')),
        ('images', glob.glob('setlyze/images/*.*')),
        ('.',['COPYING','icon.ico','README']),
        # Don't forget to manually copy the 'setlyze/docs/' folder to the
        # 'dist' folder before creating setup.exe.
        ],
)
