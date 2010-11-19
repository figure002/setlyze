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

# Standard library imports
import sys
import os
import logging
import getopt
from sqlite3 import dbapi2 as sqlite

try:
    import pkg_resources
except ImportError:
    sys.exit("SETLyze requires setuptools for Python 2.6. "
        "Please install this module and try again.")
try:
    import pygtk
except ImportError:
    sys.exit("SETLyze requires PyGTK for Python 2.6. "
        "Please install this module and try again.")
pygtk.require('2.0')
import gtk
try:
    import gobject
except ImportError:
    sys.exit("SETLyze requires PyGObject for Python 2.6. "
        "Please install this module and try again.")

import setlyze.config
import setlyze.database
import setlyze.analysis.spot_preference
import setlyze.analysis.attraction_intra
import setlyze.analysis.attraction_inter
import setlyze.analysis.relations

gobject.threads_init()

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__credits__ = ["Jonathan den Boer",
    "Serrano Pereira <serrano.pereira@gmail.com>"]
__license__ = "GPL3"
__version__ = "0.1"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

class SelectAnalysis(object):
    """
    Display a window that allows the user to select an analysis.

    Design Part: 3.0
    """

    def __init__(self):
        # Create a GTK window.
        self.w = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.w.set_title("Welcome to SETLyze")
        self.w.set_size_request(-1, -1)
        self.w.set_border_width(10)
        self.w.set_position(gtk.WIN_POS_CENTER)
        self.w.set_resizable(False)

        self.selected_analysis = None

        # Handle window signals.
        self.w.connect('destroy', gtk.main_quit)

        # Handle application signals.
        self.handler1 = setlyze.std.sender.connect('beginning-analysis', self.on_analysis_started)
        self.handler2 = setlyze.std.sender.connect('analysis-closed', self.on_analysis_closed)
        self.handler3 = setlyze.std.sender.connect('progress-dialog-closed', self.on_continue)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.w.show_all()

    def create_layout(self):
        """Construct the layout for the SelectAnalysis window."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=5, columns=2, homogeneous=False)
        table.set_col_spacings(5)
        table.set_row_spacings(5)

        # Create a label.
        label_welcome = gtk.Label("Please select the desired SETL analysis:")
        label_welcome.set_line_wrap(True)
        label_welcome.set_justify(gtk.JUSTIFY_FILL)
        label_welcome.set_alignment(xalign=0, yalign=0)
        # Add the label to the table.
        table.attach(label_welcome, left_attach=0, right_attach=1,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=5)

        # Create a vertical box to place the widgets in.
        vbox = gtk.VBox(homogeneous=True, spacing=5)

        # Create radio buttons.
        self.radio_ana1 = gtk.RadioButton(None, setlyze.locale.text('analysis1'))
        self.radio_ana1.set_tooltip_text(setlyze.locale.text('analysis1-descr'))
        self.radio_ana1.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana1)

        self.radio_ana2_1 = gtk.RadioButton(self.radio_ana1, setlyze.locale.text('analysis2.1'))
        self.radio_ana2_1.set_tooltip_text(setlyze.locale.text('analysis2.1-descr'))
        self.radio_ana2_1.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana2_1)

        self.radio_ana2_2 = gtk.RadioButton(self.radio_ana1, setlyze.locale.text('analysis2.2'))
        self.radio_ana2_2.set_tooltip_text(setlyze.locale.text('analysis2.2-descr'))
        self.radio_ana2_2.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana2_2)

        self.radio_ana3 = gtk.RadioButton(self.radio_ana1, setlyze.locale.text('analysis3'))
        self.radio_ana3.set_tooltip_text(setlyze.locale.text('analysis3-descr'))
        self.radio_ana3.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana3)

        # Add the alignment widget to the table.
        table.attach(vbox, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Load an image for the logo.
        setl_logo = gtk.Image()
        setl_logo.set_from_file(pkg_resources.resource_filename(__name__, 'setlyze/images/setl-logo.png'))
        setl_logo_align = gtk.Alignment(xalign=1, yalign=0, xscale=0, yscale=1)
        setl_logo_align.add(setl_logo)
        # Add the logo to the table.
        table.attach(setl_logo_align, left_attach=1, right_attach=2,
            top_attach=0, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.FILL, xpadding=0, ypadding=0)

        # Create a description label.
        self.label_descr = gtk.Label(setlyze.locale.text('analysis1-descr'))
        self.label_descr.set_width_chars(40)
        self.label_descr.set_line_wrap(True)
        self.label_descr.set_justify(gtk.JUSTIFY_FILL)
        self.label_descr.set_alignment(xalign=0, yalign=0)
        self.label_descr.set_padding(2, 2)

        # Create a frame for the analysis description.
        self.frame_descr = gtk.Frame()
        self.frame_descr.set_size_request(-1, -1)
        self.frame_descr.add(self.label_descr)
        self.on_toggled()
        # Add the frame to the table.
        table.attach(self.frame_descr, left_attach=0, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.FILL, xpadding=0, ypadding=0)

        # Put a separator above the buttons.
        separator = gtk.HSeparator()
        table.attach(separator, left_attach=0, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create an about button.
        button_about = gtk.Button("About")
        button_about.set_size_request(70, -1)
        button_about.connect("clicked", self.on_about)
        # Align the about button to the left.
        about_align = gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        about_align.add(button_about)
        # Add the about button to the table.
        table.attach(child=about_align, left_attach=0, right_attach=1,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Continue button.
        button_ok = gtk.Button("Continue")
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_continue)

        # Quit button.
        button_quit = gtk.Button("Quit")
        button_quit.set_size_request(70, -1)
        button_quit.connect("clicked", self.on_quit)

        # Put the buttons in a horizontal box.
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(button_quit)
        button_box.add(button_ok)

        # Align the button box to the right.
        buttons_align = gtk.Alignment(xalign=1.0, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the aligned button box to the table.
        table.attach(child=buttons_align, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the alignment widget to the main window.
        self.w.add(table)

    def on_toggled(self, radiobutton=None):
        """Update the description frame."""
        if self.radio_ana1.get_active():
            self.frame_descr.set_label("Analysis 1")
            self.label_descr.set_text(setlyze.locale.text('analysis1-descr'))
        elif self.radio_ana2_1.get_active():
            self.frame_descr.set_label("Analysis 2.1")
            self.label_descr.set_text(setlyze.locale.text('analysis2.1-descr'))
        elif self.radio_ana2_2.get_active():
            self.frame_descr.set_label("Analysis 2.2")
            self.label_descr.set_text(setlyze.locale.text('analysis2.2-descr'))
        elif self.radio_ana3.get_active():
            self.frame_descr.set_label("Analysis 3")
            self.label_descr.set_text(setlyze.locale.text('analysis3-descr'))

    def destroy_handler_connections(self):
        """
        Disconnect all signal connections with signal handlers created
        by this object.
        """

        # This handler is only needed once. We don't want
        # self.on_continue to be called each time a progress dialog is
        # closed.
        if self.handler3:
            setlyze.std.sender.disconnect(self.handler3)
            self.handler3 = None

    def on_analysis_started(self, sender):
        # Some handler are only needed once. Block subsequent execution
        # of these handler, as the signals will be emitted again from
        # different parts.
        self.destroy_handler_connections()

        # Hide this window when an analysis is running.
        self.w.hide()

    def on_analysis_closed(self, sender):
        # Hide this window when an analysis has closed.
        self.w.show()

    def on_continue(self, widget=None, data=None):
        """Begin with the selected analysis."""

        # Check if a local database is set.
        if not setlyze.config.cfg.get('has-local-db'):
            # If not, create one.
            self.make_local_database()

            # The code below isn't supposed to continue while a local
            # database is being created in the background. The code
            # below is only supposed to run AFTER the local database was
            # created.
            # Once the database was created, a signal will be sent, and
            # self.on_continue will be called again, running the code
            # below. Hence the 'return'.
            return

        # Then begin with the selected analysis.
        if self.radio_ana1.get_active():
            setlyze.analysis.spot_preference.Begin()

        elif self.radio_ana2_1.get_active():
            setlyze.analysis.attraction_intra.Begin()

        elif self.radio_ana2_2.get_active():
            setlyze.analysis.attraction_inter.Begin()

        elif self.radio_ana3.get_active():
            setlyze.analysis.relations.Begin()

    def on_quit(self, widget, data=None):
        """Close the application."""
        gtk.main_quit()

    def on_about(self, widget, data=None):
        license = ("This program is free software: you can redistribute it and/or modify\n"
            "it under the terms of the GNU General Public License as published by\n"
            "the Free Software Foundation, either version 3 of the License, or\n"
            "(at your option) any later version.\n\n"

            "This program is distributed in the hope that it will be useful,\n"
            "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
            "GNU General Public License for more details.\n\n"

            "You should have received a copy of the GNU General Public License\n"
            "along with this program.  If not, see http://www.gnu.org/licenses/")

        logo_path = pkg_resources.resource_filename(__name__,
            'setlyze/images/setl-logo.png')
        logo = gtk.gdk.pixbuf_new_from_file(logo_path)

        about = gtk.AboutDialog()
        about.set_program_name("SETLyze")
        about.set_version(__version__)
        about.set_copyright("Copyright 2010, GiMaRIS")
        about.set_authors(["Project Leader/Contact Person:\n"
            "\tArjan Gittenberger <gittenberger@gimaris.com>",
            "Application Developers:\n"
            "\tJonathan den Boer",
            "\tSerrano Pereira <serrano.pereira@gmail.com>"])
        about.set_artists(["Serrano Pereira <serrano.pereira@gmail.com>"])
        about.set_comments("A tool for analyzing SETL data.")
        about.set_license(license)
        about.set_website("http://www.gimaris.com/")
        about.set_logo(logo)
        about.run()
        about.destroy()

    def make_local_database(self):
        """
        Prepare a local database. If there's already a local database
        on the user's computer, ask the user if he/she wants to use that
        database.
        """
        dbfile = setlyze.config.cfg.get('db-file')

        # Check if there already is a local database file.
        if os.path.isfile(dbfile):
            # If there is, ask the user if he/she/it want's to use
            # the current local database.

            connection = sqlite.connect(dbfile)
            cursor = connection.cursor()

            # Get the data source.
            cursor.execute("SELECT value FROM info WHERE name='source'")
            source = cursor.fetchone()

            # Get the creation date.
            cursor.execute("SELECT value FROM info WHERE name='date'")
            date = cursor.fetchone()

            # Check if we got any results.
            if not source or not date:
                # No row was returned, just create a new local
                # database.
                self.on_make_local_db()
                return

            cursor.close()
            connection.close()

            # The first item in the list is the value.
            source = source[0]
            date = date[0]

            # Construct a message for the user.
            if source == "setl-database":
                source_str = "the SETL database"
            elif source == "csv-msaccess":
                source_str = "MS Access exported CSV files"
            else:
                logging.error("The saved local database contains an unknown data source.")
                sys.exit(1)

            message = setlyze.locale.text('use-saved-data', date, source_str)

            # Show a dialog with the message.
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
                message_format="Use saved data?")
            dialog.format_secondary_text(message)
            response = dialog.run()

            # Check the user's response.
            if response == gtk.RESPONSE_YES:
                logging.info("Using the local database from the last run.")

                # Prevent a new database from being created.
                setlyze.config.cfg.set('data-source', source)
                setlyze.config.cfg.set('make-new-db', False)
                setlyze.config.cfg.set('has-local-db', True)

                # Destroy the dialog.
                dialog.destroy()

                # Try again...
                self.on_continue()
            else:
                # User pressed No

                # Destroy the dialog.
                dialog.destroy()

                # Create a new database.
                self.on_make_local_db()
        else:
            # No database file was found. Create a new local database file.
            self.on_make_local_db()

    def on_make_local_db(self):
        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading SETL Data",
            description="Please wait while the data from the SETL database is being loaded...")
        setlyze.config.cfg.set('progress-dialog', pd)

        # Make the local database.
        t = setlyze.database.MakeLocalDB()
        t.start()

def adapt_str(string):
    """Convert the custom Python type into one of SQLite's supported types."""
    return string.decode("utf-8")

def main():
    # Registers adapt_str to convert the custom Python type into one of
    # SQLite's supported types. This adds support for Unicode strings.
    sqlite.register_adapter(str, adapt_str)

    # Initialize the logging module.
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')

    # Create a log message.
    logging.info("SETLyze %s started." % __version__)

    # Display the main window.
    SelectAnalysis()

    # Start the GTK main loop, which continuously checks for newly
    # generated events.
    gtk.main()

    # Zero is considered "successful termination".
    sys.exit(0)

if __name__ == "__main__":
    main()
