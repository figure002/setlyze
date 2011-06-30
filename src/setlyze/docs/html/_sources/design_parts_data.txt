========================================================================
Design Parts: Data
========================================================================

The design parts in this overview describes all technical design parts
representing data used in SETLyze. This includes database tables,
application variables, and data files.

2.x Data Storage Places
=======================

.. _design-part-data-2.0:

2.0
------------------------------------------------------------------------

Table ``setl_records`` in the SETL database. The SETL database can be
either the MS Access database or the PostgreSQL database. This table
contains the SETL records.

PostgreSQL query: ::

    CREATE TABLE setl_records
    (
        rec_id              SERIAL,
        rec_pla_id          INTEGER NOT NULL,
        rec_spe_id          INTEGER NOT NULL,
        rec_unknown         BOOLEAN,
        rec_o               BOOLEAN,
        rec_r               BOOLEAN,
        rec_c               BOOLEAN,
        rec_a               BOOLEAN,
        rec_e               BOOLEAN,
        rec_sur_unknown     BOOLEAN,
        rec_sur1            BOOLEAN,
        rec_sur2            BOOLEAN,
        rec_sur3            BOOLEAN,
        rec_sur4            BOOLEAN,
        rec_sur5            BOOLEAN,
        rec_sur6            BOOLEAN,
        rec_sur7            BOOLEAN,
        rec_sur8            BOOLEAN,
        rec_sur9            BOOLEAN,
        rec_sur10           BOOLEAN,
        rec_sur11           BOOLEAN,
        rec_sur12           BOOLEAN,
        rec_sur13           BOOLEAN,
        rec_sur14           BOOLEAN,
        rec_sur15           BOOLEAN,
        rec_sur16           BOOLEAN,
        rec_sur17           BOOLEAN,
        rec_sur18           BOOLEAN,
        rec_sur19           BOOLEAN,
        rec_sur20           BOOLEAN,
        rec_sur21           BOOLEAN,
        rec_sur22           BOOLEAN,
        rec_sur23           BOOLEAN,
        rec_sur24           BOOLEAN,
        rec_sur25           BOOLEAN,
        rec_1st             BOOLEAN,
        rec_2nd             BOOLEAN,
        rec_v               BOOLEAN,
        rec_photo_nrs       VARCHAR(100),
        rec_remarks         VARCHAR(100),

        CONSTRAINT rec_id_pk PRIMARY KEY (rec_id),
        CONSTRAINT rec_pla_id_fk FOREIGN KEY (rec_pla_id)
            REFERENCES setl_plates (pla_id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT rec_spe_id_fk FOREIGN KEY (rec_spe_id)
            REFERENCES setl_species (spe_id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

.. _design-part-data-2.1:

2.1
------------------------------------------------------------------------

Table ``setl_species`` in the SETL database. The SETL database can be
either the MS Access database or the PostgreSQL database. This table
contains the SETL species records.

PostgreSQL query: ::

    CREATE TABLE setl_species
    (
        spe_id                    SERIAL,
        spe_name_venacular        VARCHAR(100) UNIQUE,
        spe_name_latin            VARCHAR(100) NOT NULL UNIQUE,
        spe_invasive_in_nl        BOOLEAN,
        spe_description           VARCHAR(300),
        spe_remarks               VARCHAR(160),
        spe_picture               OID,

        CONSTRAINT spe_id_pk PRIMARY KEY (spe_id)
    );

.. _design-part-data-2.2:

2.2
------------------------------------------------------------------------

Table ``setl_localities`` in the SETL database. The SETL database can be
either the MS Access database or the PostgreSQL database. This table
contains the SETL locality records.

PostgreSQL query: ::

    CREATE TABLE setl_localities
    (
        loc_id              SERIAL,
        loc_name            VARCHAR(100) NOT NULL UNIQUE,
        loc_nr              INTEGER,
        loc_coordinates     VARCHAR(100),
        loc_description     VARCHAR(300),

        CONSTRAINT loc_id_pk PRIMARY KEY (loc_id)
    );

.. _design-part-data-2.3:

2.3
------------------------------------------------------------------------

Table ``species`` in the local SQLite database. This table is
automatically filled from :ref:`design-part-data-2.1` when the user
starts a SETLyze analysis.

.. _design-part-data-2.3.1:

2.3.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.3`, but filled from
:ref:`design-part-data-2.1`.

.. _design-part-data-2.3.2:

2.3.2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.3`, but filled from
:ref:`design-part-data-2.19`.

SQLite query: ::

    CREATE TABLE species
    (
        spe_id INTEGER PRIMARY KEY,
        spe_name_venacular VARCHAR,
        spe_name_latin VARCHAR,
        spe_invasive_in_nl INTEGER,
        spe_description VARCHAR,
        spe_remarks VARCHAR
    );

.. _design-part-data-2.4:

2.4
------------------------------------------------------------------------

Table ``localities`` in the local SQLite database. This table is
automatically filled from :ref:`design-part-data-2.2` when the user
starts a SETLyze analysis.

SQLite query: ::

    CREATE TABLE localities
    (
        loc_id INTEGER PRIMARY KEY,
        loc_name VARCHAR,
        loc_nr VARCHAR,
        loc_coordinates VARCHAR,
        loc_description VARCHAR
    );

.. _design-part-data-2.4.1:

2.4.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.4`, but filled from
:ref:`design-part-data-2.2`.

.. _design-part-data-2.4.2:

2.4.2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.4`, but filled from
:ref:`design-part-data-2.18`.

.. _design-part-data-2.5:

2.5
------------------------------------------------------------------------

Table ``records`` in the local SQLite database. This table is only filled
if the user selected CSV files to import SETL data from. By default
this table is empty, and the records data from :ref:`design-part-data-2.0`
is used.

SQLite query: ::

    CREATE TABLE records
    (
        rec_id INTEGER PRIMARY KEY,
        rec_pla_id INTEGER,
        rec_spe_id INTEGER,
        rec_unknown INTEGER,
        rec_o INTEGER,
        rec_r INTEGER,
        rec_c INTEGER,
        rec_a INTEGER,
        rec_e INTEGER,
        rec_sur_unknown INTEGER,
        rec_sur1 INTEGER,
        rec_sur2 INTEGER,
        rec_sur3 INTEGER,
        rec_sur4 INTEGER,
        rec_sur5 INTEGER,
        rec_sur6 INTEGER,
        rec_sur7 INTEGER,
        rec_sur8 INTEGER,
        rec_sur9 INTEGER,
        rec_sur10 INTEGER,
        rec_sur11 INTEGER,
        rec_sur12 INTEGER,
        rec_sur13 INTEGER,
        rec_sur14 INTEGER,
        rec_sur15 INTEGER,
        rec_sur16 INTEGER,
        rec_sur17 INTEGER,
        rec_sur18 INTEGER,
        rec_sur19 INTEGER,
        rec_sur20 INTEGER,
        rec_sur21 INTEGER,
        rec_sur22 INTEGER,
        rec_sur23 INTEGER,
        rec_sur24 INTEGER,
        rec_sur25 INTEGER,
        rec_1st INTEGER,
        rec_2nd INTEGER,
        rec_v INTEGER
    );

.. _design-part-data-2.6:

2.6
------------------------------------------------------------------------

A list ``[<selection-1>,<selection-2>]`` for storing a maximum of two
location selections. ``<selection-1>`` and ``<selection-2>`` are lists
of integers representing location IDs. These IDs are the same as the IDs
in column ``loc_id`` in :ref:`design-part-data-2.2` and
:ref:`design-part-data-2.4`.

If no location selections are made yet, this variable has the value
``[None,None]``.

Get the value with :meth:`setlyze.config.ConfigManager.get` ::

    setlyze.config.cfg.get('locations-selection', slot=int)

Set the value with :meth:`setlyze.config.ConfigManager.set` ::

    setlyze.config.cfg.set('locations-selection', list, slot=int)

.. _design-part-data-2.7:

2.7
------------------------------------------------------------------------

A list ``[<selection-1>,<selection-2>]`` for storing a maximum of two
species selections. ``<selection-1>`` and ``<selection-2>`` are lists
of integers representing species IDs. These IDs are the same as the IDs
in column ``spe_id`` in :ref:`design-part-data-2.1` and
:ref:`design-part-data-2.3`.

Get the value with :meth:`setlyze.config.ConfigManager.get` ::

    setlyze.config.cfg.get('species-selection', slot=int)

Set the value with :meth:`setlyze.config.ConfigManager.set` ::

    setlyze.config.cfg.set('species-selection', list, slot=int)

.. _design-part-data-2.9:

2.9
------------------------------------------------------------------------

Table ``species_spots_1`` in the local database containing the SETL
records for the *first* selection of species and locations.

This table does not contain the complete records, but just the plate ID
and the 25 record surfaces.

SQLite query: ::

    CREATE TABLE species_spots_1
    (
        id INTEGER PRIMARY KEY,
        rec_pla_id INTEGER,
        rec_sur1 INTEGER,
        rec_sur2 INTEGER,
        rec_sur3 INTEGER,
        rec_sur4 INTEGER,
        rec_sur5 INTEGER,
        rec_sur6 INTEGER,
        rec_sur7 INTEGER,
        rec_sur8 INTEGER,
        rec_sur9 INTEGER,
        rec_sur10 INTEGER,
        rec_sur11 INTEGER,
        rec_sur12 INTEGER,
        rec_sur13 INTEGER,
        rec_sur14 INTEGER,
        rec_sur15 INTEGER,
        rec_sur16 INTEGER,
        rec_sur17 INTEGER,
        rec_sur18 INTEGER,
        rec_sur19 INTEGER,
        rec_sur20 INTEGER,
        rec_sur21 INTEGER,
        rec_sur22 INTEGER,
        rec_sur23 INTEGER,
        rec_sur24 INTEGER,
        rec_sur25 INTEGER
    );

.. _design-part-data-2.9.1:

2.9.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.9`, but with unique plates.

.. _design-part-data-2.9.2:

2.9.2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.9`, but with plates with just one
spot removed.

.. _design-part-data-2.10:

2.10
------------------------------------------------------------------------

Table ``species_spots_2`` in the local database containing the SETL
records for the *second* selection of species and locations.

This table does not contain the complete records, but just the plate ID
and the 25 record surfaces.

SQLite query: ::

    CREATE TABLE species_spots_2
    (
        id INTEGER PRIMARY KEY,
        rec_pla_id INTEGER,
        rec_sur1 INTEGER,
        rec_sur2 INTEGER,
        rec_sur3 INTEGER,
        rec_sur4 INTEGER,
        rec_sur5 INTEGER,
        rec_sur6 INTEGER,
        rec_sur7 INTEGER,
        rec_sur8 INTEGER,
        rec_sur9 INTEGER,
        rec_sur10 INTEGER,
        rec_sur11 INTEGER,
        rec_sur12 INTEGER,
        rec_sur13 INTEGER,
        rec_sur14 INTEGER,
        rec_sur15 INTEGER,
        rec_sur16 INTEGER,
        rec_sur17 INTEGER,
        rec_sur18 INTEGER,
        rec_sur19 INTEGER,
        rec_sur20 INTEGER,
        rec_sur21 INTEGER,
        rec_sur22 INTEGER,
        rec_sur23 INTEGER,
        rec_sur24 INTEGER,
        rec_sur25 INTEGER
    );

.. _design-part-data-2.10.1:

2.10.1
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.10`, but with unique plates.

.. _design-part-data-2.10.2:

2.10.2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Same as :ref:`design-part-data-2.10`, but with plates with just one
spot removed.

.. _design-part-data-2.12:

2.12
------------------------------------------------------------------------

Table ``spot_distances_observed`` in the local database containing the
observed spot distances.

Contains the spot distances for the records in :ref:`design-part-data-2.9`
if created by :meth:`~setlyze.analysis.attraction_intra.Start.calculate_distances_intra`.

If the table is created by :meth:`~setlyze.analysis.attraction_inter.Start.calculate_distances_inter`,
the table contains the distances between spots in :ref:`design-part-data-2.9`
and :ref:`design-part-data-2.10`.

SQLite query: ::

    CREATE TABLE spot_distances_observed
    (
        id INTEGER PRIMARY KEY,
        rec_pla_id INTEGER,
        distance REAL
    );

.. _design-part-data-2.13:

2.13
------------------------------------------------------------------------

Table ``spot_distances_expected`` in the local database. Has the same
design as :ref:`design-part-data-2.12`, but contains random generated
spot distances instead. These random generated spot distances will serve
as the expected spot distances.

SQLite query: ::

    CREATE TABLE spot_distances_expected
    (
        id INTEGER PRIMARY KEY,
        rec_pla_id INTEGER,
        distance REAL
    );

.. _design-part-data-2.14:

2.14
------------------------------------------------------------------------

Table ``info`` in the local SQLite database for storing basic
information about the local database.

SQLite query: ::

    CREATE TABLE info
    (
        id INTEGER PRIMARY KEY,
        name VARCHAR,
        value VARCHAR
    );

This information includes its creation date, the data source, and a
version number. The data source is a string which has the same design as
:ref:`design-part-data-2.22`. You can insert the data source with the
following SQLite query ::

    cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)", [setlyze.config.cfg.get('data-source')] )

Giving a version number to the local database could be useful in the future.
We can then notify the user if the local database is too old,
followed by creating a new local database. This would only work if the
version for the database is incremented each time you change the design
of the local database. To do this, edit the version number in
:meth:`~setlyze.database.MakeLocalDB.create_table_info`. The version
number can be inserted with ::

    cursor.execute("INSERT INTO info VALUES (null, 'version', ?)", [db_version])

The creation date and data source is inserted by the methods
:meth:`~setlyze.database.MakeLocalDB.insert_from_csv` and
:meth:`~setlyze.database.MakeLocalDB.insert_from_db`. The date can be
inserted with ::

    cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

.. _design-part-data-2.15:

2.15
------------------------------------------------------------------------

Table ``setl_plates`` in the SETL database. The SETL database can be
either the MS Access database or the PostgreSQL database. This table
contains the SETL plate records.

PostgreSQL query: ::

    CREATE TABLE setl_plates
    (
        pla_id                 	SERIAL,
        pla_loc_id              INTEGER NOT NULL,
        pla_setl_coordinator    VARCHAR(100),
        pla_nr                  VARCHAR(100),
        pla_deployment_date     TIMESTAMP,
        pla_retrieval_date      TIMESTAMP,
        pla_water_temperature   VARCHAR(100),
        pla_salinity            VARCHAR(100),
        pla_visibility          VARCHAR(100),
        pla_remarks             VARCHAR(300),

        CONSTRAINT pla_id_pk PRIMARY KEY (pla_id),
        CONSTRAINT pla_loc_id_fk FOREIGN KEY (pla_loc_id)
            REFERENCES setl_localities (loc_id)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

.. _design-part-data-2.16:

2.16
------------------------------------------------------------------------

Table ``plates`` in the local SQLite database. This table is only filled
if the user selected CSV files to import SETL data from. By default
this table is empty, and the plates data from :ref:`design-part-data-2.15`
is used.

SQLite query: ::

    CREATE TABLE plates
    (
        pla_id INTEGER PRIMARY KEY,
        pla_loc_id INTEGER,
        pla_setl_coordinator VARCHAR,
        pla_nr VARCHAR,
        pla_deployment_date TEXT,
        pla_retrieval_date TEXT,
        pla_water_temperature VARCHAR,
        pla_salinity VARCHAR,
        pla_visibility VARCHAR,
        pla_remarks VARCHAR
    );

.. _design-part-data-2.17:

2.17
------------------------------------------------------------------------

Links to an instance of ``xml.dom.minidom.Document``. It's a XML DOM
(Document Object Model) object containing the analysis settings and results.
This XML DOM object is generated by :class:`setlyze.std.ReportGenerator`.

Get the value with :meth:`setlyze.config.ConfigManager.get` ::

    setlyze.config.cfg.get('analysis-report')

Set the value with :meth:`setlyze.config.ConfigManager.set` ::

    setlyze.config.cfg.set('analysis-report', value)

.. _design-part-data-2.18:

2.18
------------------------------------------------------------------------

CSV file containing the locality records exported from the MS Access
SETL database.

If exported from the MS Access SETL database, the CSV file must have
the format ::

    LOC_id;LOC_name;LOC_nr;LOC_coordinates;LOC_description

.. _design-part-data-2.19:

2.19
------------------------------------------------------------------------

CSV file containing the species records exported from the MS Access
SETL database.

If exported from the MS Access SETL database, the CSV file must have
the format ::

    SPE_id;SPE_name_venacular;SPE_name_latin;SPE_invasive_in_NL;SPE_description;SPE_remarks;SPE_picture

.. _design-part-data-2.20:

2.20
------------------------------------------------------------------------

CSV file containing the plate records exported from the MS Access
SETL database.

If exported from the MS Access SETL database, the CSV file must have
the format ::

    PLA_id;PLA_LOC_id;PLA_SETL_coordinator;PLA_nr;PLA_deployment_date;PLA_retrieval_date;PLA_water_temperature;PLA_salinity;PLA_visibility;PLA_remarks

.. _design-part-data-2.21:

2.21
------------------------------------------------------------------------

CSV file containing the SETL records exported from the MS Access
SETL database.

If exported from the MS Access SETL database, the CSV file must have
the format ::

    REC_id;REC_PLA_id;REC_SPE_id;REC_?;REC_O;REC_R;REC_C;REC_A;REC_E;REC_sur?;REC_sur1;REC_sur2;REC_sur3;REC_sur4;REC_sur5;REC_sur6;REC_sur7;REC_sur8;REC_sur9;REC_sur10;REC_sur11;REC_sur12;REC_sur13;REC_sur14;REC_sur15;REC_sur16;REC_sur17;REC_sur18;REC_sur19;REC_sur20;REC_sur21;REC_sur22;REC_sur23;REC_sur24;REC_sur25;REC_1st;REC_2nd;REC_V;REC_photo_nrs;REC_remarks

.. _design-part-data-2.22:

2.22
------------------------------------------------------------------------

A string variable representing the current data source.

Can be either ``setl-database`` or ``csv-msaccess``. Several application
functions check this variable to figure out where to obtain data from.
The first means the PostgreSQL SETL database, and the second from user
selected CSV files exported from the MS Access SETL database.

This variable should be set whenever the data source has changed.

Get the value with :meth:`setlyze.config.ConfigManager.get` ::

    setlyze.config.cfg.get('data-source')

Set the value with :meth:`setlyze.config.ConfigManager.set` ::

    setlyze.config.cfg.set('data-source', value)

.. _design-part-data-2.23:

2.23
------------------------------------------------------------------------

Table ``spot_distances`` in the local database containing all possible
pre-calculated spot distances.

SQLite query: ::

    CREATE TABLE spot_distances
    (
        id INTEGER PRIMARY KEY,
        delta_x INTEGER,
        delta_y INTEGER,
        distance REAL
    );

Each distance in this table is coupled to a horizontal and a vertical
spot difference. The distances are pre-calculated by
:meth:`setlyze.std.distance`. In other words, if we have two spots,
and we know the horizontal difference (Δx) and the vertical
difference (Δy), we can look up the corresponding distance in the
``spot_distances`` table.

.. deprecated:: 0.1
   A :ref:`performance test <optimization_spot_dist_calc>` showed that retrieving
   pre-calculated spot distances from the database is much slower than
   calculating them on run time.


.. _design-part-data-2.24:

2.24
------------------------------------------------------------------------

Variable of type ``dict`` containing the plate areas definition for
:class:`analysis 1 <setlyze.analysis.spot_preference>`.

The dictionary has the format ::

    {
    'area1': list,
    'area2': list,
    'area3': list,
    'area4': list
    }

Where ``list`` is a list of strings. The possible
strings are ``A``, ``B``, ``C`` and ``D``. Each letter represents a
surface on a SETL plate. For a clearer picture, refer to
:ref:`fig_plate_areas_default`.

The default value for the plate areas definition is ::

    {
    'area1': ['A'],
    'area2': ['B'],
    'area3': ['C'],
    'area4': ['D']
    }

Using :class:`setlyze.gui.DefinePlateAreas`, the user can change this
definition. The user could for example combine the surfaces ``A`` and
``B``, meaning the value for this variable becomes ::

    {
    'area1': ['A', 'B'],
    'area3': ['C'],
    'area4': ['D']
    }

Keep in mind that the dictionary keys (area1, area2, ..) don't have any
meaning. They just make it possible to destinct between the plate areas.

Get the value with :meth:`setlyze.config.ConfigManager.get` ::

    setlyze.config.cfg.get('plate-areas-definition')

Set the value with :meth:`setlyze.config.ConfigManager.set` ::

    setlyze.config.cfg.set('plate-areas-definition', value)

.. _design-part-data-2.25:

2.25
------------------------------------------------------------------------

An application variable that contains the observed species totals for each
user defined plate area. Keep in mind that this is not the number of individual
organisms found on the plate areas, as the records just tell the presence
of a species. So it tells how many times the presence of a species was
found on each user defined plate area.

This is what the value can look like ::

    {
    'area4': 52,
    'area1': 276,
    'area2': 751,
    'area3': 457
    }

Namespace:
    ``setlyze.analysis.spot_preference.Start.areas_totals_observed``

.. _design-part-data-2.26:

2.26
------------------------------------------------------------------------

An application variable that contains the expected species totals for
each plate area. Keep in mind that this not the number of individuals
found on the plate area, as the records just tell the presence of a
species.

This is what the value can look like ::

    {
    'area4': 61.439999999999998,
    'area1': 245.75999999999999,
    'area2': 737.27999999999997,
    'area3': 491.51999999999998
    }

Namespace:
    ``setlyze.analysis.spot_preference.areas_totals_expected``

.. _design-part-data-2.27:

2.27
------------------------------------------------------------------------

The element ``location_selections`` in the XML DOM report that contains
the user selected locations.

.. _design-part-data-2.28:

2.28
------------------------------------------------------------------------

The element ``species_selections`` in the XML DOM report that contains the
user selected species.

.. _design-part-data-2.29:

2.29
------------------------------------------------------------------------

The element ``spot_distances_observed`` in the XML DOM report that contains
the actual spot distances.

.. _design-part-data-2.30:

2.30
------------------------------------------------------------------------

The element ``spot_distances_expected`` in the XML DOM report that
contains the expected spot distances.

.. _design-part-data-2.31:

2.31
------------------------------------------------------------------------

The element ``plate_areas_definition`` in the XML DOM report that contains
the user defined plate areas definition.

.. _design-part-data-2.32:

2.32
------------------------------------------------------------------------

The element ``area_totals_observed`` in the XML DOM report that contains the
actual species totals per plate area.

.. _design-part-data-2.33:

2.33
------------------------------------------------------------------------

The element ``area_totals_expected`` in the XML DOM report that contains
the expected species totals per plate area.

.. _design-part-data-2.34:

2.34
------------------------------------------------------------------------

The element ``statistics_normality`` in the XML DOM report that contains
the statistic results for the normality tests.

.. _design-part-data-2.35:

2.35
------------------------------------------------------------------------

The element ``statistics_significance`` in the XML DOM report that
contains the statistic results for the significance tests.

.. _design-part-data-2.36:

2.36
------------------------------------------------------------------------

Analysis variable that contains the statistic results for the normality
tests.

Namespace:
    ``setlyze.analysis.attraction_intra.Begin.statistics['normality']``

.. _design-part-data-2.37:

2.37
------------------------------------------------------------------------

Analysis variable that contains the statistic results for the
significance tests.

Namespace:
    ``setlyze.analysis.attraction_intra.Begin.statistics['significance']``

.. _design-part-data-2.38:

2.38
------------------------------------------------------------------------

The element ``analysis`` in the XML DOM report that contains the name of
the analysis.

.. _design-part-data-2.39:

2.39
------------------------------------------------------------------------

Table ``plate_spot_totals`` in the local database for the number of
positive spots for each plate ID in the tables :ref:`design-part-data-2.9`
and/or :ref:`design-part-data-2.10`.

Column ``n_spots_a`` is for the spots in :ref:`design-part-data-2.9`, and
column ``n_spots_b`` for the spots in :ref:`design-part-data-2.10`.

SQLite query: ::

    CREATE TABLE plate_spot_totals
    (
        pla_id INTEGER PRIMARY KEY,
        n_spots_a INTEGER,
        n_spots_b INTEGER
    );

.. _design-part-data-2.40:

2.40
------------------------------------------------------------------------

A XML file containing all data elements from :ref:`design-part-data-2.17`.

.. _design-part-data-2.41:

2.41
------------------------------------------------------------------------

Table ``plate_area_totals_observed`` in the local SQLite database. This table
contains the number of positive spots for each default plate area (A, B, C,
and D) for each plate that matches the species selection.

This table is filled by :meth:`~setlyze.analysis.spot_preference.Start.set_plate_area_totals_observed`.

SQLite query: ::

    CREATE TABLE plate_area_totals_observed (
	pla_id INTEGER PRIMARY KEY,
	area_a INTEGER,
	area_b INTEGER,
	area_c INTEGER,
	area_d INTEGER
    );

.. _design-part-data-2.42:

2.42
------------------------------------------------------------------------

Table ``plate_area_totals_expected`` in the local SQLite database.

This table contains the number of expected positive spots for each default
plate area (A, B, C, and D) per plate that matches the species selection. The
expected spots are calculated with a random generator. The random generator
randomly puts an equal number of positive spots on a virtual plate, then
calcualtes the number of positive spots for each plate area. This is done for
all plates mathching a species selection.

This table is filled by :meth:`~setlyze.analysis.spot_preference.Start.set_plate_area_totals_expected`.

SQLite query: ::

    CREATE TABLE plate_area_totals_expected (
	pla_id INTEGER PRIMARY KEY,
	area_a INTEGER,
	area_b INTEGER,
	area_c INTEGER,
	area_d INTEGER
    );
