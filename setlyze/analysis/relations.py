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

import logging

from setlyze.analysis.common import PrepareAnalysis
import setlyze.locale
import setlyze.config
import setlyze.gui

class Begin(PrepareAnalysis):
    def __init__(self):
        logging.info("Beginning analysis Relation between Species")
        setlyze.gui.on_not_implemented()

class BeginBatch(Begin):
    def __init__(self):
        super(BeginBatch, self).__init__()
        logging.info("We are in batch mode")
