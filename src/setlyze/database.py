#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Copyright 2010, GiMaRIS <info@gimaris.com>
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

"""Facilitate access to the local SQLite database and the remote SETL
database.

The local SQLite database is created by :meth:`setlyze.database.MakeLocalDB.create_new_db`.
It is created using the SQLite Python module. This database is used
internally by SETLyze for local data storage and allows for the
execution of SQL queries. The database is a single file created in the
user's home directory in a subfolder called ``.setlyze``.

Here we refer to the PostgreSQL SETL database as the remote SETL
database.
"""

import sys
import os
import csv
import logging
import threading
import itertools
from sqlite3 import dbapi2 as sqlite
import time
import xlrd

import gobject

import setlyze.config
import setlyze.std

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.1.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2011/05/03"

def get_database_accessor():
    """Return an object that facilitates access to either the local or
    the remote database.

    Based on the data source configuration, obtained with
    ``setlyze.config.cfg.get('data-source')``, this function wil either
    return an instance of AccessLocalDB or AccessRemoteDB. This instance
    provides methods that are specific to the data source currently in
    use.

    Design Part: 1.93
    """
    data_source = setlyze.config.cfg.get('data-source')
    if data_source == "csv-msaccess":
        db = AccessLocalDB()
    elif data_source == "setl-database":
        db = AccessRemoteDB()
    elif data_source == "xls":
        db = AccessLocalDB()
    else:
        logging.error("setlyze.database.get_database_accessor: '%s' is not a valid data source." % data_source)
        sys.exit(1)
    return db

def get_plates_total_matching_spots_total(n_spots, slot=0):
    """Return an integer representing the number of plates that
    match the provided number of positive spots `n_spots`.

    Possible values for `slot` are 0 for the first species selection,
    and 1 for the second species selection.
    """
    connection = sqlite.connect(setlyze.config.cfg.get('db-file'))
    cursor = connection.cursor()

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
    connection.close()

    return n_plates


