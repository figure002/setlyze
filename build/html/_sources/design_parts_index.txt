=================================
SETLyze Design Parts
=================================

1.x Modules, Classes & Functions
================================

==================  =================================
Design Part #       Reference
==================  =================================
1.0                 The executable for SETLyze.
1.1                 The initial function for SETLyze.
1.2					:class:`setlyze.database.MakeLocalDB`
1.3					:mod:`setlyze.analysis.spot_preference`
1.3.1 				:class:`setlyze.analysis.spot_preference.Begin`
1.3.2 				:class:`setlyze.analysis.spot_preference.Start`
1.4 				:mod:`setlyze.analysis.attraction_intra`
1.4.1 				:class:`setlyze.analysis.attraction_intra.Begin`
1.4.2 				:class:`setlyze.analysis.attraction_intra.Start`
1.5 				:mod:`setlyze.analysis.attraction_inter`
1.5.1 				:class:`setlyze.analysis.attraction_inter.Begin`
1.5.2 				:class:`setlyze.analysis.attraction_inter.Start`
1.6 				:mod:`setlyze.analysis.relations`
1.6.1 				:class:`setlyze.analysis.relations.Begin`
1.6.2 				:class:`setlyze.analysis.relations.Start`
1.7 				:meth:`setlyze.gui.SelectLocations.save_selection`
1.8 				:meth:`setlyze.gui.SelectSpecies.save_selection`
1.11 				:meth:`setlyze.gui.SelectionWindow.on_change_data_source`
1.12 				:class:`setlyze.std.ReportGenerator`
1.13 				:meth:`setlyze.analysis.spot_preference.Start.generate_report`
1.14 				:meth:`setlyze.analysis.attraction_intra.Start.generate_report`
1.15 				:meth:`setlyze.analysis.attraction_inter.Start.generate_report`
1.16 				:meth:`setlyze.analysis.relations.Start.generate_report`
1.17 				:meth:`setlyze.std.export_report`
1.19.1 				:meth:`setlyze.database.AccessLocalDB.set_species_spots`
1.19.2 				:meth:`setlyze.database.AccessRemoteDB.set_species_spots`
1.20 				:meth:`setlyze.database.AccessDBGeneric.make_plates_unique`
1.21 				:meth:`setlyze.database.AccessDBGeneric.remove_single_spot_plates`
1.22 				:meth:`setlyze.analysis.attraction_intra.Start.calculate_distances_intra`
1.23 				:meth:`setlyze.analysis.attraction_intra.Start.calculate_distances_intra_expected`
1.24 				:meth:`setlyze.analysis.attraction_intra.Start.calculate_significance`
1.27 				:meth:`setlyze.analysis.attraction_inter.Start.calculate_distances_inter`
1.28 				:class:`setlyze.database.AccessLocalDB`
1.29 				:class:`setlyze.database.AccessRemoteDB`
1.30 				:class:`setlyze.std.ReportGenerator`
1.31 				:meth:`setlyze.database.MakeLocalDB.run`
1.32 				:meth:`setlyze.database.MakeLocalDB.insert_from_csv`
1.33 				:meth:`setlyze.database.MakeLocalDB.insert_from_db`
1.34 				:meth:`setlyze.database.MakeLocalDB.insert_localities_from_csv`
1.35 				:meth:`setlyze.database.MakeLocalDB.insert_species_from_csv`
1.36 				:meth:`setlyze.database.MakeLocalDB.insert_plates_from_csv`
1.37 				:meth:`setlyze.database.MakeLocalDB.insert_records_from_csv`
1.38 				:meth:`setlyze.database.MakeLocalDB.create_new_db`
1.39 				:meth:`setlyze.gui.SelectionWindow.update_tree`
1.41.1 				:meth:`setlyze.database.AccessLocalDB.get_record_ids`
1.41.2 				:meth:`setlyze.database.AccessRemoteDB.get_record_ids`
1.42 				:meth:`setlyze.gui.SelectLocations.create_model`
1.43 				:meth:`setlyze.gui.SelectSpecies.create_model`
1.44 				:meth:`setlyze.gui.SelectionWindow.on_continue`
1.45 				:meth:`setlyze.gui.SelectLocations.on_back`
1.46 				:meth:`setlyze.gui.SelectSpecies.on_back`
1.47 				:meth:`setlyze.database.MakeLocalDB.fill_distance_table`
1.48 				:class:`setlyze.std.ReportGenerator`
1.49 				:class:`setlyze.std.ReportReader`
1.50 				:meth:`setlyze.std.ReportGenerator.set_location_selections`
1.51 				:meth:`setlyze.std.ReportGenerator.set_specie_selections`
1.52 				:meth:`setlyze.std.ReportGenerator.set_spot_distances_observed`
1.53 				:meth:`setlyze.std.ReportGenerator.set_spot_distances_expected`
1.54 				:meth:`setlyze.std.ReportGenerator.set_plate_areas_definition`
1.55 				:meth:`setlyze.std.ReportGenerator.set_area_totals_observed`
1.56 				:meth:`setlyze.std.ReportGenerator.set_area_totals_expected`
1.57 				:class:`setlyze.config.ConfigManager`
1.58 				:meth:`setlyze.analysis.spot_preference.Start.run`
1.59 				:meth:`setlyze.analysis.attraction_intra.Start.run`
1.60 				:meth:`setlyze.analysis.attraction_inter.Start.run`
1.61 				:meth:`setlyze.analysis.relations.Start.run`
1.62 				:meth:`setlyze.analysis.spot_preference.Start.get_areas_totals_observed`
1.63 				:meth:`setlyze.analysis.spot_preference.Start.get_areas_totals_expected`
1.64 				:meth:`setlyze.analysis.spot_preference.Start.chi_square_tester`
1.66 				:meth:`setlyze.database.MakeLocalDB.insert_localities_from_db`
1.67 				:meth:`setlyze.database.MakeLocalDB.insert_species_from_db`
1.68.1 				:meth:`setlyze.analysis.spot_preference.Begin.on_display_report`
1.68.2 				:meth:`setlyze.analysis.attraction_intra.Begin.on_display_report`
1.68.3 				:meth:`setlyze.analysis.attraction_inter.Begin.on_display_report`
1.68.4 				:meth:`setlyze.analysis.relations.Begin.on_display_report`
1.69 				:meth:`setlyze.analysis.attraction_inter.Start.calculate_distances_inter_expected`
1.70 				:meth:`setlyze.std.ReportGenerator.set_statistics_normality`
1.71 				:meth:`setlyze.std.ReportGenerator.set_statistics_significance`
1.72 				:meth:`setlyze.std.ReportGenerator.set_analysis`
1.73 				:meth:`setlyze.database.AccessDBGeneric.fill_plate_spot_totals_table`
1.74 				:meth:`setlyze.analysis.attraction_inter.Start.calculate_significance`
1.75 				:meth:`setlyze.database.MakeLocalDB.create_table_info`
1.76 				:meth:`setlyze.database.MakeLocalDB.create_table_localities`
1.77 				:meth:`setlyze.database.MakeLocalDB.create_table_species`
1.78 				:meth:`setlyze.database.MakeLocalDB.create_table_plates`
1.79 				:meth:`setlyze.database.MakeLocalDB.create_table_records`
1.80 				:meth:`setlyze.database.MakeLocalDB.create_table_species_spots_1`
1.81 				:meth:`setlyze.database.MakeLocalDB.create_table_species_spots_2`
1.82 				:meth:`setlyze.database.MakeLocalDB.create_table_spot_distances`
1.83 				:meth:`setlyze.database.MakeLocalDB.create_table_spot_distances_observed`
1.84 				:meth:`setlyze.database.MakeLocalDB.create_table_spot_distances_expected`
1.85 				:meth:`setlyze.database.MakeLocalDB.create_table_plate_spot_totals`
1.86                :class:`setlyze.gui.SelectAnalysis`
1.87                :class:`setlyze.gui.SelectLocations`
1.88                :class:`setlyze.gui.SelectSpecies`
1.89                :class:`setlyze.gui.DisplayReport`
1.90                :class:`setlyze.gui.ChangeDataSource`
1.91                :class:`setlyze.gui.DefinePlateAreas`
1.92                :class:`setlyze.gui.ProgressDialog`
1.93 				:meth:`setlyze.database.get_database_accessor`
1.94                :class:`setlyze.std.Sender`
1.95                :meth:`setlyze.database.AccessDBGeneric.get_locations`
1.96                :meth:`setlyze.database.AccessLocalDB.get_species`
1.97                :meth:`setlyze.database.AccessRemoteDB.get_species`
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
3.0                 :ref:`Select Analysis <dialog-analysis-selection>`
3.1                 :ref:`Select Locations <dialog-loc-selection>`
3.2                 :ref:`Select Species <dialog-spe-selection>`
3.3                 :ref:`Analysis Report <dialog-analysis-report>`
3.4                 :ref:`Change Data Source <dialog-change-data-source>`
3.5                 :ref:`Define Plate Areas <dialog-define-plate-areas>`
3.6                 :ref:`Progress Dialog <dialog-progress-dialog>`
==================  =================================

4.x Documents
=============================

.. toctree::
   :maxdepth: 4

   design_parts_docs
