#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
#
#  This file is part of SETLyze - A tool for analyzing SETL data.
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
import os
import csv
import logging
import threading
import itertools
from sqlite3 import dbapi2 as sqlite

import setlyze.config
import setlyze.std

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

class MakeLocalDB(threading.Thread):
    """Create a local SQLite database with default tables, and fill some
    tables based on the called function.

    Design Part: 1.2
    """

    def __init__(self):
        super(MakeLocalDB, self).__init__()

        self.cursor = None
        self.connection = None
        self.dbfile = setlyze.config.cfg.get('db-file')

    def run(self):
        """Decide which functions should be called.

        Design Part: 1.31
        """

        # Check if we need to make a new database file.
        if setlyze.config.cfg.get('make-new-db'):
            # Create new database with data.
            if setlyze.config.cfg.get('data-source') == "setl-database":
                self.insert_from_db()
            elif setlyze.config.cfg.get('data-source') == "csv-msaccess":
                self.insert_from_csv()

            # Emit the signal that the local database has been created.
            setlyze.std.sender.emit("local-db-created")

    def insert_from_csv(self):
        """Create a local SQLite database by loading data from the user
        selected CSV files.

        This method requires 4 CSV files:
            * localities_file, containing the SETL locations.
            * species_file, containing the SETL species.
            * records_file, containing the SETL records.
            * plates_file, containing the SETL plates.

        These files must be exported from the MS Access SETL database.

        Design Part: 1.32
        """
        logging.info("Creating local database from CSV files...")

        # If data_source is not set to "csv-msaccess", the required data
        # files are probably not set by the user yet. ChangeDataSource
        # must be called first.
        if setlyze.config.cfg.get('data-source') != "csv-msaccess":
            logging.error("Cannot run database.MakeLocalDB.insert_from_csv() while 'data-source' is set to '%s'" % setlyze.config.cfg.get('data-source'))
            sys.exit(1)

        # First, create a new database file.
        self.create_new_db()

        # Create a connection with the local database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Add some meta-data to a separate table in the local database.
        # Add the data source we can figure out what kind of data is
        # present.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)", ( setlyze.config.cfg.get('data-source'), ) )
        # Also insert the data of creation, so we can give the user an
        # indication when this database was created.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # Insert the data from the CSV files into the local database.
        setlyze.std.update_progress_dialog(0.0,
            "Importing %s" % os.path.split(setlyze.config.cfg.get('localities-file'))[1]
            )

        self.insert_localities_from_csv()

        setlyze.std.update_progress_dialog(0.25,
            "Importing %s" % os.path.split(setlyze.config.cfg.get('plates-file'))[1]
            )

        self.insert_plates_from_csv()

        setlyze.std.update_progress_dialog(0.50,
            "Importing %s" % os.path.split(setlyze.config.cfg.get('records-file'))[1]
            )

        self.insert_records_from_csv()

        setlyze.std.update_progress_dialog(0.75,
            "Importing %s" % os.path.split(setlyze.config.cfg.get('species-file'))[1]
            )

        self.insert_species_from_csv()

        setlyze.std.update_progress_dialog(1.0)

        # Close the connection with the database.
        self.cursor.close()
        self.connection.close()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

    def insert_localities_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the locations from a CSV file into the local database.

        Keyword arguments:
            delimiter
                A one-character string used to separate fields in the
                CSV file.
            quotechar
                A one-character string used to quote fields containing
                special characters in the CSV file.

        Design Part: 1.34
        """
        logging.info("Importing data from %s" % setlyze.config.cfg.get('localities-file'))

        # Try to open the CSV file.
        try:
            f = open(setlyze.config.cfg.get('localities-file'), 'r')
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for row in setl_reader:
            self.cursor.execute("INSERT INTO localities VALUES (?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_species_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the species from a CSV file into the local database.

        Keyword arguments:
            delimiter
                A one-character string used to separate fields in the CSV
                file.
            quotechar
                A one-character string used to quote fields containing
                special characters in the CSV file.

        Design Part: 1.35
        """
        logging.info("Importing data from %s" % setlyze.config.cfg.get('species-file'))

        # Try to open the CSV file.
        try:
            f = open(setlyze.config.cfg.get('species-file'), 'r')
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for row in setl_reader:
            self.cursor.execute("INSERT INTO species VALUES (?,?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4],row[5])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_plates_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the plates from a CSV file into the local database.

        Keyword arguments:
            delimiter
                A one-character string used to separate fields in the CSV
                file.
            quotechar
                A one-character string used to quote fields containing
                special characters in the CSV file.

        Design Part: 1.36
        """
        logging.info("Importing data from %s" % setlyze.config.cfg.get('plates-file'))

        # Try to open the CSV file.
        try:
            f = open(setlyze.config.cfg.get('plates-file'), 'r')
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for row in setl_reader:
            self.cursor.execute("INSERT INTO plates VALUES (?,?,?,?,?,?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_records_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the records from a CSV file into the local database.

        Keyword arguments:
            delimiter
                A one-character string used to separate fields in the CSV
                file.
            quotechar
                A one-character string used to quote fields containing
                special characters in the CSV file.

        Design Part: 1.37
        """
        logging.info("Importing data from %s" % setlyze.config.cfg.get('records-file'))

        # Try to open the CSV file.
        try:
            f = open(setlyze.config.cfg.get('records-file'), 'r')
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        placeholders = ','.join('?' * 38)
        for row in setl_reader:
            self.cursor.execute("INSERT INTO records VALUES (%s)" % placeholders,
                (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],
                row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17],row[18],row[19],
                row[20],row[21],row[22],row[23],row[24],row[25],row[26],row[27],row[28],row[29],
                row[30],row[31],row[32],row[33],row[34],row[35],row[36],row[37])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_from_db(self):
        """Create a local SQLite database by loading data from the
        SETL PostgreSQL database. This method just loads the localities
        and the species into the local database.

        Design Part: 1.33
        """
        logging.info("Creating local database from SETL database...")

        # First, create a new database file.
        self.create_new_db()

        # Create a connection with the local database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Next time we run the tool, we'll know what data is in the
        # database.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)", (setlyze.config.cfg.get('data-source'),) )
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # TODO: Insert data from SETL database.
        logging.info("Inserting data from the SETL database into local database...")

        setlyze.std.update_progress_dialog(1.0)

        # Close the connection with the database.
        self.cursor.close()
        self.connection.close()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

    def create_new_db(self):
        """Create an empty database with the necessary tables.

        Design Part: 1.38
        """
        logging.info("Creating new local database file...")

        # Check if the data folder exists. If not, create it.
        data_path = setlyze.config.cfg.get('data-path')
        if not os.path.exists(data_path):
            logging.info("Creating data folder %s" % (data_path))
            os.makedirs(data_path)

        # Delete the current database file.
        if os.path.isfile(self.dbfile):
            os.remove(self.dbfile)

        # This will automatically create a new database file.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Create the tables.

        # This info table contains basic information about the
        # local database. A version number could be handy in the future,
        # for example we can notify the user if the local database is
        # too old.
        cursor.execute("CREATE TABLE info (\
                        id INTEGER PRIMARY KEY, \
                        name VARCHAR, \
                        value VARCHAR)")
        cursor.execute("INSERT INTO info VALUES (null, 'version', ?)", ["0.1"])

        # Design Part: 2.4
        cursor.execute("CREATE TABLE localities (\
                        loc_id INTEGER PRIMARY KEY, \
                        loc_name VARCHAR, \
                        loc_nr VARCHAR, \
                        loc_coordinates VARCHAR, \
                        loc_description VARCHAR \
                        )")

        # Design Part: 2.3
        cursor.execute("CREATE TABLE species (\
                        spe_id INTEGER PRIMARY KEY, \
                        spe_name_venacular VARCHAR, \
                        spe_name_latin VARCHAR, \
                        spe_invasive_in_nl INTEGER, \
                        spe_description VARCHAR, \
                        spe_remarks VARCHAR \
                        )")

        # Design Part: 2.16
        cursor.execute("CREATE TABLE plates (\
                        pla_id INTEGER PRIMARY KEY, \
                        pla_loc_id INTEGER, \
                        pla_setl_coordinator VARCHAR, \
                        pla_nr VARCHAR, \
                        pla_deployment_date TEXT, \
                        pla_retrieval_date TEXT, \
                        pla_water_temperature VARCHAR, \
                        pla_salinity VARCHAR, \
                        pla_visibility VARCHAR, \
                        pla_remarks VARCHAR \
                        )")

        # Design Part: 2.5
        cursor.execute("CREATE TABLE records (\
                        rec_id INTEGER PRIMARY KEY, \
                        rec_pla_id INTEGER, \
                        rec_spe_id INTEGER, \
                        rec_unknown INTEGER, \
                        rec_o INTEGER, \
                        rec_r INTEGER, \
                        rec_c INTEGER, \
                        rec_a INTEGER, \
                        rec_e INTEGER, \
                        rec_sur_unknown INTEGER, \
                        rec_sur1 INTEGER, \
                        rec_sur2 INTEGER, \
                        rec_sur3 INTEGER, \
                        rec_sur4 INTEGER, \
                        rec_sur5 INTEGER, \
                        rec_sur6 INTEGER, \
                        rec_sur7 INTEGER, \
                        rec_sur8 INTEGER, \
                        rec_sur9 INTEGER, \
                        rec_sur10 INTEGER, \
                        rec_sur11 INTEGER, \
                        rec_sur12 INTEGER, \
                        rec_sur13 INTEGER, \
                        rec_sur14 INTEGER, \
                        rec_sur15 INTEGER, \
                        rec_sur16 INTEGER, \
                        rec_sur17 INTEGER, \
                        rec_sur18 INTEGER, \
                        rec_sur19 INTEGER, \
                        rec_sur20 INTEGER, \
                        rec_sur21 INTEGER, \
                        rec_sur22 INTEGER, \
                        rec_sur23 INTEGER, \
                        rec_sur24 INTEGER, \
                        rec_sur25 INTEGER, \
                        rec_1st INTEGER, \
                        rec_2nd INTEGER, \
                        rec_v INTEGER \
                        )")

        # Note that rec_pla_id doesn't have to be unique, so we're
        # creating a separate primary key "id".
        # Design Part: 2.9.1
        # Design Part: 2.10.1
        # Design Part: 2.11.1
        cursor.execute("CREATE TABLE species_spots_1 (\
                            id INTEGER PRIMARY KEY, \
                            rec_pla_id INTEGER, \
                            rec_sur1 INTEGER, \
                            rec_sur2 INTEGER, \
                            rec_sur3 INTEGER, \
                            rec_sur4 INTEGER, \
                            rec_sur5 INTEGER, \
                            rec_sur6 INTEGER, \
                            rec_sur7 INTEGER, \
                            rec_sur8 INTEGER, \
                            rec_sur9 INTEGER, \
                            rec_sur10 INTEGER, \
                            rec_sur11 INTEGER, \
                            rec_sur12 INTEGER, \
                            rec_sur13 INTEGER, \
                            rec_sur14 INTEGER, \
                            rec_sur15 INTEGER, \
                            rec_sur16 INTEGER, \
                            rec_sur17 INTEGER, \
                            rec_sur18 INTEGER, \
                            rec_sur19 INTEGER, \
                            rec_sur20 INTEGER, \
                            rec_sur21 INTEGER, \
                            rec_sur22 INTEGER, \
                            rec_sur23 INTEGER, \
                            rec_sur24 INTEGER, \
                            rec_sur25 INTEGER \
                        )")

        # Note that rec_pla_id doesn't have to be unique, so we're
        # creating a separate unique key "id".
        # Design Part: 2.9.2
        # Design Part: 2.10.2
        # Design Part: 2.11.2
        cursor.execute("CREATE TABLE species_spots_2 (\
                            id INTEGER PRIMARY KEY, \
                            rec_pla_id INTEGER, \
                            rec_sur1 INTEGER, \
                            rec_sur2 INTEGER, \
                            rec_sur3 INTEGER, \
                            rec_sur4 INTEGER, \
                            rec_sur5 INTEGER, \
                            rec_sur6 INTEGER, \
                            rec_sur7 INTEGER, \
                            rec_sur8 INTEGER, \
                            rec_sur9 INTEGER, \
                            rec_sur10 INTEGER, \
                            rec_sur11 INTEGER, \
                            rec_sur12 INTEGER, \
                            rec_sur13 INTEGER, \
                            rec_sur14 INTEGER, \
                            rec_sur15 INTEGER, \
                            rec_sur16 INTEGER, \
                            rec_sur17 INTEGER, \
                            rec_sur18 INTEGER, \
                            rec_sur19 INTEGER, \
                            rec_sur20 INTEGER, \
                            rec_sur21 INTEGER, \
                            rec_sur22 INTEGER, \
                            rec_sur23 INTEGER, \
                            rec_sur24 INTEGER, \
                            rec_sur25 INTEGER \
                        )")

        # Create the table that will contain all the pre-calculated
        # spot distances.
        # Design Part: 2.23
        cursor.execute("CREATE TABLE spot_distances (\
                        id INTEGER PRIMARY KEY, \
                        delta_x INTEGER, \
                        delta_y INTEGER, \
                        distance REAL \
                        )")

        # The table for the found spot distances.
        # Design Part: 2.12
        cursor.execute("CREATE TABLE spot_distances_observed (\
                        id INTEGER PRIMARY KEY, \
                        rec_pla_id INTEGER, \
                        distance REAL \
                        )")

        # The table for the expected spot distances.
        # Design Part: 2.13
        cursor.execute("CREATE TABLE spot_distances_expected (\
                        id INTEGER PRIMARY KEY, \
                        rec_pla_id INTEGER, \
                        distance REAL \
                        )")

        # The table for the total of spots per plate in the distance
        # tables.
        # Design Part: 2.39
        cursor.execute("CREATE TABLE plate_spot_totals (\
                        pla_id INTEGER PRIMARY KEY, \
                        n_spots_a INTEGER, \
                        n_spots_b INTEGER \
                        )")

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        # Fill the spot_distances table.
        self.fill_distance_table()

        # No need to make a new database, as we just created one.
        setlyze.config.cfg.set('make-new-db', False)

    def fill_distance_table(self):
        """Calculate all possible spot distances for a SETL plate and put
        them in a table in the local database.

        Design Part: 1.47
        """

        # Make log message.
        logging.info("Populating distances table...")

        # Possible spot distances for a SETL plate. Moving horizontally
        # or vertically from one spot to the next is defined as
        # distance=1. Not moving means distance 0.
        distances = (0,1,2,3,4)

        # Create a Cartesian product for the possible distances.
        products = itertools.product(distances, distances)

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Now calculate the distance for each Cartesian product and put
        # each distance in the table.
        for p1,p2 in products:
            cursor.execute( "INSERT INTO spot_distances "
                            "VALUES (null,?,?,?)",
                            (p1, p2, setlyze.std.distance(p1,p2))
                            )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()


