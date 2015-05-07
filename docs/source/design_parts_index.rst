.. _design-parts:

============
Design Parts
============

1.x Modules, Classes & Functions
================================

==================  =================================
Design Part #       Reference
==================  =================================
1.0                 The executable for SETLyze (``setlyze.pyw``).
1.1                 The :meth:`main` function in the executable.
1.2					:class:`setlyze.database.MakeLocalDB`
1.3					:mod:`setlyze.analysis.spot_preference`
1.3.1 				:class:`setlyze.analysis.spot_preference.Begin`
1.3.2 				:class:`setlyze.analysis.spot_preference.BeginBatch`
1.3.3 				:class:`setlyze.analysis.spot_preference.Analysis`
1.4 				:mod:`setlyze.analysis.attraction_intra`
1.4.1 				:class:`setlyze.analysis.attraction_intra.Begin`
1.4.2 				:class:`setlyze.analysis.attraction_intra.BeginBatch`
1.4.3 				:class:`setlyze.analysis.attraction_intra.Analysis`
1.5 				:mod:`setlyze.analysis.attraction_inter`
1.5.1 				:class:`setlyze.analysis.attraction_inter.Begin`
1.5.2 				:class:`setlyze.analysis.attraction_inter.BeginBatch`
1.5.3 				:class:`setlyze.analysis.attraction_inter.Analysis`
1.11 				:meth:`setlyze.gui.SelectionWindow.on_load_data`
1.12 				:class:`setlyze.report.Report`
1.13 				:meth:`setlyze.analysis.spot_preference.Analysis.generate_report`
1.14 				:meth:`setlyze.analysis.attraction_intra.Analysis.generate_report`
1.15 				:meth:`setlyze.analysis.attraction_inter.Analysis.generate_report`
1.17 				:meth:`setlyze.report.export`
1.19.1 				:meth:`setlyze.database.AccessLocalDB.set_species_spots`
1.20 				:meth:`setlyze.database.AccessDBGeneric.make_plates_unique`
1.22 				:meth:`setlyze.analysis.attraction_intra.Analysis.calculate_distances_intra`
1.23 				:meth:`setlyze.analysis.attraction_intra.Analysis.calculate_distances_intra_expected`
1.24 				:meth:`setlyze.analysis.attraction_intra.Analysis.calculate_significance`
1.27 				:meth:`setlyze.analysis.attraction_inter.Analysis.calculate_distances_inter`
1.28 				:class:`setlyze.database.AccessLocalDB`
1.29 				:class:`setlyze.database.AccessRemoteDB`
1.31 				:meth:`setlyze.database.MakeLocalDB.run`
1.32 				:meth:`setlyze.database.MakeLocalDB.insert_from_data_files`
1.33 				:meth:`setlyze.database.MakeLocalDB.insert_from_db`
1.34.1 				:meth:`setlyze.database.MakeLocalDB.insert_locations_from_csv`
1.34.2 				:meth:`setlyze.database.MakeLocalDB.insert_locations_from_xls`
1.35.1 				:meth:`setlyze.database.MakeLocalDB.insert_species_from_csv`
1.35.2 				:meth:`setlyze.database.MakeLocalDB.insert_species_from_xls`
1.36.1 				:meth:`setlyze.database.MakeLocalDB.insert_plates_from_csv`
1.36.2 				:meth:`setlyze.database.MakeLocalDB.insert_plates_from_xls`
1.37.1				:meth:`setlyze.database.MakeLocalDB.insert_records_from_csv`
1.37.2				:meth:`setlyze.database.MakeLocalDB.insert_records_from_xls`
1.38 				:meth:`setlyze.database.MakeLocalDB.create_new_db`
1.39 				:meth:`setlyze.gui.SelectionWindow.update_tree`
1.41.1 				:meth:`setlyze.database.AccessLocalDB.get_record_ids`
1.42 				:meth:`setlyze.gui.SelectLocations.create_model`
1.43 				:meth:`setlyze.gui.SelectSpecies.create_model`
1.44 				:meth:`setlyze.gui.SelectionWindow.on_continue`
1.45 				:meth:`setlyze.gui.SelectionWindow.on_back`
1.48 				:class:`setlyze.report.Report`
1.50 				:meth:`setlyze.report.Report.set_location_selections`
1.51 				:meth:`setlyze.report.Report.set_species_selections`
1.52 				:meth:`setlyze.report.Report.set_spot_distances_observed`
1.53 				:meth:`setlyze.report.Report.set_spot_distances_expected`
1.54 				:meth:`setlyze.report.Report.set_plate_areas_definition`
1.55 				:meth:`setlyze.report.Report.set_area_totals_observed`
1.56 				:meth:`setlyze.report.Report.set_area_totals_expected`
1.57 				:class:`setlyze.config.ConfigManager`
1.58 				:meth:`setlyze.analysis.spot_preference.Analysis.run`
1.59 				:meth:`setlyze.analysis.attraction_intra.Analysis.run`
1.60 				:meth:`setlyze.analysis.attraction_inter.Analysis.run`
1.62 				:meth:`setlyze.analysis.spot_preference.Analysis.set_plate_area_totals_observed`
1.63 				:meth:`setlyze.analysis.spot_preference.Analysis.set_plate_area_totals_expected`
1.64 				:meth:`setlyze.analysis.spot_preference.Analysis.get_defined_areas_totals_observed`
1.65 				:meth:`setlyze.analysis.spot_preference.Analysis.repeat_wilcoxon_test`
1.68 				:meth:`setlyze.analysis.common.PrepareAnalysis.on_display_results`
1.69 				:meth:`setlyze.analysis.attraction_inter.Analysis.calculate_distances_inter_expected`
1.70 				:meth:`setlyze.report.Report.set_statistics`
1.72 				:meth:`setlyze.report.Report.set_analysis`
1.73 				:meth:`setlyze.database.AccessDBGeneric.fill_plate_spot_totals_table`
1.74 				:meth:`setlyze.analysis.attraction_inter.Analysis.calculate_significance`
1.75 				:meth:`setlyze.database.MakeLocalDB.create_table_info`
1.76 				:meth:`setlyze.database.MakeLocalDB.create_table_localities`
1.77 				:meth:`setlyze.database.MakeLocalDB.create_table_species`
1.78 				:meth:`setlyze.database.MakeLocalDB.create_table_plates`
1.79 				:meth:`setlyze.database.MakeLocalDB.create_table_records`
1.80 				:meth:`setlyze.database.AccessLocalDB.create_table_species_spots_1`
1.81 				:meth:`setlyze.database.AccessLocalDB.create_table_species_spots_2`
1.83 				:meth:`setlyze.database.AccessLocalDB.create_table_spot_distances_observed`
1.84 				:meth:`setlyze.database.AccessLocalDB.create_table_spot_distances_expected`
1.85 				:meth:`setlyze.database.AccessLocalDB.create_table_plate_spot_totals`
1.86                :class:`setlyze.gui.SelectAnalysis`
1.87                :class:`setlyze.gui.SelectLocations`
1.88                :class:`setlyze.gui.SelectSpecies`
1.89                :class:`setlyze.gui.Report`
1.90                :class:`setlyze.gui.LoadData`
1.91                :class:`setlyze.gui.DefinePlateAreas`
1.92                :class:`setlyze.gui.ProgressDialog`
1.93 				:meth:`setlyze.database.get_database_accessor`
1.94                :class:`setlyze.std.Sender`
1.95                :meth:`setlyze.database.AccessDBGeneric.get_locations`
1.96                :meth:`setlyze.database.AccessLocalDB.get_species`
1.98 				:meth:`setlyze.analysis.spot_preference.Analysis.calculate_significance_wilcoxon`
1.99 				:meth:`setlyze.analysis.spot_preference.Analysis.calculate_significance_chisq`
1.100 				:meth:`setlyze.analysis.spot_preference.Analysis.wilcoxon_test_for_repeats`
1.101 				:meth:`setlyze.analysis.spot_preference.Analysis.get_area_probabilities`
1.102 				:meth:`setlyze.analysis.attraction_intra.Analysis.wilcoxon_test_for_repeats`
1.103 				:meth:`setlyze.analysis.attraction_intra.Analysis.repeat_wilcoxon_test`
1.104 				:meth:`setlyze.analysis.attraction_inter.Analysis.wilcoxon_test_for_repeats`
1.105 				:meth:`setlyze.analysis.attraction_inter.Analysis.repeat_wilcoxon_test`
==================  =================================

2.x Data Storage Places
=======================

.. toctree::
   :maxdepth: 4

   design_parts_data

3.x Graphical User Interfaces
=============================

==================  =================================
Design Part #       Reference
==================  =================================
3.0                 :ref:`dialog-analysis-selection`
3.1                 :ref:`dialog-loc-selection`
3.2                 :ref:`dialog-spe-selection`
3.3                 :ref:`dialog-analysis-report`
3.4                 :ref:`dialog-load-data`
3.5                 :ref:`dialog-define-plate-areas`
3.6                 :ref:`dialog-preferences`
3.7                 :ref:`dialog-batch-mode`
==================  =================================

4.x Documents
=============================

.. toctree::
   :maxdepth: 4

   design_parts_docs
