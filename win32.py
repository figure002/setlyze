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

import glob

from distutils.core import setup
import py2exe

from setlyze import __version__

"""This setup script is used to create the py2exe executable of SETLyze. Do
*not* use this script to install SETLyze. That's what setup.py is for.

On Windows, follow these steps to create the SETLyze executable for Windows:

1) Build the Windows executable with `python win32.py py2exe`. This should
   create a 'dist' folder.

2) Build the documentation with `python setup.py build_sphinx` and copy the
   folder 'build/sphinx/html/' to the aforementioned 'dist' folder and rename it
   to "docs".

3) Manually copy the following folders to the 'dist' folder:

   C:\Program Files\GTK2-Runtime\etc\
   C:\Program Files\GTK2-Runtime\lib\
   C:\Program Files\GTK2-Runtime\share\

   These folders are a part of the GTK2-Runtime. Without these three folders,
   SETLyze would look very ugly on Windows without a GTK2-Runtime installed.

4) Test the new executable by running 'setlyze.exe' in the 'dist' folder. If
   everything works fine, you can use the 'dist' folder to create a Windows
   installer using Nullsoft Scriptable Installer System (NSIS). The NSIS script
   used to create the Windows setup is called 'setlyze.nsi'. To create
   the Windows installer for SETLyze, make sure you have NSIS installed. Then
   simply right-click the 'setlyze.nsi' file and select "Compile
   NSIS Script". This should produce the Windows installer, called something
   like 'setlyze-x.x-bundle-win32.exe'.

"""

setup(name='setlyze',
    version=__version__,
    description='A tool for analyzing the settlement of species.',
    long_description='A tool for analyzing the settlement of species.',
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    url='http://www.gimaris.com/',
    packages=['setlyze','setlyze.analysis'],
    windows = [
        {'script': 'setlyze/main.py',
        'icon_resources': [(1, 'data/graphics/icons/setlyze.ico')],
        }
    ],
    options= {
        'py2exe': {
            'includes': 'pango,atk,gobject,gio,cairo,pangocairo,_rpy2121',
            'dll_excludes': 'R.dll',
        },
    },
    data_files=[
        ('test-data/CSV', glob.glob('tests/data/CSV/*.*')),
        ('test-data/Excel', glob.glob('tests/data/Excel/*.*')),
        ('glade', glob.glob('setlyze/glade/*.*')),
        ('images', glob.glob('setlyze/images/*.*')),
        ('.', ['*.txt','*.rst']),
    ],
)