class AccessDB(object):
    """Class for accessing the database. Based on the setting of
    ``setlyze.config.cfg.get('data-source')``, this class wil either use the
    AccessLocalDB or AccessRemoteDB class to access the database.

    Design Part:
    """

    def __init__(self):
        data_source = setlyze.config.cfg.get('data-source')
        if data_source == "csv-msaccess":
            self.db = AccessLocalDB()
        elif data_source == "setl-database":
            self.db = AccessRemoteDB()
        else:
            logging.error("AccessDB: '%s' is not a valid data source." % data_source)
            sys.exit(1)

class AccessDBGeneric(object):
    """Super class for AccessLocalDB and AccessRemoteDB.

    This class contains methods that are generic for both sub-classes.
    """

    def __init__(self):
        self.progress_dialog = None
        self.dbfile = setlyze.config.cfg.get('db-file')

    def get_locations(self):
        """Return a list of all locations from the local database.

        Returns:
            A list with tuples. Each tuple has the format
            ``(loc_id, "loc_name")``
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor.execute("SELECT loc_id, loc_name FROM localities")
        locations = cursor.fetchall()
        cursor.close()
        connection.close()

        return locations

    def make_plates_unique(self, slot):
        """Join the records in local database table 'species_spots' that
        have the same plate ID. If one spot in a column contains 1, the
        resulting spot becomes 1. If all spots from a column are 0, the
        resulting spot becomes 0.

        The reason we're doing this, is because the user can select
        multiple species. The analysis should threat them as one specie.

        Design Part: 1.20
        """

        # The available tables to save the spots to.
        tables = ('species_spots_1','species_spots_2')

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Get all plate IDs.
        cursor.execute( "SELECT rec_pla_id FROM %s" % (tables[slot]) )
        pla_ids = cursor.fetchall()
        # Remove duplicate plate IDs.
        pla_ids = setlyze.std.uniqify(pla_ids)

        n = 0
        for pla_id in pla_ids:
            # Get plate ID and all 25 spots for each plate ID.
            cursor.execute( "SELECT rec_pla_id,"
                            "rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                            "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                            "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                            "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                            "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                            "FROM %s "
                            "WHERE rec_pla_id = ?" %
                            (tables[slot]),
                            (pla_id[0],)
                            )

            # Create a combined record from all records with this
            # plate ID.
            rows = cursor.fetchall()
            combined = setlyze.std.combine_by_plate(rows)

            # Remove all records with that plate ID from the
            # species_spots table.
            cursor.execute( "DELETE FROM %s "
                            "WHERE rec_pla_id = ?" %
                            (tables[slot]),
                            (pla_id[0],)
                            )

            # Insert the combined record in the species_spots table. So
            # this single record replaces all other records with this
            # plate ID.
            placeholders = ','.join('?' * 26)
            cursor.execute("INSERT INTO %s VALUES (null,%s)" %
                            (tables[slot], placeholders),
                            combined
                            )

            # Keep track of the new records being added.
            n += 1

        # Commit the database transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        # Return the total numbers of unique plate records.
        return n

    def remove_single_spot_plates(self, table):
        """Remove records that have just one spot with True. Intra-specific
        distance can’t be calculated for those.

        .. note::
           Use of this function is discouraged. You can easily check for
           a minimum number of spots in your functions. Also the function
           :meth:`~setlyze.std.get_spot_combinations_from_record` will
           return an empty list if no combinations are possibe (e.g. the
           record contains less than 2 positive spots).

        Design Part: 1.21
        """

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Get all spots for each plate.
        cursor.execute( "SELECT rec_pla_id,"
                        "rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM %s" % (table)
                        )

        delete = []
        for record in cursor:
            # Count total True's (n) for each record.
            n = 0
            for spot in record[1:]:
                # Again, skip the first item, as it's the plate ID.
                # Count the number of True's.
                if spot:
                    n += 1

            # Total (n) must be at least 2; if not, add that plate ID
            # to the list of to be deleted plates/records.
            if n < 2:
                delete.append(record[0])

        # Create a string of the IDs.
        delete_str = ",".join([str(id) for id in delete])

        # Delete the records in the list of plate IDs.
        cursor.execute( "DELETE FROM %s "
                        "WHERE rec_pla_id IN (%s)" %
                        (table, delete_str)
                        )

        # Commit the database transaction.
        # Design Part: 2.10 -> 2.11
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        # Return the list of deleted plates.
        return delete

    def fill_plate_spot_totals_table(self, spots_table1, spots_table2=None):
        """Fill the 'plate_spot_totals' table with the unique plate IDs
        from the spots tables and the number of positive spots each
        plate contains.

        This table is used by several analysis functions:
            * Calculating the expected distances, where the spot numbers
              serve as a template for the random spots generator.

            * Significance calculators, where the tests are applied to
              plates with specific numbers of positive spots.

        Keyword arguments:
            spots_table1
                The name of a spots table.
            spots_table2
                The name of a second spots table (optional).

        If just one table is provided, only the column 'n_spots_a' is
        filled. If two spots tables are provided, 'n_spots_a' is filled
        from the first spots table, and 'n_spots_b' filled from the
        second spots table.

        Design Part: 1.73
        """

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the plate_spot_totals table before we use it again.
        cursor.execute("DELETE FROM plate_spot_totals")
        connection.commit()

        skipped = 0

        if spots_table2:
            # Two spots tables are provided.

            # Get all records from both spots tables where the plate IDs
            # match.
            # Each returned record has this format:
            # id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|
            # rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|
            # rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|
            # rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|
            # rec_sur24|rec_sur25|id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|
            # rec_sur4|rec_sur5|rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|
            # rec_sur11|rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|
            # rec_sur17|rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|
            # rec_sur23|rec_sur24|rec_sur25
            cursor.execute( "SELECT s1.*, s2.* FROM %s as s1 "
                            "INNER JOIN %s as s2 "
                            "ON s1.rec_pla_id=s2.rec_pla_id" %
                            (spots_table1, spots_table2)
                            )

            for record in cursor:
                record1 = record[2:27]
                record2 = record[29:54]

                # Get the positive spots for both records.
                spots1 = setlyze.std.get_spots_from_record(record1)
                spots2 = setlyze.std.get_spots_from_record(record2)

                # We're only interested in the number of spots.
                spots1 = len(spots1)
                spots2 = len(spots2)

                # Skip this plate if both records contain less than 1
                # positive spot.
                # We won't be able to calculate distances for such records
                # anyway.
                if spots1 < 1 and spots2 < 1:
                    skipped += 1
                    continue

                # Save the number of positive spots to the
                # plate_spot_totals table.
                cursor2.execute( "INSERT INTO plate_spot_totals "
                                 "VALUES (?,?,?)",
                                 (record[1], spots1, spots2)
                                )
        else:
            # One spots table is provided.

            # Get all spots for each plate.
            # Each returned record has this format:
            # id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|
            # rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|
            # rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|
            # rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|
            # rec_sur24|rec_sur25
            cursor.execute( "SELECT * FROM %s" % (spots_table1)
                            )

            for record in cursor:
                # Get the positive spots for this plate.
                spots = setlyze.std.get_spots_from_record(record[2:])

                # We're only interested in the number of spots.
                spots = len(spots)

                # Skip this record if it contains less than 2 positive spots.
                # We won't be able to calculate a distance for such records
                # anyway.
                if spots < 2:
                    skipped += 1
                    continue

                # Save the number of positive spots to the
                # plate_spot_totals table.
                cursor2.execute( "INSERT INTO plate_spot_totals "
                                 "VALUES (?,?,null)",
                                 (record[1], spots)
                                )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

        # Return the number of records that were skipped.
        return skipped

    def get_distances_matching_spots_total(self, cursor, distance_table, spots_n=-1):
        """Get the distances from a distance table that are from plates
        matching a specific number of spots on a plate.

        This function is specific to analysis 2.1.
        """
        if spots_n == -1:
            # If spots_n=-1, get all distances.
            cursor.execute("SELECT distance FROM %s" % distance_table)
        else:
            # Get the plate IDs that match the provided total spots number.
            cursor.execute( "SELECT pla_id "
                            "FROM plate_spot_totals "
                            "WHERE n_spots_a = %d" %
                            (spots_n)
                            )
            plate_ids = cursor.fetchall()
            plate_ids = ",".join([str(item[0]) for item in plate_ids])

            # Get the distances that match the plate IDs.
            cursor.execute( "SELECT distance "
                            "FROM %s "
                            "WHERE rec_pla_id IN (%s)" %
                            (distance_table, plate_ids)
                            )

class AccessLocalDB(AccessDBGeneric):
    """Retrieve data from the local SQLite database.

    Design Part: 1.28
    """

    def __init__(self):
        super(AccessLocalDB, self).__init__()
        self.cursor = None
        self.connection = None

    def get_species(self, loc_slot=0):
        """Return a list of species that match the selected locations from
        the local database.

        Keyword arguments:
            loc_slot
                An integer defining which location selection to use,
                as a selection variable contains on or more selection
                lists. Default the first selection list is returned
                (loc_slot=0).

        Returns:
            A list with tuples in the format ``(spe_id,
            "spe_name_venacular", "spe_name_latin")``
        """

        # Get one of the location selections.
        locations_selection = setlyze.config.cfg.get('locations-selection', slot=loc_slot)

        # Connect to the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Select all plate IDs from plates that are from the selected
        # locations.
        placeholders = ','.join('?' * len(locations_selection))
        cursor.execute("SELECT pla_id FROM plates WHERE pla_loc_id IN (%s)" %
            (placeholders), locations_selection)
        # Construct a list with the IDs
        pla_ids = [row[0] for row in cursor]
        # Remove duplicates.
        pla_ids = setlyze.std.uniqify(pla_ids)
        # Create a string of the IDs for the query.
        pla_ids_str = ",".join([str(id) for id in pla_ids])
        #print "pla_ids: ", pla_ids

        # Select all specie IDs from records with those plate IDs.
        cursor.execute("SELECT rec_spe_id FROM records WHERE rec_pla_id IN (%s) AND rec_spe_id != ''" % pla_ids_str)
        # Construct a list with the IDs
        spe_ids = [row[0] for row in cursor]
        # Remove duplicates.
        spe_ids = setlyze.std.uniqify(spe_ids)
        # Create a string of the IDs for the query.
        spe_ids_str = ",".join([str(id) for id in spe_ids]) # Turn the list into a string
        #print "spe_ids: ", spe_ids

        # Select information from species that match those species IDs.
        cursor.execute("SELECT spe_id, spe_name_venacular, spe_name_latin FROM species WHERE spe_id IN (%s)" % spe_ids_str)
        species = cursor.fetchall()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        return species

    def get_record_ids(self, loc_ids, spe_ids):
        """Return the record IDs that match both the provided locations and
        species IDs.

        Design Part: 1.41
        """

        # Create strings containing all the selected locations and
        # species IDs. These will be part of the queries below.
        loc_ids_str = ",".join([str(id) for id in loc_ids])
        spe_ids_str = ",".join([str(id) for id in spe_ids])

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Get the plate IDs that match the selected locations.
        cursor.execute("SELECT pla_id FROM plates WHERE pla_loc_id IN (%s)"
            % (loc_ids_str))

        # Construct a list with the plate IDs.
        pla_ids = [row[0] for row in cursor]
        pla_ids_str = ",".join([str(id) for id in pla_ids])

        # Select all record IDs that match the plate IDs and the
        # selected species.
        cursor.execute( "SELECT rec_id FROM records "
                        "WHERE rec_pla_id IN (%s) "
                        "AND rec_spe_id IN (%s)"
                        % (pla_ids_str, spe_ids_str)
                        )

        # Construct a list with the record IDs.
        rec_ids = [row[0] for row in cursor]

        # Close connection with the local database.
        cursor.close()
        connection.close()

        return rec_ids

    def get_spots(self, rec_ids):
        """Return all the spot booleans for the specified records."""

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        # Create a string of the IDs for the query.
        rec_ids_str = ",".join([str(id) for id in rec_ids])

        # Get all 25 spots from each record that matches the list of
        # record IDs.
        cursor.execute( "SELECT rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM records "
                        "WHERE rec_id IN (%s)" % (rec_ids_str)
                        )

        records = cursor.fetchall()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        return records

    def set_species_spots(self, rec_ids, slot):
        """Create a table in the local database containing the record
        information for the selected species and locations.
        A row consists of the plate ID, and spot 1–25. The spots can
        have a value 1 for present, or 0 for absent.

        Design Part: 1.19.1
        """

        # The available tables to save the spots to.
        tables = ('species_spots_1','species_spots_2')

        # Turn the list into a string, as it'll be included in the query.
        rec_ids_str = ",".join([str(item) for item in rec_ids])

        # Make a connection with the local database.
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor2 = connection.cursor()

        # Empty the required tables before we start.
        cursor.execute( "DELETE FROM %s" % (tables[slot]) )

        # Commit the database transaction.
        connection.commit()

        # Get plate ID and all 25 spots from each record that matches
        # the list of record IDs.
        cursor.execute( "SELECT rec_pla_id,"
                        "rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM records "
                        "WHERE rec_id IN (%s)" %
                        (rec_ids_str)
                        )

        # Insert each resulting row in the species_spots table.
        placeholders = ','.join('?' * 26)
        for row in cursor:
            cursor2.execute("INSERT INTO %s VALUES (null,%s)" %
                (tables[slot], placeholders), row)

        # Commit the database transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()


class AccessRemoteDB(AccessDBGeneric):
    """Retrieve data from the SETL database.

    Design Part: 1.29
    """

    def __init__(self):
        super(AccessRemoteDB, self).__init__()

