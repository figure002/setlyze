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

import sys
import os.path
import pkg_resources

__copyright__ = "Copyright 2010-2015, GiMaRIS"
__credits__ = ["Jonathan den Boer",
    "Serrano Pereira <serrano.pereira@gmail.com>",
    "Adam van Adrichem <a.v.adrichem@gmail.com>",
    "Fedde Schaeffer <fedde.schaeffer@gmail.com>"]
__license__ = "GPL3"
__version__ = "1.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2015/02/24"

def we_are_frozen():
    """Returns True if frozen via py2exe."""
    return hasattr(sys, "frozen")

def module_path():
    """Return nodule path even if we are frozen using py2exe."""
    if we_are_frozen():
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

def resource_filename(resource_name):
    """Return file path for package resource."""
    if we_are_frozen():
        return os.path.join(module_path(), resource_name)
    return pkg_resources.resource_filename(__name__, resource_name)
