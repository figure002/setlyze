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

"""Facilitate access to the database.

The local SQLite database is created by :meth:`setlyze.database.MakeLocalDB.create_new_db`.
It is created using Python's SQLite module and is used internally by SETLyze
for storing and retrieving data for analyses. The database is a single file
created in the user's home directory in a subfolder called ``.setlyze``.

There are plans to create a central SETL database server which this module
can interact with. We refer to this database as the remote database.
"""

import sys
import os
import csv
import logging
import threading
import itertools
from sqlite3 import dbapi2 as sqlite
import re
import time
import xlrd

import gobject

import setlyze.config
import setlyze.std

# The current version of the local database.
DB_VERSION = 0.5

def get_database_accessor():
    """Return an object that facilitates access to the database.

    Based on the data source configuration, this function wil either
    return an instance of :class:`AccessLocalDB` or :class:`AccessRemoteDB`.
    This instance provides methods that are specific to the data source that
    is in use.

    Design Part: 1.93
    """
    data_source = setlyze.config.cfg.get('data-source')
    if data_source in ('data-files', 'setl-database'):
        db = AccessLocalDB()
    else:
        raise ValueError("Invalid data source '%s'." % data_source)
    return db

class MakeLocalDB(threading.Thread):
    """Create a local SQLite database with default tables and fill some
    tables based on the data source.

    This class can load data from three data sources. One data source is user
    supplied CSV files containing SETL data. The CSV files must be exported by
    the MS Access SETL database. The second source is the PostgreSQL SETL
    database. This function requires a direct connection with the SETL database
    server. The third source are XLS files containing SETL data. These files
    must be exported by MS Excel 97/2000/xp.

    Because the import of SETL data into the local database can take a while,
    and instance of this class must run in a separate thread. An instance of
    this class is therefor a thread object.

    Once a thread object is created, its activity must be started by calling
    the thread's start() method. This invokes the :meth:`run` method in a
    separate thread of control.

    Design Part: 1.2
    """

    def __init__(self, pd=None):
        super(MakeLocalDB, self).__init__()
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.data_source = setlyze.config.cfg.get('data-source')
        self.pdialog_handler = setlyze.std.ProgressDialogHandler(pd)
        self.connection = None
        self.cursor = None

    def on_exit(self):
        self.cursor.close()
        self.connection.close()

    def run(self):
        """Decide based on the configuration variables which functions should
        be called.

        This method first checks if SETLyze is configured to create a new local
        database. This is done by checking the value of configuration
        "make-new-db". If this is set to False, nothing will be done. If set
        to True, a new local database is created based on the value of the
        "data-source" configuration:

        ``setl-database``
          Method :meth:`insert_from_db` is called and some SETL data from the
          remote SETL database is loaded into the local database.

        ``data-files``
          Method :meth:`insert_from_data_files` is called which loads SETL data
          from the user supplied data files into the local database.

        Design Part: 1.31
        """

        # Check if we need to make a new database file.
        if setlyze.config.cfg.get('make-new-db'):
            # Create a new database file and make a database connection.
            self.create_new_db()

            # Create new database with data.
            if self.data_source == "setl-database":
                self.insert_from_db()
            elif self.data_source == "data-files":
                self.insert_from_data_files()
            else:
                # Exit gracefully.
                self.on_exit()
                raise ValueError("unknown data source '%s'" %
                    self.data_source)

            # Exit gracefully.
            self.on_exit()

            # Emit the signal that the local database has been created.
            # Note that the signal will be sent from a separate thread,
            # so we must use gobject.idle_add.
            gobject.idle_add(setlyze.std.sender.emit, 'local-db-created')

    def insert_from_data_files(self):
        """Create a new local database and load all SETL data from user
        selected CSV or Excel files into the local database.

        The SETL data is loaded from four separate files:

        * Locations file, containing the SETL locations.
        * Species ile, containing the SETL species.
        * Records file, containing the SETL records.
        * Plates file, containing the SETL plates.

        These files can be exported from the MS Access SETL database
        and contain all fields. CSV files must be delimited by semicolons (;)
        and double quotes (") as the quote character for fields with special
        characters. Excel (\*.xls) files must have the same format as the CSV
        files and must not have a header.

        Design Part: 1.32
        """
        logging.info("Loading SETL data from local files...")
        localities_file = setlyze.config.cfg.get('localities-file')
        plates_file = setlyze.config.cfg.get('plates-file')
        records_file = setlyze.config.cfg.get('records-file')
        species_file = setlyze.config.cfg.get('species-file')

        # If data_source is not set to "data-files", the required data
        # files are probably not set by the user yet. ChangeDataSource
        # must be called first.
        assert self.data_source == 'data-files', \
            "The data source is not set to 'data-files'"

        # Add some meta-data to a separate table in the local database.
        # Add the data source we can figure out what kind of data is
        # present.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)",
            ( self.data_source, ) )
        # Also insert the data of creation, so we can give the user an
        # indication when this database was created.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # Set the total number of times we're going to update the progress
        # dialog.
        self.pdialog_handler.set_total_steps(4)

        # Insert the data from the data files into the local database.
        try:
            filename = os.path.split(localities_file)[1]
            self.pdialog_handler.set_action("Importing %s" % filename)

            # Regular expression for matching Excel files. Because we support
            # .xlsx files, Python module xlrd version 0.8.0 or later is
            # required.
            re_excel = ".*\.(xls|xlsx)$"

            if re.match(re_excel, localities_file):
                self.insert_locations_from_xls(localities_file)
            else:
                self.insert_locations_from_csv(localities_file)

            filename = os.path.split(plates_file)[1]
            self.pdialog_handler.increase("Importing %s" % filename)

            if re.match(re_excel, plates_file):
                self.insert_plates_from_xls(plates_file)
            else:
                self.insert_plates_from_csv(plates_file)

            filename = os.path.split(records_file)[1]
            self.pdialog_handler.increase("Importing %s" % filename)

            if re.match(re_excel, records_file):
                self.insert_records_from_xls(records_file)
            else:
                self.insert_records_from_csv(records_file)

            filename = os.path.split(species_file)[1]
            self.pdialog_handler.increase("Importing %s" % filename)

            if re.match(re_excel, species_file):
                self.insert_species_from_xls(species_file)
            else:
                self.insert_species_from_csv(species_file)

            # Commit the database changes.
            self.connection.commit()
        except Exception as e:
            # Destroy the progress dialog.
            self.pdialog_handler.destroy()
            # Rollback changes to the database.
            self.connection.rollback()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'file-import-failed', e)
            return

        # If we are here, the import was successful.
        self.pdialog_handler.increase("")
        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

        return True

    def insert_locations_from_csv(self, filename, delimiter=';', quotechar='"'):
        """Insert the SETL localities from a CSV file into the local
        database.

        Argument `delimiter` is a one-character string used to separate fields
        in the CSV file, and `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file. The default
        values for these two arguments are suited for CSV files in Excel
        format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.18`.

        Design Part: 1.34
        """
        logging.info("Importing localities data from %s" % filename)

        # Try to open the CSV file.
        f = open(filename, 'r')

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum,row in enumerate(setl_reader):
            if len(row) != 5:
                raise ValueError("Expecting 5 fields per row for the "
                    "localities file, found %d fields." % len(row))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0:
                try:
                    row[0] = int(row[0])
                except:
                    continue

            self.cursor.execute("INSERT INTO localities VALUES (?,?,?,?,?)",
                row)

    def insert_species_from_csv(self, filename, delimiter=';', quotechar='"'):
        """Insert the species from a CSV file into the local database.

        Argument `delimiter` is a one-character string used to separate fields
        in the CSV file, and `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file. The default
        values for these two arguments are suited for CSV files in Excel
        format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.19`.

        Design Part: 1.35
        """
        logging.info("Importing species data from %s" % filename)

        # Try to open the CSV file.
        f = open(filename, 'r')

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum,row in enumerate(setl_reader):
            n = len(row)
            if n > 17:
                raise ValueError("Expecting at most 17 fields per row for the "
                    "species file, found %d fields." % n)

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0:
                try:
                    row[0] = int(row[0])
                except:
                    continue

            row_new = []
            for i in range(17):
                try:
                    val = row[i]
                    if val == '':
                        row_new.append(None)
                    elif val == 'FALSE':
                        row_new.append(False)
                    elif val == 'TRUE':
                        row_new.append(True)
                    else:
                        row_new.append(val)
                except:
                    row_new.append(None)

            placeholders = ','.join('?' * 17)
            self.cursor.execute("INSERT INTO species VALUES (%s)" %
                placeholders,
                row_new
            )

    def insert_plates_from_csv(self, filename, delimiter=';', quotechar='"'):
        """Insert the plates from a CSV file into the local database.

        Argument `delimiter` is a one-character string used to separate fields
        in the CSV file, and `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file. The default
        values for these two arguments are suited for CSV files in Excel
        format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.20`.

        Design Part: 1.36
        """
        logging.info("Importing plates data from %s" % filename)

        # Try to open the CSV file.
        f = open(filename, 'r')

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum,row in enumerate(setl_reader):
            if len(row) != 10:
                raise ValueError("Expecting 10 fields per row for the "
                    "plates file, found %d fields." % len(row))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0:
                try:
                    row[0] = int(row[0])
                except:
                    continue

            self.cursor.execute("INSERT INTO plates VALUES (?,?,?,?,?,?,?,?,?,?)",
                row)

    def insert_records_from_csv(self, filename, delimiter=';', quotechar='"'):
        """Insert the records from a CSV file into the local database.

        Argument `delimiter` is a one-character string used to separate fields
        in the CSV file, and `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file. The default
        values for these two arguments are suited for CSV files in Excel
        format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.21`.

        Design Part: 1.37
        """
        logging.info("Importing records data from %s" % filename)

        # Try to open the CSV file.
        f = open(filename, 'r')

        # Use Python's CSV module to create a CSV reader.
        setl_reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        placeholders = ','.join('?' * 38)
        for rownum,row in enumerate(setl_reader):
            if len(row) != 40:
                raise ValueError("Expecting 40 fields per row for the "
                    "records file, found %d fields." % len(row))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0:
                try:
                    row[0] = int(row[0])
                except:
                    continue

            self.cursor.execute("INSERT INTO records VALUES (%s)" % placeholders,
                row[:38])

    def insert_locations_from_xls(self, filename):
        """Insert the SETL localities from a XLS file into the local
        database.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.18`.

        Design Part: TODO
        """
        logging.info("Importing localities data from %s" % filename)

        # Try to open the XLS file.
        f = xlrd.open_workbook(filename)

        # Use Python's xlrd module to create a XLS reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the XLS file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            values = setl_reader.row_values(rownum)
            if len(values) != 5:
                raise ValueError("Expecting 5 fields per row for the "
                    "localities file, found %d fields." % len(values))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0 and isinstance(values[0], unicode):
                continue

            self.cursor.execute("INSERT INTO localities VALUES (?,?,?,?,?)",
                values)

    def insert_plates_from_xls(self, filename):
        """Insert the plates from a XLS file into the local database.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.20`.

        Design Part: TODO
        """
        logging.info("Importing plates data from %s" % filename)

        # Try to open the XLS file.
        f = xlrd.open_workbook(filename)

        # Use Python's xlrd module to create a XLS reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the XLS file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            values = setl_reader.row_values(rownum)

            if len(values) != 10:
                raise ValueError("Expecting 10 fields per row for the "
                    "plates file, found %d fields." % len(values))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0 and isinstance(values[0], unicode):
                continue

            self.cursor.execute("INSERT INTO plates VALUES (?,?,?,?,?,?,?,?,?,?)",
                values)

    def insert_records_from_xls(self, filename):
        """Insert the records from a XLS file into the local database.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.21`.

        Design Part: TODO
        """
        logging.info("Importing records data from %s" % filename)

        # Try to open the XLS file.
        f = xlrd.open_workbook(filename)

        # Use Python's xlrd module to create a XLS reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the xls file and insert that row
        # into the local database.
        placeholders = ','.join('?' * 38)
        for rownum in range(setl_reader.nrows):
            values = setl_reader.row_values(rownum)

            if len(values) < 38:
                raise ValueError("Expecting at least 38 fields per row for the "
                    "records file, found %d fields." % len(values))

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0 and isinstance(values[0], unicode):
                continue

            self.cursor.execute("INSERT INTO records VALUES (%s)" % placeholders,
                values[:38])

    def insert_species_from_xls(self, filename):
        """Insert the species from a XLS file into the local database.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.19`.

        Design Part: 1.35(b) TODO
        """
        logging.info("Importing species data from %s" % filename)

        # Try to open the XLS file.
        f = xlrd.open_workbook(filename)

        # Use Python's xlrd module to create a XLS reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the XLS file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            values = setl_reader.row_values(rownum)

            n = len(values)
            if n > 17:
                raise ValueError("Expecting at most 17 fields per row for the "
                    "species file, found %d fields." % n)

            # Check if the first row contains headers by checking if the first
            # field in the first row is a string. If so, skip the first row.
            if rownum == 0 and isinstance(values[0], unicode):
                continue

            placeholders = ','.join('?' * 17)
            row = []
            for i in range(17):
                try:
                    val = values[i]
                    if val == '':
                        row.append(None)
                    else:
                        row.append(val)
                except:
                    row.append(None)

            self.cursor.execute("INSERT INTO species VALUES (%s);" %
                placeholders,
                row
            )

    def insert_from_db(self):
        """Create a new local database and load localities and species
        data from the remote SETL database into the local database.

        This method requires a direct connection with the SETL
        database server.

        The reason why we don't load all SETL data into the local database
        is because we can execute queries on the remote database. So
        there's no need to load large amounts of data onto the user's
        computer. Because the localities and species data is accessed
        often, loading this into the local database increases speed of
        the application.

        Design Part: 1.33
        """
        logging.info("Creating local database from SETL database...")

        # Set the total number of times we're going to update the progress
        # dialog.
        self.pdialog_handler.set_total_steps(2)

        # Update progress dialog.
        self.pdialog_handler.increase()

        # Next time we run the tool, we'll know what data is in the database.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)",
            (self.data_source,) )
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # Commit the transaction.
        self.connection.commit()

        # TODO: Actually insert data from SETL database.
        logging.info("Loading data from the remote SETL database...")

        # Update progress dialog.
        self.pdialog_handler.increase()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

        return True

    def create_new_db(self):
        """Create a new local database.

        This deletes any existing database file.

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
            self.remove_db_file()

        # Create a new database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Create the tables.
        self.create_table_info()
        self.create_table_localities()
        self.create_table_species()
        self.create_table_plates()
        self.create_table_records()

        # Commit the transaction.
        self.connection.commit()

        # No need to make a new database, as we just created one.
        setlyze.config.cfg.set('make-new-db', False)

    def remove_db_file(self, tries=0):
        """Remove the database file.

        This method does three tries if for some reason the database file
        could not be deleted (e.g. the file is in use by a different process).
        """
        if tries > 2:
            raise EnvironmentError("Failed to delete database file %s. "
                "It may be in use by a different process." % self.dbfile)
        try:
            os.remove(self.dbfile)
        except:
            tries += 1
            time.sleep(2)
            self.remove_db_file(tries)
        return True

    def create_table_info(self):
        """Create the "info" table for storing general information.

        This information includes its creation date and the data source.
        The data source is either the SETL database (MS Access/PostgreSQL)
        or XLS/CSV files containing SETL data. A version number for the
        database is also saved. This could be handy in the future,
        for example we can notify the user if the local database is
        too old, followed by creating a new local database.

        Design Part: 1.75
        """
        self.cursor.execute("CREATE TABLE info (\
            id INTEGER PRIMARY KEY, \
            name VARCHAR, \
            value VARCHAR)"
            )

        self.cursor.execute("INSERT INTO info "
            "VALUES (null, 'version', ?)", [DB_VERSION])

    def create_table_localities(self):
        """Create the "localities" table for the SETL locations.

        Because the data from this table is accessed frequently, the
        localities records are automatically saved to this table when
        an analyze is started.

        Design Part: 1.76
        """
        # Design Part: 2.4
        self.cursor.execute("CREATE TABLE localities (\
            loc_id INTEGER PRIMARY KEY, \
            loc_name VARCHAR, \
            loc_nr VARCHAR, \
            loc_coordinates VARCHAR, \
            loc_description VARCHAR \
        )")

    def create_table_species(self):
        """Create the "species" table for the SETL species.

        Because the data from this table is accessed frequently, the
        species records are automatically saved to this table when
        an analyze is started.

        Design Part: 1.77
        """

        # Design Part: 2.3
        self.cursor.execute("CREATE TABLE species (\
            spe_id INTEGER PRIMARY KEY, \
            spe_name_venacular VARCHAR, \
            spe_name_latin VARCHAR, \
            spe_invasive_in_nl INTEGER, \
            spe_description VARCHAR, \
            spe_remarks VARCHAR, \
            spe_picture VARCHAR, \
            spe_aphia_id INTEGER, \
            spe_kingdom VARCHAR, \
            spe_phylum VARCHAR, \
            spe_class VARCHAR, \
            spe_order VARCHAR, \
            spe_family VARCHAR, \
            spe_genus VARCHAR, \
            spe_subgenus VARCHAR, \
            spe_species VARCHAR, \
            spe_subspecies VARCHAR \
        )")

    def create_table_plates(self):
        """Create the "plates" table for the SETL plates.

        This table is only filled if the user selected CSV or XLS files to
        import SETL data from. If the remote SETL database is used,
        the plate records are obtained directly via queries.

        Design Part: 1.78
        """
        # Design Part: 2.16
        self.cursor.execute("CREATE TABLE plates (\
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

    def create_table_records(self):
        """Create the "records" table for the SETL records.

        This table is only filled if the user selected CSV or XLS files to
        import SETL data from. If the remote SETL database is used,
        the records are obtained directly via queries.

        Design Part: 1.79
        """

        # Design Part: 2.5
        self.cursor.execute("CREATE TABLE records (\
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

class AccessDBGeneric(object):
    """Super class for :class:`AccessLocalDB` and :class:`AccessRemoteDB`.

    This class contains methods that are generic for both sub-classes.
    It provides both sub classes with methods for data that is always
    present in the local database.
    """

    def __init__(self):
        self.progress_dialog = None
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.conn = sqlite.connect(self.dbfile)
        self.cursor = self.conn.cursor()

    def get_database_info(self):
        """Return database information.

        These include the creation date and the data source.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name,value FROM info;")
        info = cursor.fetchall()
        info = dict(info)
        cursor.close()

        # Some types need to be converted from string.
        to_float = ['version']
        for key in to_float:
            info[key] = float(info[key])

        return info

    def get_locations(self):
        """Return a list of all locations from the local database.

        Returns a list of tuples ``(loc_id, 'loc_name')``.

        Design Part: 1.95
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT loc_id, loc_name FROM localities")
        locations = cursor.fetchall()
        cursor.close()
        return locations

    def make_plates_unique(self, slot):
        """Combine the records with the same plate ID in a spots table.

        The value for `slot` defines which spots table is used.
        The possible values of `slot` are ``0`` for table
        "species_spots_1" and ``1`` for table "species_spots_2".

        We're doing this so we can threat multiple species selected by
        the user as a single species.

        Returns the total numbers of distinctive plates.

        Design Part: 1.20
        """
        tables = ('species_spots_1','species_spots_2')

        # Get all distinctive plate IDs.
        cursor = self.conn.cursor()
        cursor.execute( "SELECT DISTINCT rec_pla_id FROM %s" % (tables[slot]) )
        pla_ids = cursor.fetchall()

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

            # Create a combined record from all records with this plate ID.
            rows = cursor.fetchall()

            # No need to do anything if there is just one record for a plate.
            if len(rows) < 2:
                continue

            # Remove all records with that plate ID from the species_spots table.
            cursor.execute( "DELETE FROM %s "
                            "WHERE rec_pla_id = ?" %
                            (tables[slot]),
                            (pla_id[0],)
            )

            # Insert the combined record in the species_spots table. So this
            # single record replaces all other records with this plate ID.
            combined = setlyze.std.combine_records(rows)
            placeholders = ','.join('?' * 26)
            cursor.execute("INSERT INTO %s VALUES (null,%s)" %
                            (tables[slot], placeholders),
                            combined
            )

        # Commit the database transaction.
        self.conn.commit()
        cursor.close()

        # Return the total numbers of unique plate records.
        return len(pla_ids)

    def fill_plate_spot_totals_table(self, spots_table1, spots_table2=None):
        """Populate table "plate_spot_totals".

        This table is populated with the number of positive spots for each
        plate. The information is obtained from the spots tables `spots_table1`
        and optionally `spots_table2`.

        The "plate_spot_totals" table is used in several situations:

            * Calculating the expected distances, where the positive spot
              number serves as a template for the random spots generator
              (see :meth:`~setlyze.std.get_random_for_plate`).

            * Significance calculators, where the tests are applied to
              plates with a specific number of positive spots (see
              :meth:`get_distances_matching_spots_total`).

        If just `spots_table1` is provided, only the column "n_spots_a"
        is populated with positive spot numbers. If both `spots_table1` and
        `spots_table2` are provided, column "n_spots_a" is filled
        from `spots_table1`, and column "n_spots_b" filled from `spots_table2`.

        Returns a tuple (`rows affected`, `rows skipped`).

        Design Part: 1.73
        """
        cursor = self.conn.cursor()
        cursor2 = self.conn.cursor()

        # Empty the plate_spot_totals table before we use it again.
        cursor.execute("DELETE FROM plate_spot_totals")
        self.conn.commit()

        skipped = 0
        rowcount = 0

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
                plate_id = record[1]

                # Get the positive spots for both records.
                spots1 = setlyze.std.get_spots_from_record(record1)
                spots2 = setlyze.std.get_spots_from_record(record2)

                # We're only interested in the number of spots.
                spots1 = len(spots1)
                spots2 = len(spots2)

                # Skip this plate if both records contain less than 1 positive
                # spot. We won't be able to calculate distances for such
                # records anyway.
                if spots1 < 1 and spots2 < 1:
                    skipped += 1
                    continue

                # Save the number of positive spots to the plate_spot_totals
                # table.
                cursor2.execute( "INSERT INTO plate_spot_totals "
                                 "VALUES (?,?,?)",
                                 (plate_id, spots1, spots2)
                )
                rowcount += 1
        else:
            # One spots table is provided.

            # Get all spots for each plate.
            # Each returned record has this format:
            # id|rec_pla_id|rec_sur1|rec_sur2|rec_sur3|rec_sur4|rec_sur5|
            # rec_sur6|rec_sur7|rec_sur8|rec_sur9|rec_sur10|rec_sur11|
            # rec_sur12|rec_sur13|rec_sur14|rec_sur15|rec_sur16|rec_sur17|
            # rec_sur18|rec_sur19|rec_sur20|rec_sur21|rec_sur22|rec_sur23|
            # rec_sur24|rec_sur25
            cursor.execute("SELECT * FROM %s" % spots_table1)

            for record in cursor:
                plate_id = record[1]

                # Get the positive spots for this record.
                spots = setlyze.std.get_spots_from_record(record[2:])

                # We're only interested in the number of spots.
                spots = len(spots)

                # Skip this record if it contains less than 2 positive spots.
                # We won't be able to calculate a distance for such records
                # anyway.
                if spots < 2:
                    skipped += 1
                    continue

                # Save the number of positive spots to the plate_spot_totals
                # table.
                cursor2.execute( "INSERT INTO plate_spot_totals "
                                 "VALUES (?,?,null)",
                                 (plate_id, spots)
                )
                rowcount += 1

        # Commit the transaction.
        self.conn.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()

        # Return the number of (rows affected, rows skipped)
        return (rowcount, skipped)

    def get_distances_matching_spots_total(self, distance_table, spots_n):
        """Get the distances from distance table `distance_table` that
        are from plates having `spots_n` positive spot numbers.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns the distances.
        """
        cursor = self.conn.cursor()

        if spots_n < 0:
            # If spots_n is a negative number, get all distances
            # up to the absolute number. So if we find -5, get all
            # distances up to 5.
            cursor.execute("SELECT distance FROM %s" % distance_table)

            # Get the plate IDs that have n spots lower or equal to the
            # absolute spots number.
            cursor.execute( "SELECT pla_id "
                            "FROM plate_spot_totals "
                            "WHERE n_spots_a <= %d" %
                            (abs(spots_n))
                            )
            plate_ids = cursor.fetchall()
            plate_ids_str = ",".join([str(item[0]) for item in plate_ids])

            # Get the distances that match the plate IDs.
            cursor.execute( "SELECT distance "
                            "FROM %s "
                            "WHERE rec_pla_id IN (%s)" %
                            (distance_table, plate_ids_str)
                            )
        else:
            # Get the plate IDs that match the provided total spots number.
            cursor.execute( "SELECT pla_id "
                            "FROM plate_spot_totals "
                            "WHERE n_spots_a = %d" %
                            (spots_n)
                            )
            plate_ids = cursor.fetchall()
            plate_ids_str = ",".join([str(item[0]) for item in plate_ids])

            # Get the distances that match the plate IDs.
            cursor.execute( "SELECT distance "
                            "FROM %s "
                            "WHERE rec_pla_id IN (%s)" %
                            (distance_table, plate_ids_str)
                            )

        # Save the number of matching plates. Note that this variable can only
        # be called after the iter that this generator returns was used.
        self.matching_plates_total = len(plate_ids)

        # Return all matching distances.
        for distance in cursor:
            yield distance[0]

        # Close connection with the local database.
        cursor.close()

    def get_distances_matching_ratios(self, distance_table, ratios):
        """Get the spot distances from distance table `distance_table` where
        positive spots numbers between species A and B have ratio
        matching the list of ratios `ratios`.

        The ratio A:B is considered the same as B:A.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns the distances.
        """
        cursor = self.conn.cursor()
        plate_ids = []

        for ratio in ratios:
            # Get the plate IDs that match the ratio A:B.
            cursor.execute( "SELECT pla_id "
                            "FROM plate_spot_totals "
                            "WHERE n_spots_a = %d "
                            "AND n_spots_b = %d" %
                            (ratio[0], ratio[1])
                            )

            # Add the plate IDs to the list of plate IDs.
            ids = [x[0] for x in cursor.fetchall()]
            plate_ids.extend(ids)

            # We need the complement ratio B:A as well, so we get the
            # plate IDs for the complement as well.

            # No need to get the complement ratio if it's the same.
            if ratio[0] == ratio[1]:
                continue

            # Get the plate IDs that match the complement ratio B:A.
            cursor.execute( "SELECT pla_id "
                            "FROM plate_spot_totals "
                            "WHERE n_spots_a = %d "
                            "AND n_spots_b = %d" %
                            (ratio[1], ratio[0])
                            )

            # Add the plate IDs to the list of plate IDs.
            ids = [x[0] for x in cursor.fetchall()]
            plate_ids.extend(ids)

        # Save the number of matching plates. Note that this variable can only
        # be called after the iter that this generator returns was used.
        self.matching_plates_total = len(plate_ids)

        # Turn the list of plate IDs into a string.
        plate_ids_str = ",".join([str(x) for x in plate_ids])

        # Get the distances that match the plate IDs.
        cursor.execute( "SELECT distance "
                        "FROM %s "
                        "WHERE rec_pla_id IN (%s)" %
                        (distance_table, plate_ids_str)
                        )

        # Return all matching distances.
        for distance in cursor:
            yield distance[0]

        # Close connection with the local database.
        cursor.close()

    def get_area_totals(self, plate_area_totals_table, area_group):
        """Return total number of positive spots per area group per plate.

        Argument `plate_area_totals_table` is either
        ``plate_area_totals_observed`` or ``plate_area_totals_expected``.
        The area group `area_group` can be a sequence containing a
        combination of the letters A, B, C, and D. Each letter is one of
        the default areas on a SETL plate.
        """
        cursor = self.conn.cursor()

        # Compile a string containing the area fields for 'area_group'.
        fields = []
        for area in area_group:
            if area == 'A':
                fields.append('area_a')
            elif area == 'B':
                fields.append('area_b')
            elif area == 'C':
                fields.append('area_c')
            elif area == 'D':
                fields.append('area_d')
        fields_str = ",".join(fields)

        # Get the area totals for the areas in area group.
        cursor.execute( "SELECT %s FROM %s" %
                        (fields_str, plate_area_totals_table)
                        )

        if len(fields) > 1:
            # We're dealing with combined areas, so we will return the total of
            # the areas combined.
            for totals in cursor:
                total = 0
                for t in totals:
                    total += t
                yield total
        else:
            # One field, so one total is returned per row.
            for total in cursor:
                yield total[0]

        # Close connection with the local database.
        cursor.close()

    def get_plates_total_matching_spots_total(self, n_spots, slot=0):
        """Return the number of plates that match the provided number of
        positive spots `n_spots`.

        Possible values for `slot` are 0 for the first species selection,
        and 1 for the second species selection.
        """
        cursor = self.conn.cursor()

        if slot == 0:
            field = 'n_spots_a'
        elif slot == 1:
            field = 'n_spots_b'
        else:
            raise ValueError("Possible values for 'slot' are 0 and 1.")

        if n_spots < 0:
            # If spots_n is a negative number, get all distances
            # up to the absolute number. So if we find -5, get all
            # distances with up to 5 spots.
            cursor.execute( "SELECT COUNT(pla_id) "
                            "FROM plate_spot_totals "
                            "WHERE %s <= ?" % (field),
                            [abs(n_spots)])
            n_plates = cursor.fetchone()[0]
        else:
            # If it's a positive number, just get the plates that
            # match that spots number.
            cursor.execute( "SELECT COUNT(pla_id) "
                            "FROM plate_spot_totals "
                            "WHERE %s = ?" % (field),
                            [n_spots])
            n_plates = cursor.fetchone()[0]

        cursor.close()
        return n_plates

class AccessLocalDB(AccessDBGeneric):
    """Provide standard methods for accessing data in the local
    SQLite database. These methods are only used when the data source
    is set to ``data-files``.

    Inherits from :class:`AccessDBGeneric` which provides this
    class with methods that are not data source specific.

    Design Part: 1.28
    """

    def __init__(self):
        super(AccessLocalDB, self).__init__()

    def create_table_species_spots_1(self):
        """Create temporary table "species_spots_1".

        This table will contain the SETL records for the first species
        selection.

        Because the user can select multiple species, the plate IDs in column
        "rec_pla_id" don't have to be unique, so we're creating a separate
        column "id" as the primary key.

        Design Part: 1.80
        Creates Design Part: 2.9, 2.9.1, 2.9.2
        """
        self.cursor.execute("CREATE TEMP TABLE species_spots_1 (\
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


    def create_table_species_spots_2(self):
        """Create temporary table "species_spots_2".

        This table will contain the SETL records for the second species
        selection.

        Because the user can select multiple species, the plate IDs in column
         "rec_pla_id" don't have to be unique, so we're creating a separate
         column "id" as the primary key.

        Design Part: 1.81
        Creates Design Part: 2.10, 2.10.1, 2.10.2
        """
        self.cursor.execute("CREATE TEMP TABLE species_spots_2 (\
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

    def create_table_spot_distances_observed(self):
        """Create temporary table "spot_distances_observed".

        This table is used to store observed spot distances.

        Design Part: 1.83
        Creates Design Part: 2.12
        """
        self.cursor.execute("CREATE TEMP TABLE spot_distances_observed (\
            id INTEGER PRIMARY KEY, \
            rec_pla_id INTEGER, \
            distance REAL \
        )")

    def create_table_spot_distances_expected(self):
        """Create temporary table "spot_distances_expected".

        This table is used to store expected spot distances.

        Design Part: 1.84
        Creates Design Part: 2.13
        """
        self.cursor.execute("CREATE TEMP TABLE spot_distances_expected (\
            id INTEGER PRIMARY KEY, \
            rec_pla_id INTEGER, \
            distance REAL \
        )")

    def create_table_plate_spot_totals(self):
        """Create temporary table "plate_spot_totals".

        This table is used to store the total of spots per plate.

        Design Part: 1.85
        Creates Design Part: 2.39
        """
        self.cursor.execute("CREATE TEMP TABLE plate_spot_totals (\
            pla_id INTEGER PRIMARY KEY, \
            n_spots_a INTEGER, \
            n_spots_b INTEGER \
        )")

    def create_table_plate_area_totals_observed(self):
        """Create temporary table "plate_area_totals_observed".

        This table is used to store the total of positive spots per plate area
        per plate ID.

        Design Part:
        """

        # Design Part:
        self.cursor.execute("CREATE TEMP TABLE plate_area_totals_observed (\
            pla_id INTEGER PRIMARY KEY, \
            area_a INTEGER, \
            area_b INTEGER, \
            area_c INTEGER, \
            area_d INTEGER \
        )")

    def create_table_plate_area_totals_expected(self):
        """Create temporary table "plate_area_totals_expected".

        This table is used to store the total of expected positive spots per
        plate area per plate ID.

        Design Part: TODO
        """
        self.cursor.execute("CREATE TEMP TABLE plate_area_totals_expected (\
            pla_id INTEGER PRIMARY KEY, \
            area_a INTEGER, \
            area_b INTEGER, \
            area_c INTEGER, \
            area_d INTEGER \
        )")

    def get_species(self, locations):
        """Return species that match a locations selection `locations`.

        Species are returned as tuples in the format
        ``(id, 'common_name', 'latin_name')``. Argument `locations` is a list
        of location IDs.

        Design Part: 1.96
        """
        cursor = self.conn.cursor()

        # Select all plate IDs from plates that are from the selected
        # locations.
        placeholders = ','.join('?' * len(locations))
        cursor.execute("SELECT pla_id FROM plates WHERE pla_loc_id IN (%s)" %
            (placeholders), locations)
        # Construct a list with the IDs
        pla_ids = [row[0] for row in cursor]
        # Remove duplicates.
        pla_ids = setlyze.std.uniqify(pla_ids)
        # Create a string of the IDs for the query.
        pla_ids_str = ",".join([str(id) for id in pla_ids])

        # Select all species IDs from records with those plate IDs.
        cursor.execute("SELECT rec_spe_id FROM records WHERE rec_pla_id IN (%s) AND rec_spe_id != ''" % pla_ids_str)
        # Construct a list with the IDs
        spe_ids = [row[0] for row in cursor]
        # Remove duplicates.
        spe_ids = setlyze.std.uniqify(spe_ids)
        # Create a string of the IDs for the query.
        spe_ids_str = ",".join([str(id) for id in spe_ids]) # Turn the list into a string
        #print "spe_ids: ", spe_ids

        # Select information from species that match those species IDs.
        cursor.execute("SELECT spe_id,spe_name_venacular,spe_name_latin,"
            "spe_invasive_in_nl,spe_phylum,spe_class,spe_order,spe_family,"
            "spe_genus,spe_species,spe_subspecies FROM species WHERE spe_id IN (%s)" % spe_ids_str)
        species = cursor.fetchall()

        cursor.close()
        return species

    def get_record_ids(self, locations, species):
        """Return records that match the locations and species selections.

        Returns a list of record IDs that match the locations IDs
        in the list `locations` and the species IDs in the list `species`.

        Both `locations` and `species` can be an integer instead of a list with
        a single integer.

        Design Part: 1.41
        """
        # Create strings containing all the selected locations and
        # species IDs. These will be part of the queries below.
        if isinstance(locations, int):
            loc_ids_str = str(locations)
        else:
            loc_ids_str = ",".join([str(id) for id in locations])

        if isinstance(species, int):
            spe_ids_str = str(species)
        else:
            spe_ids_str = ",".join([str(id) for id in species])

        # Get the plate IDs that match the selected locations.
        cursor = self.conn.cursor()
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

        cursor.close()
        return rec_ids

    def get_spots(self, rec_ids):
        """Return all 25 spot booleans for the records with IDs matching
        the list of record IDs `rec_ids`.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns tuples with the 25 spot booleans for
        all matching records.
        """
        # Create a string of the IDs for the query.
        rec_ids_str = ",".join([str(id) for id in rec_ids])

        # Get all 25 spots from each record that matches the list of
        # record IDs.
        cursor = self.conn.cursor()
        cursor.execute( "SELECT rec_sur1,rec_sur2,rec_sur3,rec_sur4,rec_sur5,"
                        "rec_sur6,rec_sur7,rec_sur8,rec_sur9,rec_sur10,"
                        "rec_sur11,rec_sur12,rec_sur13,rec_sur14,rec_sur15,"
                        "rec_sur16,rec_sur17,rec_sur18,rec_sur19,rec_sur20,"
                        "rec_sur21,rec_sur22,rec_sur23,rec_sur24,rec_sur25 "
                        "FROM records "
                        "WHERE rec_id IN (%s)" % (rec_ids_str)
                        )

        for record in cursor:
            yield record
        cursor.close()

    def set_species_spots(self, rec_ids, slot):
        """Create a table in the local database containing the spots
        information for SETL records matching `rec_ids`. Two spots
        tables can be created. The values for `slot` can be ``0`` for table
        ``species_spots_1`` and ``1`` for ``species_spots_2``.

        Each record in the spots table consists of the plate ID followed
        by the 25 spot booleans.

        Design Part: 1.19.1
        """
        cursor = self.conn.cursor()
        cursor2 = self.conn.cursor()

        # The available tables to save the spots to.
        tables = ('species_spots_1','species_spots_2')

        # Turn the list into a string, as it'll be included in the query.
        rec_ids_str = ",".join([str(item) for item in rec_ids])

        # Empty the required tables before we start.
        cursor.execute( "DELETE FROM %s" % (tables[slot]) )

        # Commit the database transaction.
        self.conn.commit()

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
        self.conn.commit()
        cursor.close()
        cursor2.close()

class AccessRemoteDB(AccessDBGeneric):
    """Provide standard methods for accessing data in the remote
    PostgreSQL SETL database. These methods are only used when the data
    source is set to ``setl-database``.

    Inherits from :class:`AccessDBGeneric` which provides this
    class with methods that are not data source specific.

    Design Part: 1.29
    """

    def __init__(self):
        super(AccessRemoteDB, self).__init__()

