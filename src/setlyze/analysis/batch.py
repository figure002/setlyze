#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, 2011, GiMaRIS <info@gimaris.com>
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

"""This module starts analyses in batch mode.

The selected analysis is repeated for a selection of species. If all species
are selected by the user, the analysis is repeated for each species and the
results are displayed in a single report.
"""

import logging

import setlyze.gui
import setlyze.std
import setlyze.analysis.common
import setlyze.analysis.spot_preference
import setlyze.analysis.attraction_intra
import setlyze.analysis.attraction_inter
import setlyze.analysis.relations

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

class Begin(setlyze.analysis.common.PrepareAnalysis):
    """Select which analysis to run in batch mode:

    1. Let the user select an analysis.
    2. Run the analysis in batch mode.
    """

    def __init__(self):
        super(Begin, self).__init__()
        logging.info("Entering batch mode")

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Display the window for selecting the batch analysis. This signal
        # makes the main window hide.
        self.w = setlyze.gui.SelectBatchAnalysis()

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_close),
            # The batch analysis selection window back button was clicked.
            'select-batch-analysis-window-back': setlyze.std.sender.connect('select-batch-analysis-window-back', self.on_analysis_closed),
            # An analysis was selected.
            'batch-analysis-selected': setlyze.std.sender.connect('batch-analysis-selected', self.on_analysis_selected),
        }

    def on_close(self, sender=None, data=None):
        """Display the window for selecting the batch analysis."""
        self.unset_signal_handlers()
        self.w.destroy()

    def on_analysis_selected(self, sender, analysis):
        """Start the selected analysis in batch mode."""
        if analysis == 'spot_preference':
            setlyze.analysis.spot_preference.BeginBatch()
        elif analysis == 'attraction_intra':
            setlyze.analysis.attraction_intra.BeginBatch()
        elif analysis == 'attraction_inter':
            setlyze.analysis.attraction_inter.BeginBatch()
        elif analysis == 'relations':
            setlyze.analysis.relations.BeginBatch()
