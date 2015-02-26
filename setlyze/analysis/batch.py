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

"""Start an analysis in batch mode.

Batch mode for an analysis is started by instantiating its :class:`BeginBatch`
class. In batch mode, the selected analysis is repeated for a selection of
species. The user can select multiple species and the analysis is repeated for
each species separately and the results are displayed in a summary report.
"""

import logging

import setlyze
from setlyze.analysis.common import PrepareAnalysis
from setlyze.gui import select_batch_analysis
from setlyze.analysis import (spot_preference, attraction_intra,
    attraction_inter, relations)

class Begin(PrepareAnalysis):

    """Start an analysis in batch mode.

    First the user can select which analysis to start, then the analysis is
    started in batch mode.
    """

    def __init__(self):
        super(Begin, self).__init__()
        # Set some signal handlers.
        self.signal_handlers = {
            # Unset signal handlers of this class once an analysis has started.
            'beginning-analysis': setlyze.sender.connect('beginning-analysis', self.unset_signal_handlers),
            # The batch analysis selection window back button was clicked.
            'select-batch-analysis-window-back': setlyze.sender.connect('select-batch-analysis-window-back', self.on_analysis_closed),
            # An analysis was selected.
            'batch-analysis-selected': setlyze.sender.connect('batch-analysis-selected', self.on_analysis_selected),
        }
        # Display the window for selecting the batch analysis.
        select_batch_analysis.show()

    def on_analysis_selected(self, sender, analysis):
        """Start the selected analysis `analysis` in batch mode."""
        if analysis == 'spot_preference':
            spot_preference.BeginBatch()
        elif analysis == 'attraction_intra':
            attraction_intra.BeginBatch()
        elif analysis == 'attraction_inter':
            attraction_inter.BeginBatch()
        elif analysis == 'relations':
            relations.BeginBatch()