class MakeLocalDB(threading.Thread):
    """Create a local SQLite database with default tables and fill some
    tables based on the data source.

    This class can load data from two data sources. One data source
    is user supplied CSV files containing SETL data. The CSV files must
    be exported by the MS Access SETL database.
    The second source is the PostgreSQL SETL database. This function
    requires a direct connection with the SETL database server.

    Because the import of SETL data into the local database can take
    a while, and instance of this class must run in a separate thread.
    An instance of this class is therefor a thread object.

    Once a thread object is created, its activity must be started by
    calling the thread’s start() method. This invokes the run() method
    in a separate thread of control.

    Design Part: 1.2
    """

    def __init__(self):
        logging.debug("MakeLocalDB.__init__ is called")        
        super(MakeLocalDB, self).__init__()

        self.cursor = None
        self.connection = None
        self.dbfile = setlyze.config.cfg.get('db-file')
        self.pdialog_handler = setlyze.std.ProgressDialogHandler()

    def run(self):
        """Decide based on the configuration variables which functions
        should be called.

        This method first checks if SETLyze is configured to create
        a new local database. This is done by checking the value of
        ``setlyze.config.cfg.get('make-new-db')``. If this is set to
        ``False``, the method ends and the thread is destroyed. If set
        to ``True``, a new local database is created based on the data
        source configuration.

        The data source configuration is checked by calling
        ``setlyze.config.cfg.get('data-source')``. If this is set to
        ``setl-database``, the method ``insert_from_db`` is called and
        some SETL data from the remote SETL database is loaded into the
        local database. If set to ``csv-msaccess``, the method
        ``insert_from_csv`` is called which loads all SETL data from the
        supplied CSV files into the local database.

        Design Part: 1.31
        """

        # Check if we need to make a new database file.
        if setlyze.config.cfg.get('make-new-db'):
            # Create new database with data.
            if setlyze.config.cfg.get('data-source') == "setl-database":
                self.insert_from_db()
            elif setlyze.config.cfg.get('data-source') == "csv-msaccess":
                self.insert_from_csv()
            elif setlyze.config.cfg.get('data-source') == "xls":
                self.insert_from_xls()
            else:
                raise ValueError("Encountered unknown data source '%s'" %
                    setlyze.config.cfg.get('data-source'))

            # Emit the signal that the local database has been created.
            # Note that the signal will be sent from a separate thread,
            # so we must use gobject.idle_add.
            gobject.idle_add(setlyze.std.sender.emit, 'local-db-created')

    def insert_from_csv(self):
        """Create a new local database and load all SETL data from the
        user selected CSV files into the local database.

        The SETL data is loaded from four separate CSV files:
            * localities_file, containing the SETL locations.
            * species_file, containing the SETL species.
            * records_file, containing the SETL records.
            * plates_file, containing the SETL plates.

        These files must be exported from the MS Access SETL database
        and contain all fields. The CSV file must be in Excel format,
        which means delimited by semicolons (;) and double quotes (") as
        the quote character for fields with special characters.

        Design Part: 1.32
        """
        logging.info("Creating local database from CSV files...")

        # If data_source is not set to "csv-msaccess", the required data
        # files are probably not set by the user yet. ChangeDataSource
        # must be called first.
        if setlyze.config.cfg.get('data-source') != 'csv-msaccess':
            raise ValueError("Cannot run this function while 'data-source' is "
                "set to '%s'." % setlyze.config.cfg.get('data-source'))

        # First, create a new database file.
        self.create_new_db()

        # Create a connection with the local database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Add some meta-data to a separate table in the local database.
        # Add the data source we can figure out what kind of data is
        # present.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)",
            ( setlyze.config.cfg.get('data-source'), ) )
        # Also insert the data of creation, so we can give the user an
        # indication when this database was created.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # Set the total number of times we're going to update the progress
        # dialog.
        self.pdialog_handler.set_total_steps(4)

        # Insert the data from the CSV files into the local database.
        filename = os.path.split(setlyze.config.cfg.get('localities-file'))[1]
        self.pdialog_handler.set_action("Importing %s" % filename)
        try:
            self.insert_localities_from_csv()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading localities data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('plates-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_plates_from_csv()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading plates data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('records-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_records_from_csv()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading records data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('species-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_species_from_csv()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading species data from %s failed." % filename)
            return

        # If we are here, the import was successful. Set the progress dialog
        # to 100%.
        self.pdialog_handler.increase("")

        # Close the connection with the database.
        self.cursor.close()
        self.connection.close()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

        return True

    def insert_localities_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the SETL localities from a CSV file into the local
        database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.18`.

        Design Part: 1.34
        """
        logging.info("Importing localities data from %s" % setlyze.config.cfg.get('localities-file'))

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
            if len(row) != 5:
                raise ValueError("Expecting 5 fields per row for the "
                    "localities CSV file, found %d fields." % len(row))

            self.cursor.execute("INSERT INTO localities VALUES (?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_species_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the species from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.19`.

        Design Part: 1.35
        """
        logging.info("Importing species data from %s" % setlyze.config.cfg.get('species-file'))

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
            if len(row) not in (6, 7):
                raise ValueError("Expecting 7 fields per row for the "
                    "species CSV file, found %d fields." % len(row))

            self.cursor.execute("INSERT INTO species VALUES (?,?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4],row[5])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_plates_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the plates from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.20`.

        Design Part: 1.36
        """
        logging.info("Importing plates data from %s" % setlyze.config.cfg.get('plates-file'))

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
            if len(row) != 10:
                raise ValueError("Expecting 10 fields per row for the "
                    "plates CSV file, found %d fields." % len(row))

            self.cursor.execute("INSERT INTO plates VALUES (?,?,?,?,?,?,?,?,?,?)",
                (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_records_from_csv(self, delimiter=';', quotechar='"'):
        """Insert the records from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.21`.

        Design Part: 1.37
        """
        logging.info("Importing records data from %s" % setlyze.config.cfg.get('records-file'))

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
            if len(row) != 40:
                raise ValueError("Expecting 40 fields per row for the "
                    "plates CSV file, found %d fields." % len(row))

            self.cursor.execute("INSERT INTO records VALUES (%s)" % placeholders,
                (row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],
                row[10],row[11],row[12],row[13],row[14],row[15],row[16],row[17],row[18],row[19],
                row[20],row[21],row[22],row[23],row[24],row[25],row[26],row[27],row[28],row[29],
                row[30],row[31],row[32],row[33],row[34],row[35],row[36],row[37])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_from_xls(self):
        #raise Exception("NOT implemented yet.")

        """Create a new local database and load all SETL data from the
        user selected Excel files into the local database.

        The SETL data is loaded from four separate Excel files:
            * localities_file, containing the SETL locations.
            * species_file, containing the SETL species.
            * records_file, containing the SETL records.
            * plates_file, containing the SETL plates.

        These files must be exported from the MS Access SETL database
        and contain all fields. The Excel files have to be
        delimited by semicolons (;) and double quotes (") as
        the quote character for fields with special characters.

        Design Part: ....
        """
        logging.info("Creating local database from Microsoft Excel spreadsheet files...")

        # If data_source is not set to "xls", the required data
        # files are probably not set by the user yet. ChangeDataSource
        # must be called first.
        if setlyze.config.cfg.get('data-source') != 'xls':
            raise ValueError("Cannot run this function while 'data-source' is "
                "set to '%s'." % setlyze.config.cfg.get('data-source'))

        # First, create a new database file.
        self.create_new_db()

        # Create a connection with the local database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Add some meta-data to a separate table in the local database.
        # Add the data source we can figure out what kind of data is
        # present.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)",
            ( setlyze.config.cfg.get('data-source'), ) )
        # Also insert the data of creation, so we can give the user an
        # indication when this database was created.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # Set the total number of times we're going to update the progress
        # dialog.
        self.pdialog_handler.set_total_steps(4)

        # Insert the data from the xls files into the local database.
        filename = os.path.split(setlyze.config.cfg.get('localities-file'))[1]
        self.pdialog_handler.set_action("Importing %s" % filename)
        try:
            self.insert_localities_from_xls()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading localities data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('plates-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_plates_from_xls()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading plates data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('records-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_records_from_xls()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading records data from %s failed." % filename)
            return

        filename = os.path.split(setlyze.config.cfg.get('species-file'))[1]
        self.pdialog_handler.increase("Importing %s" % filename)
        try:
            self.insert_species_from_xls()
        except:
            # Close the connection with the database.
            self.cursor.close()
            self.connection.close()
            # Create a new database, because not all data could be imported.
            self.create_new_db()
            # Emit the signal that the import failed.
            gobject.idle_add(setlyze.std.sender.emit, 'csv-import-failed',
                "Loading species data from %s failed." % filename)
            return

        # If we are here, the import was successful. Set the progress dialog
        # to 100%.
        self.pdialog_handler.increase("")

        # Close the connection with the database.
        self.cursor.close()
        self.connection.close()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

        return True

    def insert_localities_from_xls(self, delimiter=';', quotechar='"'):		
        """Insert the SETL localities from a CSV file into the local
        database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.18`.

        Design Part: 1.34
        """
        logging.info("Importing localities data from %s" % setlyze.config.cfg.get('localities-file'))

        # Try to open the CSV file.
        try:
            f= xlrd.open_workbook(setlyze.config.cfg.get('localities-file'))
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = f.sheet_by_index(0)


        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            if len(setl_reader.row_values(rownum)) != 5:
                raise ValueError("Expecting 5 fields per row for the "
                    "localities CSV file, found %d fields." % len(setl_reader.row_values(rownum)))

            self.cursor.execute("INSERT INTO localities VALUES (?,?,?,?,?)",
                (setl_reader.row_values(rownum)[0],
                 setl_reader.row_values(rownum)[1],
                 setl_reader.row_values(rownum)[2],
                 setl_reader.row_values(rownum)[3],
                 setl_reader.row_values(rownum)[4])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_plates_from_xls(self, delimiter=';', quotechar='"'):
        """Insert the plates from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.20`.

        Design Part: ....
        """
        logging.info("Importing plates data from %s" % setlyze.config.cfg.get('plates-file'))

        # Try to open the CSV file.
        try:
            f= xlrd.open_workbook(setlyze.config.cfg.get('plates-file'))
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = f.sheet_by_index(0)


        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            if len(setl_reader.row_values(rownum)) != 10:
                raise ValueError("Expecting 10 fields per row for the "
                    "plates CSV file, found %d fields." % len(setl_reader.row_values(rownum)))

            self.cursor.execute("INSERT INTO plates VALUES (?,?,?,?,?,?,?,?,?,?)",
                (setl_reader.row_values(rownum)[0],
                 setl_reader.row_values(rownum)[1],
                 setl_reader.row_values(rownum)[2],
                 setl_reader.row_values(rownum)[3],
                 setl_reader.row_values(rownum)[4],
                 setl_reader.row_values(rownum)[5],
                 setl_reader.row_values(rownum)[6],
                 setl_reader.row_values(rownum)[7],
                 setl_reader.row_values(rownum)[8],
                 setl_reader.row_values(rownum)[9])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_records_from_xls(self, delimiter=';', quotechar='"'):
        """Insert the records from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.21`.

        Design Part: 1.37
        """
        logging.info("Importing records data from %s" % setlyze.config.cfg.get('records-file'))

        # Try to open the CSV file.
        try:
            f= xlrd.open_workbook(setlyze.config.cfg.get('records-file'))
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        placeholders = ','.join('?' * 38)
        for rownum in range(setl_reader.nrows):
            if len(setl_reader.row_values(rownum)) != 40:
                raise ValueError("Expecting 40 fields per row for the "
                    "plates CSV file, found %d fields." % len(setl_reader.row_values(rownum)))

            self.cursor.execute("INSERT INTO records VALUES (%s)" % placeholders,
                (setl_reader.row_values(rownum)[0],
                 setl_reader.row_values(rownum)[1],
                 setl_reader.row_values(rownum)[2],
                 setl_reader.row_values(rownum)[3],
                 setl_reader.row_values(rownum)[4],
                 setl_reader.row_values(rownum)[5],
                 setl_reader.row_values(rownum)[6],
                 setl_reader.row_values(rownum)[7],
                 setl_reader.row_values(rownum)[8],
                 setl_reader.row_values(rownum)[9],
                 setl_reader.row_values(rownum)[10],
                 setl_reader.row_values(rownum)[11],
                 setl_reader.row_values(rownum)[12],
                 setl_reader.row_values(rownum)[13],
                 setl_reader.row_values(rownum)[14],
                 setl_reader.row_values(rownum)[15],
                 setl_reader.row_values(rownum)[16],
                 setl_reader.row_values(rownum)[17],
                 setl_reader.row_values(rownum)[18],
                 setl_reader.row_values(rownum)[19],
                 setl_reader.row_values(rownum)[20],
                 setl_reader.row_values(rownum)[21],
                 setl_reader.row_values(rownum)[22],
                 setl_reader.row_values(rownum)[23],
                 setl_reader.row_values(rownum)[24],
                 setl_reader.row_values(rownum)[25],
                 setl_reader.row_values(rownum)[26],
                 setl_reader.row_values(rownum)[27],
                 setl_reader.row_values(rownum)[28],
                 setl_reader.row_values(rownum)[29],
                 setl_reader.row_values(rownum)[30],
                 setl_reader.row_values(rownum)[31],
                 setl_reader.row_values(rownum)[32],
                 setl_reader.row_values(rownum)[33],
                 setl_reader.row_values(rownum)[34],
                 setl_reader.row_values(rownum)[35],
                 setl_reader.row_values(rownum)[36],
                 setl_reader.row_values(rownum)[37])
                )

        # Commit the database changes.
        self.connection.commit()

    def insert_species_from_xls(self, delimiter=';', quotechar='"'):
        """Insert the species from a CSV file into the local database.

        `delimiter` is a one-character string used to separate fields
        in the CSV file. `quotechar` is a one-character string used to
        quote fields containing special characters in the CSV file.
        The default values for these two arguments are suited for CSV
        files in Excel format.

        For a description of the format for the localities file, refer
        to :ref:`design-part-data-2.19`.

        Design Part: 1.35
        """
        logging.info("Importing species data from %s" % setlyze.config.cfg.get('species-file'))

        # Try to open the CSV file.
        try:
            f= xlrd.open_workbook(setlyze.config.cfg.get('species-file'))
        except IOError, e:
            logging.error(e)
            return False

        # Use Python's CSV module to create a CSV reader.
        setl_reader = f.sheet_by_index(0)

        # Read through every row in the CSV file and insert that row
        # into the local database.
        for rownum in range(setl_reader.nrows):
            if len(setl_reader.row_values(rownum)) not in (6, 7):
                raise ValueError("Expecting 7 fields per row for the "
                    "species CSV file, found %d fields." % len(setl_reader.row_values(rownum)))

            self.cursor.execute("INSERT INTO species VALUES (?,?,?,?,?,?)",
                (setl_reader.row_values(rownum)[0],
                 setl_reader.row_values(rownum)[1],
                 setl_reader.row_values(rownum)[2],
                 setl_reader.row_values(rownum)[3],
                 setl_reader.row_values(rownum)[4],
                 setl_reader.row_values(rownum)[5])
                )

        # Commit the database changes.
        self.connection.commit()

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

        # First, create a new database file.
        self.create_new_db()

        # Create a connection with the local database.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Update progress dialog.
        self.pdialog_handler.increase()

        # Next time we run the tool, we'll know what data is in the
        # database.
        self.cursor.execute( "INSERT INTO info VALUES (null, 'source', ?)", (setlyze.config.cfg.get('data-source'),) )
        self.cursor.execute( "INSERT INTO info VALUES (null, 'date', date('now'))" )

        # TODO: Actually insert data from SETL database.
        logging.info("Loading data from the remote SETL database...")

        # Update progress dialog.
        self.pdialog_handler.increase()

        # Close the connection with the database.
        self.cursor.close()
        self.connection.close()

        logging.info("Local database populated.")
        setlyze.config.cfg.set('has-local-db', True)

    def create_new_db(self):
        """Create a new local database and then calls the methods
        that create the necessary tables.

        This deletes the current local database if present in the user's
        home folder.

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

        # This will automatically create a new database file.
        self.connection = sqlite.connect(self.dbfile)
        self.cursor = self.connection.cursor()

        # Create the tables.
        self.create_table_info()
        self.create_table_localities()
        self.create_table_species()
        self.create_table_plates()
        self.create_table_records()
        self.create_table_species_spots_1()
        self.create_table_species_spots_2()
        self.create_table_spot_distances_observed()
        self.create_table_spot_distances_expected()
        self.create_table_plate_spot_totals()
        self.create_table_plate_area_totals_observed()
        self.create_table_plate_area_totals_expected()

        # Commit the transaction.
        self.connection.commit()

        # Close connection with the local database.
        self.cursor.close()
        self.connection.close()

        # No need to make a new database, as we just created one.
        setlyze.config.cfg.set('make-new-db', False)

    def remove_db_file(self, tries=0):
        """Remove the database file.

        This method does 3 tries if for some reason the database file
        could not be deleted (e.g. the file is in use by a different
        process.
        """
        if tries > 2:
            raise EnvironmentError("I was unable to remove the file %s. "
                "Please make sure it's not in use by a different "
                "process." % self.dbfile)

        try:
            os.remove(self.dbfile)
        except:
            tries += 1
            time.sleep(2)
            self.remove_db_file(tries)

        return True

    def create_table_info(self):
        """Create a table for storing basic information about the
        local database.

        This information includes its creation date and the data source.
        The data source is either the SETL database (MS Access/PostgreSQL)
        or CSV files containing SETL data. A version number for the
        database is also saved. This could be handy in the future,
        for example we can notify the user if the local database is
        too old, followed by creating a new local database.

        Design Part: 1.75
        """
        db_version = 0.1

        self.cursor.execute("CREATE TABLE info (\
            id INTEGER PRIMARY KEY, \
            name VARCHAR, \
            value VARCHAR)"
            )

        self.cursor.execute("INSERT INTO info "
            "VALUES (null, 'version', ?)", [db_version])

    def create_table_localities(self):
        """Create a table for the SETL localities.

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
        """Create a table for the SETL species.

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
            spe_remarks VARCHAR \
        )")

    def create_table_plates(self):
        """Create a table for the SETL plates.

        This table is only filled if the user selected CSV files to
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
        """Create a table for the SETL records.

        This table is only filled if the user selected CSV files to
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

    def create_table_species_spots_1(self):
        """Create a table that will contain the SETL records for the
        first species selection.

        Because the user can select multiple species, the plate IDs in
        column ``rec_pla_id`` don't have to be unique, so we're
        creating a separate column ``id`` as the primary key.

        Design Part: 1.80
        """

        # Design Part: 2.9, 2.9.1, 2.9.2
        self.cursor.execute("CREATE TABLE species_spots_1 (\
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
        """Create a table that will contain the SETL records for the
        second species selection.

        Because the user can select multiple species, the plate IDs in
        column ``rec_pla_id`` don't have to be unique, so we're
        creating a separate column ``id`` as the primary key.

        Design Part: 1.81
        """

        # Design Part: 2.10, 2.10.1, 2.10.2
        self.cursor.execute("CREATE TABLE species_spots_2 (\
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
        """Create a table for the observed spot distances.

        Design Part: 1.83
        """

        # Design Part: 2.12
        self.cursor.execute("CREATE TABLE spot_distances_observed (\
            id INTEGER PRIMARY KEY, \
            rec_pla_id INTEGER, \
            distance REAL \
        )")

    def create_table_spot_distances_expected(self):
        """Create a table for the expected spot distances.

        Design Part: 1.84
        """

        # Design Part: 2.13
        self.cursor.execute("CREATE TABLE spot_distances_expected (\
            id INTEGER PRIMARY KEY, \
            rec_pla_id INTEGER, \
            distance REAL \
        )")

    def create_table_plate_spot_totals(self):
        """Create a table for the total of spots per plate in the
        distance tables.

        Design Part: 1.85
        """

        # Design Part: 2.39
        self.cursor.execute("CREATE TABLE plate_spot_totals (\
            pla_id INTEGER PRIMARY KEY, \
            n_spots_a INTEGER, \
            n_spots_b INTEGER \
        )")

    def create_table_plate_area_totals_observed(self):
        """Create a table for the total of positive spots per plate area per
        plate ID.

        Design Part:
        """

        # Design Part:
        self.cursor.execute("CREATE TABLE plate_area_totals_observed (\
            pla_id INTEGER PRIMARY KEY, \
            area_a INTEGER, \
            area_b INTEGER, \
            area_c INTEGER, \
            area_d INTEGER \
        )")

    def create_table_plate_area_totals_expected(self):
        """Create a table for the total of positive spots per plate area per
        plate ID.

        Design Part:
        """

        # Design Part:
        self.cursor.execute("CREATE TABLE plate_area_totals_expected (\
            pla_id INTEGER PRIMARY KEY, \
            area_a INTEGER, \
            area_b INTEGER, \
            area_c INTEGER, \
            area_d INTEGER \
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

    def get_database_info(self):
        """Return info (creation date, data source) stored in the local
        database file.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

        cursor.execute("SELECT value FROM info WHERE name='source'")
        source = cursor.fetchone()

        cursor.execute("SELECT value FROM info WHERE name='date'")
        date = cursor.fetchone()

        cursor.close()
        connection.close()

        info = {'source': None, 'date': None}
        if source:
            info['source'] = source[0]
        if date:
            info['date'] = date[0]

        return info

    def get_locations(self):
        """Return a list of all locations from the local database.

        Returns a list of tuples ``(loc_id, 'loc_name')``.

        Design Part: 1.95
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()
        cursor.execute("SELECT loc_id, loc_name FROM localities")
        locations = cursor.fetchall()
        cursor.close()
        connection.close()

        return locations

    def make_plates_unique(self, slot):
        """Combine the records with the same plate ID in a spots table.
        The value for `slot` defines which spots table is used.
        The possible values of `slot` are ``0`` for table
        ``species_spots_1`` and ``1`` for ``species_spots_2``.

        We're doing this so we can threat multiple species selected by
        the user as a single species.

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
            combined = setlyze.std.combine_records(rows)

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
        """Remove records that have just one positive spot. Intra-specific
        distance can’t be calculated for those.

        .. deprecated:: 0.1
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
        """Fill the ``plate_spot_totals`` table with the number of
        positive spots for each plate.

        The information is obtained from the tables `spots_table1` and
        `spots_table2` (optional).

        The ``plate_spot_totals`` table is used in several situations:

            * Calculating the expected distances, where the positive spot
              number serves as a template for the random spots generator
              (see :ref:`~setlyze.std.get_random_for_plate`).

            * Significance calculators, where the tests are applied to
              plates with a specific number of positive spots (see
              :ref:`get_distances_matching_spots_total`).

        If just `spots_table1` is provided, only the column ``n_spots_a``
        is filled with positive spot numbers. If both `spots_table1` and
        `spots_table2` are provided, ``n_spots_a`` is filled
        from `spots_table1`, and ``n_spots_b`` filled from `spots_table2`.

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
                plate_id = record[1]

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
                                 (plate_id, spots1, spots2)
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

                # Save the number of positive spots to the
                # plate_spot_totals table.
                cursor2.execute( "INSERT INTO plate_spot_totals "
                                 "VALUES (?,?,null)",
                                 (plate_id, spots)
                                )

        # Commit the transaction.
        connection.commit()

        # Close connection with the local database.
        cursor.close()
        cursor2.close()
        connection.close()

        # Return the number of records that were skipped.
        return skipped

    def get_distances_matching_spots_total(self, distance_table, spots_n):
        """Get the distances from distance table `distance_table` that
        are from plates having `spots_n` positive spot numbers.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns the distances.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

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
        connection.close()

    def get_distances_matching_ratios(self, distance_table, ratios):
        """Get the spot distances from distance table `distance_table` where
        positive spots numbers between species A and B have ratio
        matching the list of ratios `ratios`.

        The ratio A:B is considered the same as B:A.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns the distances.
        """
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

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
        connection.close()

    def get_area_totals(self, plate_area_totals_table, area_group):
        """TODO"""
        connection = sqlite.connect(self.dbfile)
        cursor = connection.cursor()

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

        # Return all matching distances. Two for-loops are created to make
        # this function as fast as possible.
        if len(fields) > 1:
            # More then one total is returned at each iter, so we need to
            # unpack all items per iter and yield those.
            for totals in cursor:
                for total in totals:
                    #if total == 0: continue
                    yield total
        else:
            # One field, so one total is returned at a time (no nested for-loop
            # required here).
            for total in cursor:
                #if total[0] == 0: continue
                yield total[0]

        # Close connection with the local database.
        cursor.close()
        connection.close()

class AccessLocalDB(AccessDBGeneric):
    """Provide standard methods for accessing data in the local
    SQLite database. These methods are only used when the data source
    is set to ``csv-msaccess``.

    Inherits from :class:`AccessDBGeneric` which provides this
    class with methods that are not data source specific.

    Design Part: 1.28
    """

    def __init__(self):
        super(AccessLocalDB, self).__init__()
        self.cursor = None
        self.connection = None

    def get_species(self, loc_slot=0):
        """Return a list of species tuples in the format ``(spe_id,
        'spe_name_venacular', 'spe_name_latin')`` from the local
        database that match the localities selection.

        The values for `loc_slot` are ``0`` for the first localities
        selection and ``1`` for the second localities selection.

        Design Part: 1.96
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
        cursor.execute("SELECT spe_id, spe_name_venacular, spe_name_latin FROM species WHERE spe_id IN (%s)" % spe_ids_str)
        species = cursor.fetchall()

        # Close connection with the local database.
        cursor.close()
        connection.close()

        return species

    def get_record_ids(self, loc_ids, spe_ids):
        """Return a list of record IDs that match the localities IDs
        in the list `loc_ids` and the species IDs in the list `spe_ids`.

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
        """Return all 25 spot booleans for the records with IDs matching
        the list of record IDs `rec_ids`.

        This is a generator, meaning that this method returns an
        iterator. This iterator returns tuples with the 25 spot booleans for
        all matching records.
        """

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

        for record in cursor:
            yield record

        # Close connection with the local database.
        cursor.close()
        connection.close()

    def set_species_spots(self, rec_ids, slot):
        """Create a table in the local database containing the spots
        information for SETL records matching `rec_ids`. Two spots
        tables can be created. The values for `slot` can be ``0`` for table
        ``species_spots_1`` and ``1`` for ``species_spots_2``.

        Each record in the spots table consists of the plate ID followed
        by the 25 spot booleans.

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
    """Provide standard methods for accessing data in the remote
    PostgreSQL SETL database. These methods are only used when the data
    source is set to ``setl-database``.

    Inherits from :class:`AccessDBGeneric` which provides this
    class with methods that are not data source specific.

    Design Part: 1.29
    """

    def __init__(self):
        super(AccessRemoteDB, self).__init__()

