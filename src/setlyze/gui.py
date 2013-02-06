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

"""This module provides the graphical user interfaces ("GUIs") for SETLyze.

We use GTK+ for the GUI creation. GTK+ is a highly usable, feature rich
toolkit for creating graphical user interfaces which boasts cross
platform compatibility and an easy to use API.

GTK+ is an event driven toolkit, which means it will sleep in gtk.main()
until an event occurs and control is passed to the appropriate function.
To understand the code, it's important that you gain basic
understanding of signals and callbacks, as these are used throughout
the application (not just this module). The following tutorial is a good
place to start: `Theory of Signals and Callbacks
<http://www.pygtk.org/pygtk2tutorial/sec-TheoryOfSignalsAndCallbacks.html>`_

Each class in this module represents a graphical dialog or window.
Displaying one of these dialogs is as easy as instantiating the class.
You can easily test this from the interactive Python shell:

    >>> import setlyze.gui
    >>> g = setlyze.gui.SelectLocations()

The above would display a nice localities selection dialog. You could
then do the following to get a list of the selected locations.

    >>> import setlyze.config
    >>> setlyze.config.cfg.get('locations-selection')
"""

import sys
import os
import logging
import webbrowser

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import pkg_resources

import setlyze.locale
import setlyze.config
import setlyze.database
import setlyze.report
from setlyze.std import module_path,make_remarks

__author__ = "Serrano Pereira, Adam van Adrichem, Fedde Schaeffer"
__copyright__ = "Copyright 2010, 2011, GiMaRIS"
__license__ = "GPL3"
__version__ = "0.2"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2013/02/02"

def on_help(button, section):
    """Display the help contents for `section` in the system's default
    application for displaying HTML files (usually a web browser).
    """

    # Construct the path to the help file.
    if setlyze.std.we_are_frozen():
        path = os.path.join(setlyze.std.module_path(),
            'docs/html/user_manual.html#'+section)
    else:
        path = pkg_resources.resource_filename('setlyze',
            '/docs/html/user_manual.html#'+section)

    # Turn the path into an URL.
    if path.startswith('/'):
        url = 'file://'+path
    else:
        url = 'file:///'+path

    # WORKAROUND:
    # On Windows, the section part of the URL (the '#...' part)
    # is stripped off. This doesn't happen if 'file:///' is left out.
    # This however always launches IE instead of the default browser.
    if os.name == 'nt':
        url = path

    # Open the URL in the system's default web browser.
    webbrowser.open(url)

def on_quit(button, data=None):
    """Quit the application."""
    dialog = gtk.MessageDialog(parent=None, flags=0,
        type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
            message_format="Are you sure you want to quit SETLyze?")
    dialog.set_position(gtk.WIN_POS_CENTER)

    response = dialog.run()
    if response == gtk.RESPONSE_YES:
        dialog.destroy()
        gtk.main_quit()
    else:
        dialog.destroy()

    # Return True to stop other handlers from being invoked for the
    # 'delete-event' signal. This prevents the GTK window that calles
    # this function from closing anyway.
    return True

def on_not_implemented():
    dialog = gtk.MessageDialog(parent=None, flags=0,
        type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
            message_format="Not yet implemented")
    dialog.format_secondary_text("Sorry, the feature you're trying to "
        "access is not implemented yet. It will be implemented in the next "
        "version of SETLyze.")
    dialog.set_position(gtk.WIN_POS_CENTER)
    dialog.run()
    dialog.destroy()

def markup_header(text):
    """Apply Pango markup to `text` to make it look like a header."""
    text = "<span size='large' weight='bold'>%s</span>" % (text)
    return text


class SelectAnalysis(gtk.Window):
    """Display a window that allows the user to select an analysis.

    Design Part: 1.86
    """

    def __init__(self):
        super(SelectAnalysis, self).__init__()

        self.set_title("Welcome to SETLyze")
        self.set_size_request(-1, -1)
        self.set_border_width(10)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_resizable(False)

        # Handle window signals.
        self.connect('destroy', gtk.main_quit)

        # Handle application signals.
        self.signal_handlers = {
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_analysis_started),
            'analysis-closed': setlyze.std.sender.connect('analysis-closed', self.on_analysis_closed),
            'local-db-created': setlyze.std.sender.connect('local-db-created', self.on_continue),
        }

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def unset_signal_handlers(self):
        """Disconnect all signal connections with signal handlers created
        by this object.
        """

        # This handler is only needed once. We don't want
        # self.on_continue to be called each time the local database
        # is recreated.
        if self.signal_handlers['local-db-created']:
            setlyze.std.sender.disconnect(self.signal_handlers['local-db-created'])
            self.signal_handlers['local-db-created'] = None

    def create_layout(self):
        """Construct the layout."""

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
        self.radio_ana1 = gtk.RadioButton(None,
            setlyze.locale.text('analysis1'))
        self.radio_ana1.set_tooltip_text(setlyze.locale.text('analysis1-descr'))
        self.radio_ana1.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana1)

        self.radio_ana2_1 = gtk.RadioButton(self.radio_ana1,
            setlyze.locale.text('analysis2'))
        self.radio_ana2_1.set_tooltip_text(setlyze.locale.text('analysis2-descr'))
        self.radio_ana2_1.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana2_1)

        self.radio_ana2_2 = gtk.RadioButton(self.radio_ana1,
            setlyze.locale.text('analysis3'))
        self.radio_ana2_2.set_tooltip_text(setlyze.locale.text('analysis3-descr'))
        self.radio_ana2_2.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana2_2)

        self.radio_ana3 = gtk.RadioButton(self.radio_ana1,
            setlyze.locale.text('analysis4'))
        self.radio_ana3.set_tooltip_text(setlyze.locale.text('analysis4-descr'))
        self.radio_ana3.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana3)

        self.radio_ana_batch = gtk.RadioButton(self.radio_ana1,
            setlyze.locale.text('analysis-batch'))
        self.radio_ana_batch.set_tooltip_text(setlyze.locale.text('analysis-batch-descr'))
        self.radio_ana_batch.connect('clicked', self.on_toggled)
        vbox.pack_start(self.radio_ana_batch)

        # Add the alignment widget to the table.
        table.attach(vbox, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Load an image for the logo.
        setl_logo = gtk.Image()
        if setlyze.std.we_are_frozen():
            image_path = os.path.join(setlyze.std.module_path(),
                'images/setlyze-logo.png')
        else:
            image_path = pkg_resources.resource_filename('setlyze',
                'images/setlyze-logo.png')
        setl_logo.set_from_file(image_path)
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
        button_about = gtk.Button(stock=gtk.STOCK_ABOUT)
        button_about.connect("clicked", self.on_about)

        # Create a settings button.
        button_prefs = gtk.Button(stock=gtk.STOCK_PREFERENCES)
        button_prefs.connect("clicked", self.on_preferences)

        # Put the buttons in a horizontal button box.
        button_box_l = gtk.HButtonBox()
        button_box_l.set_layout(gtk.BUTTONBOX_START)
        button_box_l.set_spacing(5)
        button_box_l.pack_start(button_about, expand=True, fill=True, padding=0)
        button_box_l.pack_start(button_prefs, expand=True, fill=True, padding=0)

        # Add the about button to the table.
        table.attach(button_box_l, left_attach=0, right_attach=1,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Continue button.
        button_ok = gtk.Button(stock=gtk.STOCK_OK)
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_continue)

        # Quit button.
        button_quit = gtk.Button(stock=gtk.STOCK_QUIT)
        button_quit.set_size_request(70, -1)
        button_quit.connect("clicked", self.on_quit)

        # Put the buttons in a horizontal box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_quit, expand=True, fill=True, padding=0)
        button_box_r.pack_start(button_ok, expand=True, fill=True, padding=0)

        # Add the aligned button box to the table.
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the alignment widget to the main window.
        self.add(table)

    def on_toggled(self, radiobutton=None):
        """Update the description frame."""
        if self.radio_ana1.get_active():
            self.frame_descr.set_label("Spot preference")
            self.label_descr.set_text(setlyze.locale.text('analysis1-descr'))
        elif self.radio_ana2_1.get_active():
            self.frame_descr.set_label("Attraction within species")
            self.label_descr.set_text(setlyze.locale.text('analysis2-descr'))
        elif self.radio_ana2_2.get_active():
            self.frame_descr.set_label("Attraction within species")
            self.label_descr.set_text(setlyze.locale.text('analysis3-descr'))
        elif self.radio_ana3.get_active():
            self.frame_descr.set_label("Attraction between species")
            self.label_descr.set_text(setlyze.locale.text('analysis4-descr'))
        elif self.radio_ana_batch.get_active():
            self.frame_descr.set_label("Batch mode")
            self.label_descr.set_text(setlyze.locale.text('analysis-batch-descr'))

    def on_analysis_started(self, sender):
        """Destroy this object's signal handlers and hide the dialog."""

        # Some handler are only needed once. Block subsequent execution
        # of these handler, as the signals will be emitted again from
        # different parts.
        self.unset_signal_handlers()

        # Hide this window when an analysis is running.
        self.hide()

    def on_analysis_closed(self, sender):
        """Show the dialog."""
        self.show()

    def on_continue(self, widget=None, data=None):
        """Check if a local database is set. If not, create one if necessary
        and set the database. Once a database has been set, begin with the
        selected analysis.
        """

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
            return False

        # Then begin with the selected analysis.
        if self.radio_ana1.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'spot_preference')

        elif self.radio_ana2_1.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'attraction_intra')

        elif self.radio_ana2_2.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'attraction_inter')

        elif self.radio_ana3.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'relations')

        elif self.radio_ana_batch.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'batch')

        return False

    def on_quit(self, widget, data=None):
        """Close the application."""
        gtk.main_quit()

    def on_preferences(self, widget, data=None):
        Preferences()

    def on_about(self, widget, data=None):
        """Display SETLyze's about dialog."""
        About()

    def make_local_database(self):
        """Set a local database. If there's already a local database file
        on the user's computer, ask the user if he/she wants to use that
        database. If Yes is answered, that local database file
        will be set as the data source. If No is answered, a
        new local database is created and filled with data from the remote
        SETL database (that last part is not implemented yet).
        """
        dbfile = setlyze.config.cfg.get('db-file')

        # Check if there already is a local database file.
        if os.path.isfile(dbfile):
            # If there is, ask the user if he/she/it want's to use
            # the current local database.

            db = setlyze.database.get_database_accessor()
            db_info = db.get_database_info()

            # Check if we got any results.
            if not db_info['source'] or not db_info['date']:
                # No row was returned, just create a new local database.
                self.on_make_local_db()
                return

            # The first item in the list is the value.
            source = db_info['source']
            date = db_info['date']

            # Construct a message for the user.
            if source == "setl-database":
                source_str = "the SETL database"
            elif source == "csv-msaccess":
                source_str = "MS Access exported CSV files"
            elif source == "xls":
                source_str = "Microsoft Excel spreadsheet files"
            else:
                raise ValueError("Unknown data source '%s'." % source)

            message = setlyze.locale.text('use-saved-data', date, source_str)

            # Show a dialog with the message.
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
                message_format="Use saved data?")
            dialog.format_secondary_text(message)
            dialog.set_position(gtk.WIN_POS_CENTER)
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
        """Make a new local database."""

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading SETL Data",
            description="Please wait while the data from the SETL database is being loaded...")
        setlyze.config.cfg.set('progress-dialog', pd)

        # Make the local database.
        t = setlyze.database.MakeLocalDB()
        t.start()

class SelectBatchAnalysis(object):
    """Display a window that allows the user to select an analysis for batch mode."""

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/window_select_analysis.glade'))

        # Get some GTK objects.
        self.window = self.builder.get_object('window_select_analysis')
        self.radio_ana_spot_pref = self.builder.get_object('radio_ana_spot_pref')
        self.radio_ana_attraction_intra = self.builder.get_object('radio_ana_attraction_intra')
        self.radio_ana_attraction_inter = self.builder.get_object('radio_ana_attraction_inter')
        self.radio_ana_relation = self.builder.get_object('radio_ana_relation')
        self.frame_descr = self.builder.get_object('frame_descr')
        self.label_descr = self.builder.get_object('label_descr')

        # Handle window signals.
        self.window.connect('delete-event', on_quit)

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Updated the analysis description.
        self.on_toggled()

        # Handle application signals.
        self.signal_handlers = {
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.close),
        }

        # Display all widgets.
        self.window.show_all()

    def unset_signal_handlers(self):
        """Disconnect all signal connections with signal handlers
        created by this analysis.
        """
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def on_toggled(self, radiobutton=None):
        """Update the description frame."""
        if self.radio_ana_spot_pref.get_active():
            self.frame_descr.set_label("Spot preference")
            self.label_descr.set_text(setlyze.locale.text('analysis1-descr'))

        elif self.radio_ana_attraction_intra.get_active():
            self.frame_descr.set_label("Attraction within species")
            self.label_descr.set_text(setlyze.locale.text('analysis2-descr'))

        elif self.radio_ana_attraction_inter.get_active():
            self.frame_descr.set_label("Attraction between species")
            self.label_descr.set_text(setlyze.locale.text('analysis3-descr'))

        elif self.radio_ana_relation.get_active():
            self.frame_descr.set_label("Relation between species")
            self.label_descr.set_text(setlyze.locale.text('analysis4-descr'))

    def on_ok(self, widget=None, data=None):
        """Send the `on-start-analysis` signal with the selected analysis as
        signal attribute.
        """
        if self.radio_ana_spot_pref.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'spot_preference')

        elif self.radio_ana_attraction_intra.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'attraction_intra')

        elif self.radio_ana_attraction_inter.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'attraction_inter')

        elif self.radio_ana_relation.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'relations')

    def on_back(self, widget, data=None):
        """Go back to the main window."""

        # Close the window.
        self.close()

        # Emit the signal that the Back button was pressed.
        setlyze.std.sender.emit('select-batch-analysis-window-back')

        # Prevent default action of the close button.
        return False

    def close(self, widget=None, data=None):
        """Close the window and unset any signal handlers."""
        self.unset_signal_handlers()
        self.window.destroy()

class SelectionWindow(gtk.Window):
    """Super class for :class:`SelectLocations` and :class:`SelectSpecies`."""

    def __init__(self, title, description, width, slot):
        super(SelectionWindow, self).__init__()

        self.header = title
        self.description = description
        self.width = width
        self.selection = []
        self.set_save_slot(slot)

        self.set_title(title)
        self.set_size_request(self.width, 400)
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', on_quit)

        # Handle application signals.
        self.signal_handlers = {
            'local-db-created': setlyze.std.sender.connect('local-db-created', self.update_tree)
        }

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def create_layout(self):
        """Construct the layout for the selection dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=3, columns=2, homogeneous=False)
        table.set_col_spacings(0)
        table.set_row_spacings(5)

        # Create a vertical box to place the widgets in.
        vbox = gtk.VBox(homogeneous=False, spacing=5)

        # Create a toolbar.
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        toolbar.set_tooltips(True)

        # Create buttons for the toolbar.
        button_home = gtk.ToolButton(gtk.STOCK_HOME)
        sep = gtk.SeparatorToolItem()
        button_help = gtk.ToolButton(gtk.STOCK_HELP)

        # Add the buttons to the toolbar.
        toolbar.insert(button_home, 0)
        toolbar.insert(sep, 1)
        toolbar.insert(button_help, 2)

        # Handle button signals.
        button_home.connect("clicked", self.on_close_dialog)
        if isinstance(self, SelectLocations):
            button_help.connect("clicked", on_help, 'locations-selection-dialog')
        elif isinstance(self, SelectSpecies):
            button_help.connect("clicked", on_help, 'species-selection-dialog')

        # Add the toolbar to the vertical box.
        table.attach(toolbar, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a dialog header.
        self.header = gtk.Label()
        self.header.set_alignment(xalign=0, yalign=0)
        self.header.set_line_wrap(True)
        self.header.set_justify(gtk.JUSTIFY_FILL)
        # Add the label to the vertcal box.
        vbox.pack_start(self.header, expand=False, fill=True, padding=0)
        # Set the header text from the title.
        self.set_header(self.get_title())

        # Create a label.
        self.label_descr = gtk.Label(self.description)
        self.label_descr.set_alignment(xalign=0, yalign=0)
        self.label_descr.set_line_wrap(True)
        self.label_descr.set_justify(gtk.JUSTIFY_FILL)
        # Add the label to the vertcal box.
        vbox.pack_start(self.label_descr, expand=False, fill=True, padding=0)

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # Add the ScrolledWindow to the vertcal box.
        vbox.pack_start(scrolled_window, expand=True, fill=True, padding=0)

        # Create a TreeView.
        self.treeview = gtk.TreeView()
        # Make it so multiple items can be selected.
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        # Save selection on each TreeView selection change.
        self.treeview.get_selection().connect('changed', self.on_changed)

        # Create a model for the TreeView.
        self.update_tree()

        # Create the columns for the TreeView.
        self.create_columns(self.treeview)

        # Add the TreeView to the scrolled window.
        scrolled_window.add(self.treeview)

        # Add the vertical box to the table.
        table.attach(child=vbox, left_attach=0, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.FILL|gtk.EXPAND, xpadding=10, ypadding=0)

        # User Data File button
        self.button_chg_source = gtk.Button(" Change _Data Source ")
        self.button_chg_source.set_size_request(-1, -1)
        self.button_chg_source.connect("clicked", self.on_change_data_source)

        # But the button in a horizontal button box.
        button_box_l = gtk.HButtonBox()
        button_box_l.set_layout(gtk.BUTTONBOX_START)
        button_box_l.pack_start(self.button_chg_source, expand=True, fill=True,
            padding=0)

        # Add the button box to the table.
        table.attach(button_box_l, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=0)

        # Continue button
        button_continue = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        button_continue.set_size_request(-1, -1)
        button_continue.connect("clicked", self.on_continue)
        button_continue.set_label("_Continue")

        # Back button
        button_back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        button_back.set_size_request(-1, -1)
        button_back.connect("clicked", self.on_back)

        # But the button in a horizontal button box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_back, expand=True, fill=True, padding=0)
        button_box_r.pack_start(button_continue, expand=True, fill=True,
            padding=0)

        # Add the aligned button box to the table.
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=5)

        # Add the table to the main window.
        self.add(table)

    def unset_signal_handlers(self):
        """Disconnect all signal handlers created by this class."""
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def set_header(self, header):
        """Set the header text to `header`."""
        self.header.set_markup(markup_header(header))

    def set_description(self, description):
        """Set the description text to `description`."""
        self.label_descr.set_text(description)

    def set_save_slot(self, slot):
        """Set the localities/species selection save slot to `slot`.

        The selection variable has two slots available for saving
        selections (in analysis 3, two selections need to be saved,
        hence two slots were created).

        The possible values of `slot` are ``0`` for the first selection,
        and ``1`` for the second selection.
        """
        if slot not in (0,1):
            raise ValueError("Wrong value for save slot. Slot can be either 0 or 1.")
        self.save_slot = slot

    def on_continue(self, button):
        """Before saving the localities/species selection, check if
        anything was selected. If not, display a message dialog. If yes,
        call method self.save_selection to save the selection and then
        close the selection dialog.

        Design Part: 1.44
        """

        # Check if something was selected. If not, display a dialog.
        if len(self.selection) == 0:
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="No items selected")
            dialog.format_secondary_text("No items were selected. Please "
                "select at least one item from the list.\n\n"
                "Tip: Hold Ctrl or Shift to select multiple items. To "
                "select all items, press Ctrl+A.")
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return

        # Save the selection. This method is present in one of the sub
        # classes.
        self.save_selection()

        # Destroy the handlers.
        self.unset_signal_handlers()

        # Then close this window.
        self.destroy()

    def on_changed(self, treeselection):
        """Save the locations selection to a temporary variable.

        This method is called whenever the selection changes.
        """
        (model, rows) = treeselection.get_selected_rows()
        self.selection = []
        for row in rows:
            iter = model.get_iter(row)
            # We use column=0, because the first column in the
            # TreeModels contain the ID, which we'll need for the SQL
            # queries.
            self.selection.append(model.get_value(iter, column=0))

    def update_tree(self, widget=None):
        """Load the localities/species data from the local database into
        the tree view.

        This function should be called whenever the localities/species
        data is updated. For example after new localities/species data
        was imported into the local database. This function is also
        called when the selection dialog is created.

        Design Part: 1.39
        """

        # Create a model based on the new locations.
        self.create_model()

        # Apply the new model to the TreeView.
        self.treeview.set_model(self.model)

    def on_close_dialog(self, widget=None, data=None):
        """Close the dialog and send the ``selection-dialog-closed``
        signal.

        This method should is called when the user pressed the X (close)
        button of the selection dialog. The signal can then be handled
        in the analysis class.
        """
        self.destroy()

        # Destroy the handlers.
        self.unset_signal_handlers()

        # Emit the signal that a selection dialog was closed.
        setlyze.std.sender.emit('selection-dialog-closed')

    def on_change_data_source(self, button):
        """Display the ChangeDataSource dialog.

        Design Part: 1.11
        """
        ChangeDataSource()

class SelectLocations(SelectionWindow):
    """Display a selection dialog that allows the user to make a
    selection from the SETL locations in the local database.

    Design Part: 1.87
    """

    def __init__(self, title="Locations Selection",
            description="Select the locations:", width=-1, slot=0):
        super(SelectLocations, self).__init__(title, description, width, slot)

        self.info_key = 'info-loc-selection'

    def on_back(self, button):
        """Destroy the selection dialog and send the
        ``locations-dialog-back`` signal.

        The ``locations-dialog-back`` signal is sent with the save slot
        as an attribute. The save slot can have a value of ``0`` for the
        first selection and ``1`` for the second selection.

        This function is called when the user presses the Back button in
        a location selection window.

        Design Part: 1.45
        """

        # Close the dialog.
        self.destroy()

        # Destroy the handlers.
        self.unset_signal_handlers()

        # Emit the signal that the Back button was pressed.
        setlyze.std.sender.emit('locations-dialog-back', self.save_slot)

    def save_selection(self):
        """Save the locations selection and send the
        ``locations-selection-saved`` signal.

        The ``locations-selection-saved`` signal is sent with the save slot
        as an attribute. The save slot can have a value of ``0`` for the
        first selection and ``1`` for the second selection.

        Design Part: 1.7
        """
        setlyze.config.cfg.set('locations-selection', self.selection,
                slot=self.save_slot)

        # Make log message.
        selection = [setlyze.config.cfg.get('locations-selection', slot=0),
            setlyze.config.cfg.get('locations-selection', slot=1)]
        logging.info("\tLocations selection set to: %s" % selection)

        # Emit the signal the selection was saved.
        setlyze.std.sender.emit('locations-selection-saved', self.save_slot)

    def create_model(self):
        """Create a model for the tree view from the location IDs and
        names.

        Design Part: 1.42
        """

        # Create an object for accessing the database.
        db = setlyze.database.get_database_accessor()

        # Create the model.
        self.model = gtk.ListStore(gobject.TYPE_INT,
                                   gobject.TYPE_STRING)
        for item in db.get_locations():
            self.model.append([item[0], item[1]])

        # Create a sorted version of the model. Then sort the locations
        # ascending.
        self.model = gtk.TreeModelSort(self.model)
        self.model.set_sort_column_id(1, gtk.SORT_ASCENDING)

    def create_columns(self, treeview):
        """Create the columns for the tree view."""
        renderer_text = gtk.CellRendererText()
        # Notice text=1, which means that we let the column display the
        # attribute values for the cell renderer from column 1 in the
        # tree model. Column 1 contains the location names.
        column = gtk.TreeViewColumn("Locations", renderer_text, text=1)
        # Sort on column 1 from the model.
        column.set_sort_column_id(1)
        # Add the column to the tree view.
        treeview.append_column(column)

class SelectSpecies(SelectionWindow):
    """Display a selection dialog that allows the user to make a
    selection from the SETL species in the local database.

    Design Part: 1.88
    """

    def __init__(self, title="Species Selection",
            description="Select the species:", width=-1, slot=0):
        super(SelectSpecies, self).__init__(title, description, width, slot)

        self.info_key = 'info-spe-selection'

    def on_back(self, widget, data=None):
        """Destroy the selection dialog and send the
        ``species-dialog-back`` signal.

        The ``species-dialog-back`` signal is sent with the save slot
        as an attribute. The save slot can have a value of ``0`` for the
        first selection and ``1`` for the second selection.

        This function is called when the user presses the Back button in
        a species selection window.

        Design Part: 1.46
        """

        # Then close this window.
        self.destroy()

        # Destroy the handlers.
        self.unset_signal_handlers()

        # Emit the signal that the Back button was pressed.
        setlyze.std.sender.emit('species-dialog-back', self.save_slot)

    def save_selection(self):
        """Save the species selection and send the
        ``species-selection-saved`` signal.

        The ``species-selection-saved`` signal is sent with the save slot
        as an attribute. The save slot can have a value of ``0`` for the
        first selection and ``1`` for the second selection.

        Design Part: 1.12.2
        """
        setlyze.config.cfg.set('species-selection', self.selection,
            slot=self.save_slot)

        # Make log message.
        selection = [setlyze.config.cfg.get('species-selection', slot=0),
            setlyze.config.cfg.get('species-selection', slot=1)]
        logging.info("\tSpecies selection set to: %s" % selection)

        # Emit the signal that a selection was saved.
        setlyze.std.sender.emit('species-selection-saved', self.save_slot)

    def create_model(self):
        """Create a model for the tree view from the species IDs and
        names.

        Design Part: 1.43
        """

        # Create an object for accessing the local database.
        db = setlyze.database.AccessLocalDB()

        # Create the model.
        self.model = gtk.ListStore(gobject.TYPE_INT,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)


        for item in db.get_species(loc_slot=self.save_slot):
            self.model.append([item[0], item[1], item[2]])

        # Create a sorted version of the model. Then sort on the latin
        # species names.
        self.model = gtk.TreeModelSort(self.model)
        self.model.set_sort_column_id(2, gtk.SORT_ASCENDING)

    def create_columns(self, treeview):
        """Create columns for the tree view."""
        renderer_text = gtk.CellRendererText()
        # Notice text=2, which means that we let the column display the
        # attribute values for the cell renderer from column 2 in the
        # TreeModel. Column 2 contains the species names (latin).
        column = gtk.TreeViewColumn("Species (Latin)", renderer_text, text=2)
        # Sort on column 2 from the model.
        column.set_sort_column_id(2)
        column.set_sort_order(gtk.SORT_ASCENDING)
        column.set_resizable(True)
        # Add the column to the tree view.
        treeview.append_column(column)

        renderer_text = gtk.CellRendererText()
        # Notice text=1, which means that we let the column display the
        # attribute values for the cell renderer from column 1 in the
        # TreeModel. Column 1 contains the species names (venacular).
        column = gtk.TreeViewColumn("Species (venacular)", renderer_text,
            text=1)
        # Sort on column 1 from the model.
        column.set_sort_column_id(1)
        column.set_resizable(True)
        # Add the column to the tree view.
        treeview.append_column(column)

class DefinePlateAreas(gtk.Window):
    """Display a dialog that allows the user to define the areas on a
    SETL plate.

    Below is a SETL-plate with a grid. By default there are 4 surface
    areas defined on a SETL plate (A, B, C and D). Sometimes it's useful
    to combine plate areas.

    +---+---+---+---+---+
    | A | B | B | B | A |
    +---+---+---+---+---+
    | B | C | C | C | B |
    +---+---+---+---+---+
    | B | C | D | C | B |
    +---+---+---+---+---+
    | B | C | C | C | B |
    +---+---+---+---+---+
    | A | B | B | B | A |
    +---+---+---+---+---+

    So if the user decides to combine A and B, the plate areas
    definition looks like this,

    +---+---+---+---+---+
    | A | A | A | A | A |
    +---+---+---+---+---+
    | A | C | C | C | A |
    +---+---+---+---+---+
    | A | C | D | C | A |
    +---+---+---+---+---+
    | A | C | C | C | A |
    +---+---+---+---+---+
    | A | A | A | A | A |
    +---+---+---+---+---+

    Design Part: 1.91
    """

    def __init__(self, title="Define SETL-plate Areas for Chi-squared Test"):
        super(DefinePlateAreas, self).__init__()

        self.set_title(title)
        self.set_size_request(-1, -1)
        self.set_border_width(0)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # The areas definition.
        self.definition = None

        # Handle window signals.
        self.connect('delete-event', on_quit)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=5, columns=2, homogeneous=False)
        table.set_col_spacings(0)
        table.set_row_spacings(10)

        # Create a toolbar.
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_ICONS)
        toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        toolbar.set_tooltips(True)

        # Create buttons for the toolbar.
        button_home = gtk.ToolButton(gtk.STOCK_HOME)
        sep = gtk.SeparatorToolItem()
        button_help = gtk.ToolButton(gtk.STOCK_HELP)

        # Add the buttons to the toolbar.
        toolbar.insert(button_home, 0)
        toolbar.insert(sep, 1)
        toolbar.insert(button_help, 2)

        # Handle button signals.
        button_home.connect("clicked", self.on_close_dialog)
        button_help.connect("clicked", on_help, 'define-plate-areas-dialog')

        # Add the toolbar to the vertical box.
        table.attach(toolbar, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a vertical box to place the widgets in.
        vbox = gtk.VBox(homogeneous=False, spacing=5)

        # Create a dialog header.
        header = gtk.Label()
        header.set_alignment(xalign=0, yalign=0)
        header.set_line_wrap(True)
        header.set_justify(gtk.JUSTIFY_FILL)
        header.set_markup(markup_header(self.get_title()))
        # Add the label to the vertcal box.
        vbox.pack_start(header, expand=False, fill=True, padding=0)

        # Create a description label.
        label_descr = gtk.Label( setlyze.locale.text('define-plate-areas') )
        label_descr.set_alignment(xalign=0, yalign=0)
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        # Add the label to the vertcal box.
        vbox.pack_start(label_descr, expand=False, fill=True, padding=0)

        # Add the label to the table.
        table.attach(vbox, left_attach=0, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=0)

        # Load an image of the SETL grid.
        setl_grid = gtk.Image()
        if setlyze.std.we_are_frozen():
            image_path = os.path.join(setlyze.std.module_path(),
                'images/setl-grid.png')
        else:
            image_path = pkg_resources.resource_filename('setlyze',
                'images/setl-grid.png')
        setl_grid.set_from_file(image_path)
        # Add the image to the table.
        table.attach(setl_grid, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=0)

        # Create the definition table.
        def_table = self.create_definition_table()
        # Add def_table to the main table.
        table.attach(def_table, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=0)

        # Continue button
        button_continue = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        button_continue.set_label("_Continue")
        button_continue.set_size_request(-1, -1)
        button_continue.connect("clicked", self.on_continue)

        # Back button
        button_back = gtk.Button(stock=gtk.STOCK_GO_BACK)
        button_back.set_size_request(-1, -1)
        button_back.connect("clicked", self.on_back)

        # But the button in a horizontal button box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_back, expand=True,
            fill=True, padding=0)
        button_box_r.pack_start(button_continue, expand=True,
            fill=True, padding=0)

        # Add the aligned box to the table
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=10, ypadding=5)

        # Add the table to the main window.
        self.add(table)

    def create_definition_table(self):
        """Construct the form for defining the plate areas."""

        # Create a table for the radio buttons.
        def_table = gtk.Table(rows=5, columns=5, homogeneous=False)
        def_table.set_col_spacings(10)
        def_table.set_row_spacings(10)

        # Create labels.
        label_spot1 = gtk.Label("Plate area 1: ")
        # Add the label to the table.
        def_table.attach(child=label_spot1, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_spot2 = gtk.Label("Plate area 2: ")
        # Add the label to the table.
        def_table.attach(child=label_spot2, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_spot3 = gtk.Label("Plate area 3: ")
        # Add the label to the table.
        def_table.attach(child=label_spot3, left_attach=0, right_attach=1,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_spot4 = gtk.Label("Plate area 4: ")
        # Add the label to the table.
        def_table.attach(child=label_spot4, left_attach=0, right_attach=1,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_a = gtk.Label()
        label_a.set_markup("<span size='x-large' weight='normal'>A</span>")
        # Add the label to the table.
        def_table.attach(child=label_a, left_attach=1, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_b = gtk.Label()
        label_b.set_markup("<span size='x-large' weight='normal'>B</span>")
        # Add the label to the table.
        def_table.attach(child=label_b, left_attach=2, right_attach=3,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_c = gtk.Label()
        label_c.set_markup("<span size='x-large' weight='normal'>C</span>")
        # Add the label to the table.
        def_table.attach(child=label_c, left_attach=3, right_attach=4,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        label_d = gtk.Label()
        label_d.set_markup("<span size='x-large' weight='normal'>D</span>")
        # Add the label to the table.
        def_table.attach(child=label_d, left_attach=4, right_attach=5,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create radio buttons column A.
        self.radio_1A = gtk.RadioButton(None)
        self.radio_1A.set_active(True)
        def_table.attach(self.radio_1A, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_2A = gtk.RadioButton(self.radio_1A)
        def_table.attach(self.radio_2A, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_3A = gtk.RadioButton(self.radio_1A)
        def_table.attach(self.radio_3A, left_attach=1, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_4A = gtk.RadioButton(self.radio_1A)
        def_table.attach(self.radio_4A, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create radio buttons column B.
        self.radio_1B = gtk.RadioButton(None)
        def_table.attach(self.radio_1B, left_attach=2, right_attach=3,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_2B = gtk.RadioButton(self.radio_1B)
        self.radio_2B.set_active(True)
        def_table.attach(self.radio_2B, left_attach=2, right_attach=3,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_3B = gtk.RadioButton(self.radio_1B)
        def_table.attach(self.radio_3B, left_attach=2, right_attach=3,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_4B = gtk.RadioButton(self.radio_1B)
        def_table.attach(self.radio_4B, left_attach=2, right_attach=3,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create radio buttons column C.
        self.radio_1C = gtk.RadioButton(None)
        def_table.attach(self.radio_1C, left_attach=3, right_attach=4,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_2C = gtk.RadioButton(self.radio_1C)
        def_table.attach(self.radio_2C, left_attach=3, right_attach=4,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_3C = gtk.RadioButton(self.radio_1C)
        self.radio_3C.set_active(True)
        def_table.attach(self.radio_3C, left_attach=3, right_attach=4,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_4C = gtk.RadioButton(self.radio_1C)
        def_table.attach(self.radio_4C, left_attach=3, right_attach=4,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create radio buttons column D.
        self.radio_1D = gtk.RadioButton(None)
        def_table.attach(self.radio_1D, left_attach=4, right_attach=5,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_2D = gtk.RadioButton(self.radio_1D)
        def_table.attach(self.radio_2D, left_attach=4, right_attach=5,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_3D = gtk.RadioButton(self.radio_1D)
        def_table.attach(self.radio_3D, left_attach=4, right_attach=5,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        self.radio_4D = gtk.RadioButton(self.radio_1D)
        self.radio_4D.set_active(True)
        def_table.attach(self.radio_4D, left_attach=4, right_attach=5,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        return def_table

    def on_close_dialog(self, widget=None, data=None):
        """Close the dialog and send the ``define-areas-dialog-closed``
        signal.

        This method should is called when the user presses the X (close)
        button of the selection dialog. The signal can then be handled
        in the analysis class.
        """
        self.destroy()

        # Emit the signal that the dialog was closed.
        setlyze.std.sender.emit('define-areas-dialog-closed')

    def on_continue(self, widget, data=None):
        """Check if the user made a correct definition. If yes, normalize
        the definition and save it."""

        # Get the user selected plate areas definition.
        definition = self.get_selection()

        # Check if the definition is any good.
        if not self.iscorrect(definition):
            # Apparently the definition was not good.
            return

        # Then close this window.
        self.destroy()

        # Normalize the definition.
        definition = self.normalize(definition)

        # Save the definition.
        self.save(definition)

    def on_back(self, widget, data=None):
        """Destroy the dialog and send the ``define-areas-dialog-back``
        signal.

        This function is called when the user presses the Back button.
        """

        # Close the dialog.
        self.destroy()

        # Emit the signal that the Back button was pressed.
        setlyze.std.sender.emit('define-areas-dialog-back')

    def get_selection(self):
        """Return the plate areas as defined by the user."""

        # Spot are definition table.
        area_selection = {  'area1': [],
                            'area2': [],
                            'area3': [],
                            'area4': [] }

        # Fill the definition table.
        area_selection['area1'].append( self.radio_1A.get_active() )
        area_selection['area1'].append( self.radio_1B.get_active() )
        area_selection['area1'].append( self.radio_1C.get_active() )
        area_selection['area1'].append( self.radio_1D.get_active() )

        area_selection['area2'].append( self.radio_2A.get_active() )
        area_selection['area2'].append( self.radio_2B.get_active() )
        area_selection['area2'].append( self.radio_2C.get_active() )
        area_selection['area2'].append( self.radio_2D.get_active() )

        area_selection['area3'].append( self.radio_3A.get_active() )
        area_selection['area3'].append( self.radio_3B.get_active() )
        area_selection['area3'].append( self.radio_3C.get_active() )
        area_selection['area3'].append( self.radio_3D.get_active() )

        area_selection['area4'].append( self.radio_4A.get_active() )
        area_selection['area4'].append( self.radio_4B.get_active() )
        area_selection['area4'].append( self.radio_4C.get_active() )
        area_selection['area4'].append( self.radio_4D.get_active() )

        return area_selection

    def iscorrect(self, definition):
        """Check if the user defined plate areas are correct.

        Return True if the definition is correct, and False if it's not.
        If the definition is False, display a message dialog describing
        the problem.
        """

        # Check if the user combined all surfaces together.
        for area, selection in definition.iteritems():
            # Count the number of selected (True's) for each plate area.
            if selection.count(True) == 4:
                # The user combined all surfaces to one plate area. This
                # is useless, so show a warning.
                dialog = gtk.MessageDialog(parent=None, flags=0,
                    type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                    message_format="Invalid plate areas definition")
                dialog.format_secondary_text( setlyze.locale.text(
                    'error-single-plate-area') )
                dialog.set_position(gtk.WIN_POS_CENTER)
                dialog.run()
                dialog.destroy()

                # The definition is not correct.
                return False

        # 's alright...
        return True

    def normalize(self, definition):
        """Return a normalized and simplified version of `definition`.

        This means that an area selection that looks like
        [True, False, True, False] will be converted to ['A','C']. Empty
        areas are removed from the normalized spot areas definition.

        For example, if `definition` equals ::

            {
            'area1': [True, False, False, False],
            'area2': [False, True, False, False],
            'area3': [False, False, True, True],
            'area4': [False, False, False, False]
            }

        This method will return ::

            {
            'area1': ['A'],
            'area2': ['B'],
            'area3': ['C', 'D']
            }
        """

        # Index to spot name.
        index2name = {0:'A', 1:'B', 2:'C', 3:'D'}

        # New spot area definition.
        new_definition = {  'area1': [],
                            'area2': [],
                            'area3': [],
                            'area4': [] }

        # For every True in a selection, replace it with the surface
        # name, an put it in the new plate area definition.
        for area, selection in definition.iteritems():
            i = 0
            for item in selection:
                if item:
                    new_definition[area].append(index2name[i])
                i += 1

        # Remove empty areas.
        remove = []
        for area, selection in new_definition.iteritems():
            if len(selection) == 0:
                remove.append(area)
        for area in remove:
            del new_definition[area]

        # Return the normalized definition.
        return new_definition

    def save(self, definition):
        """Save the plate areas definition and emit the
        ``plate-areas-defined`` signal.
        """

        # Set the spots definition.
        setlyze.config.cfg.set('plate-areas-definition', definition)

        # Make log message.
        logging.info("\tPlate areas definition set to: %s" % definition)

        # Emit the signal that the plate areas are defined.
        setlyze.std.sender.emit('plate-areas-defined')

class ChangeDataSource(gtk.Window):
    """Display a dialog that allows the user to change to a different
    data source. The following data sources are supported:

        * CSV files with SETL data exported from the MS Access SETL
          database.

        * Import of Microsoft Excel spread-sheet files.

        * TODO: The remote SETL database. This requires a direct
          connection with the SETL database server.

    Design Part: 1.90
    """

    def __init__(self):
        super(ChangeDataSource, self).__init__()
        self.signal_handlers = {}

        self.set_title("Change Data Source")
        self.set_size_request(-1, -1)
        self.set_border_width(10)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_modal(True)

        # Create the layout for the dialog.
        self.create_layout()

        # Bind handles to application signals.
        self.set_signal_handlers()

        # Display all widgets.
        self.show_all()

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            # Show an epic fail message when import fails.
            'csv-import-failed': setlyze.std.sender.connect('csv-import-failed', self.on_csv_import_failed),

            # Make sure the above handle is disconnected when loading new SETL data succeeds.
            'local-db-created': setlyze.std.sender.connect('local-db-created', self.unset_signal_handlers)
        }

    def unset_signal_handlers(self, sender=None, data=None):
        """Disconnect all signal connections with signal handlers created by
        this class.
        """
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a new notebook, place the position of the tabs
        notebook = gtk.Notebook()
        notebook.set_tab_pos(gtk.POS_TOP)

        # Create a vertical box container.
        vbox = gtk.VBox(homogeneous=False, spacing=5)
        vbox.set_border_width(0)

        # Create pages for the notebook.
        page_csv = self.create_page_csv()
        page_db = self.create_page_db()
        page_xls = self.create_page_xls()

        # Add the pages to the notebook.
        label_csv = gtk.Label("CSV Files From Access DB")
        notebook.append_page(page_csv, label_csv)

        label_db = gtk.Label("Remote SETL DB")
        notebook.append_page(page_db, label_db)

        # Microsoft Excel spreadsheet files
        label_xls = gtk.Label("XLS Files From Microsoft Excel")
        notebook.append_page(page_xls, label_xls)

        # Add a header to the dialog.
        label_header = gtk.Label()
        label_header.set_alignment(xalign=0, yalign=0)
        label_header.set_line_wrap(True)
        label_header.set_justify(gtk.JUSTIFY_FILL)
        label_header.set_markup(markup_header("Change Data Source"))
        vbox.add(label_header)

        # Add a label to the vertical box.
        label_descr = gtk.Label( setlyze.locale.text('change-data-source') )
        label_descr.set_alignment(xalign=0, yalign=0)
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        vbox.add(label_descr)

        # Add the notebook to the vertical box.
        vbox.add(notebook)

        # Add the vertical box to the main window.
        self.add(vbox)

    def create_page_db(self):
        """Return a notebook page for switching to SETL data from
        the remote SETL database."""

        # Create a table to organize the widgets in.
        table = gtk.Table(rows=1, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        table.set_border_width(10)

        # Create a description label.
        label_descr = gtk.Label( setlyze.locale.text('change-data-source-db') )
        label_descr.set_alignment(xalign=0, yalign=0)
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        table.attach(child=label_descr, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        return table

    def create_page_csv(self):
        """Return a notebook page for switching to SETL data from
        CSV files."""

        # Create a table to organize the widgets in.
        table = gtk.Table(rows=6, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        table.set_border_width(10)

        # Create a description label.
        label_descr = gtk.Label( setlyze.locale.text('change-data-source-csv') )
        label_descr.set_alignment(xalign=0, yalign=0)
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        table.attach(child=label_descr, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a filter for the file chooser.
        csv_filter = gtk.FileFilter()
        csv_filter.set_name("Comma Separated File (*.csv, *.txt)")
        csv_filter.add_mime_type("text/csv")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_pattern("*.txt")

        # Create labels.
        label_localities = gtk.Label("Select localities file:")
        label_localities.set_alignment(xalign=0, yalign=0)
        label_species = gtk.Label("Select species file:")
        label_species.set_alignment(xalign=0, yalign=0)
        label_records = gtk.Label("Select records file:")
        label_records.set_alignment(xalign=0, yalign=0)
        label_plates = gtk.Label("Select plates file:")
        label_plates.set_alignment(xalign=0, yalign=0)

        # Create a localities file chooser button.
        self.loc_file_chooser = gtk.FileChooserButton('Select file...')
        self.loc_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.loc_file_chooser.add_filter(csv_filter)
        self.loc_file_chooser.connect('current-folder-changed',
            self.update_working_folder)

        # Create a plates file chooser button.
        self.pla_file_chooser = gtk.FileChooserButton('Select file...')
        self.pla_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.pla_file_chooser.add_filter(csv_filter)

        # Create a records file chooser button.
        self.rec_file_chooser = gtk.FileChooserButton('Select file...')
        self.rec_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.rec_file_chooser.add_filter(csv_filter)

        # Create a species file chooser button.
        self.spe_file_chooser = gtk.FileChooserButton('Select file...')
        self.spe_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.spe_file_chooser.add_filter(csv_filter)

        # Add the labels to the table.
        table.attach(label_localities, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_plates, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_records, left_attach=0, right_attach=1,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_species, left_attach=0, right_attach=1,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the file choosers to the table.
        table.attach(self.loc_file_chooser, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.pla_file_chooser, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.rec_file_chooser, left_attach=1, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.spe_file_chooser, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # OK button
        button_ok = gtk.Button(stock=gtk.STOCK_OK)
        button_ok.set_size_request(-1, -1)
        button_ok.connect("clicked", self.on_csv_ok)

        # Cancel button
        button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_cancel.set_size_request(-1, -1)
        button_cancel.connect("clicked", self.on_cancel)

        # But the button in a horizontal button box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_cancel, expand=True, fill=True,
            padding=0)
        button_box_r.pack_start(button_ok, expand=True, fill=True, padding=0)

        # Add the aligned box to the table
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=5, bottom_attach=6, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        return table

    def create_page_xls(self):
        """Return a notebook page for switching to SETL data from
        XLS files."""

        # Create a table to organize the widgets in.
        table = gtk.Table(rows=6, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)
        table.set_border_width(10)

        # Create a description label.
        label_descr = gtk.Label( setlyze.locale.text('change-data-source-xls') )
        label_descr.set_alignment(xalign=0, yalign=0)
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        table.attach(child=label_descr, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a filter for the file chooser.
        xls_filter = gtk.FileFilter()
        xls_filter.set_name("Excel File (*.xls)")
        xls_filter.add_mime_type("application/vnd.ms-excel")
        xls_filter.add_pattern("*.xls")

        # Create labels.
        label_localities = gtk.Label("Select localities file:")
        label_localities.set_alignment(xalign=0, yalign=0)
        label_species = gtk.Label("Select species file:")
        label_species.set_alignment(xalign=0, yalign=0)
        label_records = gtk.Label("Select records file:")
        label_records.set_alignment(xalign=0, yalign=0)
        label_plates = gtk.Label("Select plates file:")
        label_plates.set_alignment(xalign=0, yalign=0)


        # Create a localities file chooser button.
        self.loc_xls_file_chooser = gtk.FileChooserButton('Select file...')
        self.loc_xls_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.loc_xls_file_chooser.add_filter(xls_filter)
        self.loc_xls_file_chooser.connect('current-folder-changed',
            self.update_working_folder)

        # Create a plates file chooser button.
        self.pla_xls_file_chooser = gtk.FileChooserButton('Select file...')
        self.pla_xls_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.pla_xls_file_chooser.add_filter(xls_filter)

        # Create a records file chooser button.
        self.rec_xls_file_chooser = gtk.FileChooserButton('Select file...')
        self.rec_xls_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.rec_xls_file_chooser.add_filter(xls_filter)

        # Create a species file chooser button.
        self.spe_xls_file_chooser = gtk.FileChooserButton('Select file...')
        self.spe_xls_file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.spe_xls_file_chooser.add_filter(xls_filter)

        # Add the labels to the table.
        table.attach(label_localities, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_plates, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_records, left_attach=0, right_attach=1,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(label_species, left_attach=0, right_attach=1,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the file choosers to the table.
        table.attach(self.loc_xls_file_chooser, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.pla_xls_file_chooser, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.rec_xls_file_chooser, left_attach=1, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)
        table.attach(self.spe_xls_file_chooser, left_attach=1, right_attach=2,
            top_attach=4, bottom_attach=5, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # OK button for xls files.
        button_ok = gtk.Button(stock=gtk.STOCK_OK)
        button_ok.set_size_request(-1, -1)
        button_ok.connect("clicked", self.on_xls_ok)

        # Cancel button
        button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_cancel.set_size_request(-1, -1)
        button_cancel.connect("clicked", self.on_cancel)

        # But the button in a horizontal button box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_cancel, expand=True, fill=True, padding=0)
        button_box_r.pack_start(button_ok, expand=True, fill=True, padding=0)

        # Add the aligned box to the table
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=5, bottom_attach=6, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        return table

    def on_csv_ok(self, widget, data=None):
        """Save the paths to the CSV files, set the new value for the
        data source configuration, load the SETL data from the CSV file
        into the local database, and close the dialog.
        """

        # Check if all files are selected.
        if not self.loc_file_chooser.get_filename() or \
            not self.spe_file_chooser.get_filename() or \
            not self.rec_file_chooser.get_filename() or \
            not self.pla_file_chooser.get_filename():
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Not all CSV files selected")
            dialog.format_secondary_text( setlyze.locale.text(
                'csv-files-not-selected') )
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return False

        # Save the paths.
        setlyze.config.cfg.set('localities-file',
            self.loc_file_chooser.get_filename() )
        setlyze.config.cfg.set('species-file',
            self.spe_file_chooser.get_filename() )
        setlyze.config.cfg.set('records-file',
            self.rec_file_chooser.get_filename() )
        setlyze.config.cfg.set('plates-file',
            self.pla_file_chooser.get_filename() )

        # Let the application know that we are now using user selected CSV files.
        setlyze.config.cfg.set('data-source', 'csv-msaccess')

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading data",
            description="Please wait while the data is being loaded...")
        setlyze.config.cfg.set('progress-dialog', pd)

        # Make a new local database.
        t = setlyze.database.MakeLocalDB()
        t.start()

        # Close the dialog.
        self.destroy()

    def on_xls_ok(self, widget, data=None):
        """Save the paths to the XLS files, set the new value for the
        data source configuration, load the SETL data from the XLS file
        into the local database, and close the dialog.
        """

        # Check if all files are selected.
        if not self.loc_xls_file_chooser.get_filename() or \
            not self.spe_xls_file_chooser.get_filename() or \
            not self.rec_xls_file_chooser.get_filename() or \
            not self.pla_xls_file_chooser.get_filename():
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Not all xls files selected")
            dialog.format_secondary_text( setlyze.locale.text(
                'xls-files-not-selected') )
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return False

        # Save the paths.
        setlyze.config.cfg.set('localities-file',
            self.loc_xls_file_chooser.get_filename() )
        setlyze.config.cfg.set('species-file',
            self.spe_xls_file_chooser.get_filename() )
        setlyze.config.cfg.set('records-file',
            self.rec_xls_file_chooser.get_filename() )
        setlyze.config.cfg.set('plates-file',
            self.pla_xls_file_chooser.get_filename() )

        # Let the application know that we are now using user selected xls files.
        setlyze.config.cfg.set('data-source', 'xls')

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading data",
            description="Please wait while the data is being loaded...")
        setlyze.config.cfg.set('progress-dialog', pd)

        # Make a new local database.
        t = setlyze.database.MakeLocalDB()
        t.start()

        # Close the dialog.
        self.destroy()

    def on_csv_import_failed(self, sender, error, data=None):
        """Display an error message showing the user that importing SETL data
        from the selected CSV or XLS files failed.
        """
        self.unset_signal_handlers()

        # Close the progress dialog.
        setlyze.config.cfg.get('progress-dialog').destroy()

        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
            message_format="Loading SETL data failed")
        dialog.format_secondary_text( setlyze.locale.text('csv-import-failed',
            error) )
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Returning True indicates that the event has been handled, and that
        # it should not propagate further.
        return True

    def on_cancel(self, widget, data=None):
        """Close the dialog."""
        self.unset_signal_handlers()
        self.destroy()

    def update_working_folder(self, chooser, data=None):
        """Set the working folder for the file choosers to the folder
        where the first data file was selected from.

        This way the user doesn't have to navigate to the same folder
        multiple times.
        """
        path = chooser.get_filename()
        if path:
            folder = os.path.dirname(path)
            # For the CSV files
            self.spe_file_chooser.set_current_folder(folder)
            self.rec_file_chooser.set_current_folder(folder)
            self.pla_file_chooser.set_current_folder(folder)
            # For the XLS files
            self.spe_xls_file_chooser.set_current_folder(folder)
            self.rec_xls_file_chooser.set_current_folder(folder)
            self.pla_xls_file_chooser.set_current_folder(folder)

class ProgressDialog(gtk.Window):
    """Display a progress dialog.

    This progress dialog is useful if you have a process that could
    take a long time to run. This class allows you to display a progress
    dialog which shows the progress for a long process (called the worker
    process). This worker process needs to run in a separate thread for
    this to work.

    You cannot access the progress dialog, which runs in the main thread, from
    a separate (worker) thread. Doing this will cause the application to crash.
    For the purpose of controlling the progress dialog from the worker
    process, use :class:`setlyze.std.ProgressDialogHandler`. Read the
    documentation for that class for usage information.

    Design Part: 1.92
    """

    def __init__(self, title, description):
        super(ProgressDialog, self).__init__()

        self.description = description

        self.set_size_request(400, -1)
        self.set_title(title)
        self.set_border_width(0)
        self.set_deletable(True)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_keep_above(True)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', self.on_close)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a vertical box container.
        vbox = gtk.VBox(homogeneous=False, spacing=5)
        vbox.set_border_width(10)

        # Create a label.
        self.descr_label = gtk.Label()
        self.descr_label.set_line_wrap(True)
        self.descr_label.set_text(self.description)
        self.descr_label.set_alignment(xalign=0, yalign=0)

        # Create a label.
        self.action = gtk.Label()
        self.action.set_alignment(xalign=0, yalign=0)

        # Create the progress bar.
        self.pbar = gtk.ProgressBar()
        self.pbar.set_fraction(0.0)
        self.pbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)

        pbar_align = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=1.0,
            yscale=0.0)
        pbar_align.add(self.pbar)

        # Cancel button
        self.button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.button_cancel.set_size_request(-1, -1)
        self.button_cancel.connect("clicked", self.on_cancel)

        # But the button in a horizontal button box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(self.button_cancel, expand=True, fill=True,
            padding=0)

        # Add the alignment objects to the vertical container.
        vbox.pack_start(self.descr_label, expand=False, fill=False, padding=5)
        vbox.pack_start(pbar_align, expand=False, fill=False, padding=5)
        vbox.pack_start(self.action, expand=False, fill=True, padding=0)
        vbox.pack_start(button_box_r, expand=False, fill=False, padding=0)

        self.add(vbox)

    def on_cancel(self, widget=None, data=None):
        """Destroy the dialog and send cancel signal."""
        logging.info("Cancel button is pressed")
        self.destroy()
        setlyze.std.sender.emit('analysis-canceled')

    def on_close(self, widget=None, data=None):
        """Destroy the dialog."""
        logging.info("Close button is pressed")
        self.destroy()
        setlyze.std.sender.emit('progress-dialog-closed')

class Report(gtk.Window):
    """Display a dialog visualizing the elements in a report object.

    The argument `report` must be an instance of
    :class:`setlyze.report.Report`
    """

    def __init__(self, report):
        super(Report, self).__init__()

        self.report = report
        self.set_title("Analysis Report")
        self.set_size_request(600, 500)
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', on_quit)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=4, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)

        # Create a toolbar.
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_BOTH)
        toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        toolbar.set_tooltips(True)

        # Create buttons for the toolbar.
        button_home = gtk.ToolButton(gtk.STOCK_HOME)
        button_save = gtk.ToolButton(gtk.STOCK_SAVE_AS)
        button_save.set_label("Save Report")
        sep = gtk.SeparatorToolItem()
        button_help = gtk.ToolButton(gtk.STOCK_HELP)

        # Add the buttons to the toolbar.
        toolbar.insert(button_home, 0)
        toolbar.insert(button_save, 1)
        toolbar.insert(sep, 2)
        toolbar.insert(button_help, 3)

        # Handle button signals.
        button_home.connect("clicked", self.on_close)
        button_save.connect("clicked", self.on_save)
        button_help.connect("clicked", on_help, 'analysis-report-dialog')

        # Add the toolbar to the vertical box.
        table.attach(toolbar, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a vertical box for widgets that go on the top of the
        # report window, like the report header.
        self.vbox_top = gtk.VBox(homogeneous=False, spacing=1)

        # Add the vbox_top to the table.
        table.attach(self.vbox_top, left_attach=0, right_attach=2,
            top_attach=1, bottom_attach=2,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.SHRINK | gtk.FILL,
            xpadding=10, ypadding=0)

        # Create a vertical box for the differenct report elements like
        # locations/species selection, significance results, etc.
        self.vbox = gtk.VBox(homogeneous=False, spacing=1)

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE) # Has no effect.
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # Add the vertical box to the scrolled window. A gtk.VBox
        # doesn't have native scrolling capabilities, so we use
        # add_with_viewport() instead of the usual add().
        scrolled_window.add_with_viewport(self.vbox)

        # Add the scrolled window to the table.
        table.attach(scrolled_window, left_attach=0, right_attach=2,
            top_attach=2, bottom_attach=3,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            xpadding=10, ypadding=0)

        # Add report elements.
        self.add_report_elements()

        # Add the table to the window.
        self.add(table)

    def on_close(self, obj, data=None):
        """Close the dialog and emit the `report-dialog-closed` signal."""

        # Close the report window.
        self.destroy()

        # Emit the signal that an analysis report window was closed.
        setlyze.std.sender.emit('report-dialog-closed')

    def on_save(self, obj, data=None):
        """Display a dialog that allows the user to save the report to
        a file.
        """

        # Create a file chooser dialog.
        chooser = gtk.FileChooserDialog(title="Save Analysis Report As...",
            parent=None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_SAVE, gtk.RESPONSE_OK),
            backend=None)
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_do_overwrite_confirmation(True)

        # Create a filter for the file chooser.
        xml_filter = gtk.FileFilter()
        xml_filter.set_name("XML Document (*.xml)")
        xml_filter.add_mime_type("text/xml")
        xml_filter.add_pattern("*.xml")

        txt_filter = gtk.FileFilter()
        txt_filter.set_name("Plain Text Document (*.txt)")
        txt_filter.add_pattern("*.txt")

        tex_filter = gtk.FileFilter()
        tex_filter.set_name("LaTeX Document (*.tex, *.latex)")
        tex_filter.add_mime_type("application/x-tex")
        tex_filter.add_mime_type("application/x-latex")
        tex_filter.add_pattern("*.tex")
        tex_filter.add_pattern("*.latex")

        chooser.add_filter(txt_filter)
        #chooser.add_filter(tex_filter)
        chooser.add_filter(xml_filter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            # Get the filename to which the data should be exported.
            path = chooser.get_filename()

            # Get the name of the selected file type.
            filter_name = chooser.get_filter().get_name()

            # Close the filechooser.
            chooser.destroy()

            # File type = XML
            if "*.xml" in filter_name:
                setlyze.report.export(self.reader, path, 'xml')

            # File type = text
            elif "*.txt" in filter_name:
                # Let the user select which elements to export.
                dialog = SelectExportElements(self.reader)
                response = dialog.run()

                # Export the selected report elements.
                if response == gtk.RESPONSE_ACCEPT:
                    setlyze.report.export(self.reader, path, 'txt',
                        dialog.get_selected_elements())
                dialog.destroy()

            # File type = LaTeX
            elif "*.tex" in filter_name:
                # Let the user select which elements to export.
                dialog = SelectExportElements(self.reader)
                response = dialog.run()

                # Export the selected report elements.
                if response == gtk.RESPONSE_ACCEPT:
                    setlyze.report.export(self.reader, path, 'latex',
                        dialog.get_selected_elements())
                dialog.destroy()
        else:
            chooser.destroy()

    def add_report_elements(self):
        """Add the report elements present in the XML DOM object to the
        report dialog.
        """
        if not self.report:
            return

        if hasattr(self.report, 'analysis_name'):
            self.add_title_header(self.report.analysis_name)

        if hasattr(self.report, 'locations_selections') and \
            hasattr(self.report, 'species_selections'):
            self.add_selections(self.report.locations_selections, self.report.species_selections)

        if hasattr(self.report, 'plate_areas_definition'):
            self.add_plate_areas_definition(self.report.plate_areas_definition)

        if hasattr(self.report, 'area_totals_observed') and \
            hasattr(self.report, 'area_totals_expected'):
            self.add_area_totals(self.report.area_totals_observed, self.report.area_totals_expected)

        if 'chi_squared_areas' in self.report.statistics:
            for stats in self.report.statistics['chi_squared_areas']:
                self.add_statistics_chisq_areas(stats)

        if 'wilcoxon_spots' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_spots']:
                self.add_statistics_wilcoxon_spots(stats)

        if 'wilcoxon_spots_repeats' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_spots_repeats']:
                self.add_statistics_repeats_spots(stats)

        if 'wilcoxon_ratios' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_ratios']:
                self.add_statistics_wilcoxon_ratios(stats)

        if 'wilcoxon_ratios_repeats' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_ratios_repeats']:
                self.add_statistics_repeats_ratios(stats)

        if 'wilcoxon_areas' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_areas']:
                self.add_statistics_wilcoxon_areas(stats)

        if 'wilcoxon_areas_repeats' in self.report.statistics:
            for stats in self.report.statistics['wilcoxon_areas_repeats']:
                self.add_statistics_repeats_areas(stats)

        if 'chi_squared_spots' in self.report.statistics:
            for stats in self.report.statistics['chi_squared_spots']:
                self.add_statistics_chisq_spots(stats)

        if 'chi_squared_ratios' in self.report.statistics:
            for stats in self.report.statistics['chi_squared_ratios']:
                self.add_statistics_chisq_ratios(stats)

    def add_title_header(self, analysis_name):
        """Add a header text to the report dialog.

        The header contains the name of the analysis.
        """
        header = gtk.Label()
        header.set_alignment(xalign=0, yalign=0)
        header.set_line_wrap(False)
        header.set_markup(markup_header("Analysis Report: %s" % analysis_name))
        self.vbox_top.pack_start(header, expand=False, fill=True, padding=0)

    def add_selections(self, locations_selections, species_selections):
        """Add the location + species selections to the report dialog."""

        # Create a scrolled window.
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Locations and Species Selections")
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 200)
        # Add columns to the tree view.
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Locations and Species Selections", cell,
            text=0)
        tree.append_column(column)
        # To store the data, we use the TreeStore object.
        treestore = gtk.TreeStore(gobject.TYPE_STRING)

        # Add the species selection to the model.
        for i, species in enumerate(species_selections, start=1):
            treeiter = treestore.append(parent=None, row=["Species selection (%d)" % i])
            check = 0
            for id, spe in species.iteritems():
                species = "%s (%s)" % (spe['name_latin'], spe['name_common'])
                treestore.append(parent=treeiter, row=[species])
                check = 1
            if not check:
                treestore.remove(treeiter)

        # Add the locations selection to the model.
        for i, locations in enumerate(locations_selections, start=1):
            treeiter = treestore.append(parent=None, row=["Locations selection (%d)" % i])
            check = 0
            for id, loc in locations.iteritems():
                location = loc['name']
                treestore.append(parent=treeiter, row=[location])
                check = 1
            if not check:
                treestore.remove(treeiter)

        # Set the tree model.
        tree.set_model(treestore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the scorred window to the vertical box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_plate_areas_definition(self, definition):
        """Add the plate areas definition to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-plate-areas-definition'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 120)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Area ID", cell, text=0)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Plate Area Surfaces", cell, text=1)
        tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        for area_id, spots in sorted(definition.iteritems()):
            spots = ", ".join(spots)
            liststore.append([area_id, spots])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_area_totals(self, observed, expected):
        """Add the species totals per plate area to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-plate-area-totals'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 120)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Area ID", cell, text=0)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Observed Totals", cell, text=1)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Expected Totals", cell, text=2)
        tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(gobject.TYPE_STRING,
            gobject.TYPE_STRING, gobject.TYPE_STRING)

        # Add the distances to the model.
        for area_id in sorted(observed):
            liststore.append([area_id, observed[area_id], expected[area_id]])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_spots(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        for positive_spots,stats in statistics['results'].iteritems():
            # Add all result items to the tree model.
            liststore.append([
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_ratios(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Ratio Group','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        for ratio_group,stats in statistics['results'].iteritems():
            # Add all result items to the tree model.
            liststore.append([
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_areas(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 220)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Plate Area','n (totals)','n (observed species)',
            'n (expected species)', 'P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        for plate_area,stats in statistics['results'].iteritems():
            # Add all result items to the tree model.
            liststore.append([
                plate_area,
                stats['n_values'],
                stats['n_sp_observed'],
                stats['n_sp_expected'],
                stats['p_value'],
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_spots(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Chi squared','df',
            'Mean Observed','Mean Expected','Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        for positive_spots,stats in statistics['results'].iteritems():
            # Add all result items to the tree model.
            liststore.append([
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['chi_squared'],
                stats['df'],
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_areas(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 100)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['P-value','Chi squared','df','Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            )

        # Add all result items to the tree model.
        liststore.append([
            statistics['results']['p_value'],
            statistics['results']['chi_squared'],
            statistics['results']['df'],
            make_remarks(statistics['results'], statistics['attr']),
        ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_ratios(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ('Ratio Group','n (plates)',
            'n (distances)','P-value','Chi squared','df',
            'Mean Observed','Mean Expected','Remarks')

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        for ratio_group, stats in statistics['results'].iteritems():
            # Add all result items to the tree model.
            liststore.append([
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['p_value'],
                stats['chi_squared'],
                stats['df'],
                stats['mean_observed'],
                stats['mean_expected'],
                make_remarks(stats, statistics['attr']),
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_areas(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeats)" % statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 220)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Plate Area','n (totals)','n (observed species)',
            'n (significant)','n (non-significant)','n (preference)',
            'n (rejection)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        for plate_area, stats in statistics['results'].iteritems():
            liststore.append([
                plate_area,
                stats['n_values'],
                stats['n_sp_observed'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
                stats['n_preference'],
                stats['n_rejection'],
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_spots(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeats)" % statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)','n (distances)',
            'n (significant)','n (non-significant)','n (attraction)',
            'n (repulsion)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        for positive_spots, stats in statistics['results'].iteritems():
            liststore.append([
                positive_spots,
                stats['n_plates'],
                stats['n_values'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
                stats['n_attraction'],
                stats['n_repulsion'],
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_ratios(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeats)" % statistics['attr']['method'])
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Ratio Group','n (plates)','n (distances)',
            'n (significant)','n (non-significant)','n (attraction)',
            'n (repulsion)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        for ratio_group, stats in statistics['results'].iteritems():
            liststore.append([
                ratio_group,
                stats['n_plates'],
                stats['n_values'],
                stats['n_significant'],
                statistics['attr']['repeats'] - stats['n_significant'],
                stats['n_attraction'],
                stats['n_repulsion'],
            ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

class DisplayReport(gtk.Window):
    """Display a dialog visualizing the elements in the XML DOM analysis
    data object. The argument `reader` is an instance of
    :class:`setlyze.report.ReportReader`.

    This class uses :class:`~setlyze.report.ReportReader` to read the data
    from the XML DOM analysis data object.

    Design Part: 1.89
    """

    def __init__(self, report=None):
        super(DisplayReport, self).__init__()

        # Set the XML DOM for the ReportReader.
        self.set_report_reader(report)

        self.set_title("Analysis Report")
        self.set_size_request(600, 500)
        self.set_border_width(0)
        self.set_resizable(True)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', on_quit)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def set_report_reader(self, report):
        """Create a report reader and pass the XML DOM report data
        object `report` to the reader. `report` can also be the path to
        a report data XML file.
        """
        self.reader = setlyze.report.ReportReader(report)

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=4, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)

        # Create a toolbar.
        toolbar = gtk.Toolbar()
        toolbar.set_style(gtk.TOOLBAR_BOTH)
        toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        toolbar.set_tooltips(True)

        # Create buttons for the toolbar.
        button_home = gtk.ToolButton(gtk.STOCK_HOME)
        button_save = gtk.ToolButton(gtk.STOCK_SAVE_AS)
        button_save.set_label("Save Report")
        sep = gtk.SeparatorToolItem()
        button_help = gtk.ToolButton(gtk.STOCK_HELP)

        # Add the buttons to the toolbar.
        toolbar.insert(button_home, 0)
        toolbar.insert(button_save, 1)
        toolbar.insert(sep, 2)
        toolbar.insert(button_help, 3)

        # Handle button signals.
        button_home.connect("clicked", self.on_close)
        button_save.connect("clicked", self.on_save)
        button_help.connect("clicked", on_help, 'analysis-report-dialog')

        # Add the toolbar to the vertical box.
        table.attach(toolbar, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a vertical box for widgets that go on the top of the
        # report window, like the report header.
        self.vbox_top = gtk.VBox(homogeneous=False, spacing=1)

        # Add the vbox_top to the table.
        table.attach(self.vbox_top, left_attach=0, right_attach=2,
            top_attach=1, bottom_attach=2,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.SHRINK | gtk.FILL,
            xpadding=10, ypadding=0)

        # Create a vertical box for the differenct report elements like
        # locations/species selection, significance results, etc.
        self.vbox = gtk.VBox(homogeneous=False, spacing=1)

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE) # Has no effect.
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        # Add the vertical box to the scrolled window. A gtk.VBox
        # doesn't have native scrolling capabilities, so we use
        # add_with_viewport() instead of the usual add().
        scrolled_window.add_with_viewport(self.vbox)

        # Add the scrolled window to the table.
        table.attach(scrolled_window, left_attach=0, right_attach=2,
            top_attach=2, bottom_attach=3,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            xpadding=10, ypadding=0)

        # Add report elements.
        self.add_report_elements()

        # Add the table to the window.
        self.add(table)

    def on_close(self, obj, data=None):
        """Close the dialog and emit the `report-dialog-closed` signal."""

        # Close the report window.
        self.destroy()

        # Emit the signal that an analysis report window was closed.
        setlyze.std.sender.emit('report-dialog-closed')

    def on_save(self, obj, data=None):
        """Display a dialog that allows the user to save the report to
        a file.
        """

        # Create a file chooser dialog.
        chooser = gtk.FileChooserDialog(title="Save Analysis Report As...",
            parent=None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_SAVE, gtk.RESPONSE_OK),
            backend=None)
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_do_overwrite_confirmation(True)

        # Create a filter for the file chooser.
        xml_filter = gtk.FileFilter()
        xml_filter.set_name("XML Document (*.xml)")
        xml_filter.add_mime_type("text/xml")
        xml_filter.add_pattern("*.xml")

        txt_filter = gtk.FileFilter()
        txt_filter.set_name("Plain Text Document (*.txt)")
        txt_filter.add_pattern("*.txt")

        tex_filter = gtk.FileFilter()
        tex_filter.set_name("LaTeX Document (*.tex, *.latex)")
        tex_filter.add_mime_type("application/x-tex")
        tex_filter.add_mime_type("application/x-latex")
        tex_filter.add_pattern("*.tex")
        tex_filter.add_pattern("*.latex")

        chooser.add_filter(txt_filter)
        #chooser.add_filter(tex_filter)
        chooser.add_filter(xml_filter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            # Get the filename to which the data should be exported.
            path = chooser.get_filename()

            # Get the name of the selected file type.
            filter_name = chooser.get_filter().get_name()

            # Close the filechooser.
            chooser.destroy()

            # File type = XML
            if "*.xml" in filter_name:
                setlyze.report.export(self.reader, path, 'xml')

            # File type = text
            elif "*.txt" in filter_name:
                # Let the user select which elements to export.
                dialog = SelectExportElements(self.reader)
                response = dialog.run()

                # Export the selected report elements.
                if response == gtk.RESPONSE_ACCEPT:
                    setlyze.report.export(self.reader, path, 'txt',
                        dialog.get_selected_elements())
                dialog.destroy()

            # File type = LaTeX
            elif "*.tex" in filter_name:
                # Let the user select which elements to export.
                dialog = SelectExportElements(self.reader)
                response = dialog.run()

                # Export the selected report elements.
                if response == gtk.RESPONSE_ACCEPT:
                    setlyze.report.export(self.reader, path, 'latex',
                        dialog.get_selected_elements())
                dialog.destroy()
        else:
            chooser.destroy()

    def add_report_elements(self):
        """Add the report elements present in the XML DOM object to the
        report dialog.
        """
        if not self.reader.doc:
            return

        # Get the names of all root report elements.
        report_elements = self.reader.get_child_names()

        # Add the names of all statistics elements to the list of root
        # elements.
        statistics = self.reader.get_element(self.reader.doc, 'statistics')
        report_elements.extend(self.reader.get_child_names(statistics))

        # Add a header with the analysis name.
        self.add_title_header()

        #if 'species_selections' in report_elements:
        #    self.add_species_selections()

        #if 'location_selections' in report_elements:
        #    self.add_locations_selections()

        if "location_selections" in report_elements and \
                "species_selections" in report_elements:
            self.add_selections()

        if 'spot_distances_observed' in report_elements and \
                'spot_distances_expected' in report_elements:
            self.add_distances()

        if 'plate_areas_definition' in report_elements:
            self.add_plate_areas_definition()

        if 'area_totals_observed' in report_elements and \
                'area_totals_expected' in report_elements:
            self.add_area_totals()

        if 'chi_squared_areas' in report_elements:
            self.add_statistics_chisq_areas()

        if 'statistics' in report_elements:
            if 'normality' in report_elements:
                self.add_statistics_normality()

            if 't_test' in report_elements:
                self.add_statistics_ttest()

            if 'wilcoxon_spots' in report_elements:
                self.add_statistics_wilcoxon_spots()

            if 'wilcoxon_spots_repeats' in report_elements:
                self.add_statistics_repeats_spots('wilcoxon_spots', 'Wilcoxon')

            if 'wilcoxon_ratios' in report_elements:
                self.add_statistics_wilcoxon_ratios()

            if 'wilcoxon_ratios_repeats' in report_elements:
                self.add_statistics_repeats_ratios('wilcoxon_ratios', 'Wilcoxon')

            if 'wilcoxon_areas' in report_elements:
                self.add_statistics_wilcoxon_areas()

            if 'wilcoxon_areas_repeats' in report_elements:
                self.add_statistics_repeats_areas('wilcoxon_areas', 'Wilcoxon')

            if 'chi_squared_spots' in report_elements:
                self.add_statistics_chisq_spots()

            if 'chi_squared_ratios' in report_elements:
                self.add_statistics_chisq_ratios()


    def add_title_header(self):
        """Add a header text to the report dialog.

        The header contains the name of the analysis.
        """

        # Create a label.
        header = gtk.Label()
        header.set_alignment(xalign=0, yalign=0)
        header.set_line_wrap(False)

        # Get the analysis name.
        analysis_name = self.reader.get_analysis_name()
        if not analysis_name:
            return

        # Set the header text from the title.
        header.set_markup(markup_header("Analysis Report: %s" % analysis_name))

        # Add the header to the top vertcal box.
        self.vbox_top.pack_start(header, expand=False, fill=True, padding=0)

    def add_distances(self):
        """Add the spot distances (observed + expected) to the report
        dialog.
        """

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Spot Distances")
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 150)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Observed Distances", cell, text=0)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Expected Distances", cell, text=1)
        tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        # Add the distances to the model.
        observed_distances = self.reader.get_spot_distances_observed()
        expected_distances = self.reader.get_spot_distances_expected()
        for dist_observed in observed_distances:
            liststore.append([dist_observed, expected_distances.next()])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_selections(self):
        """Add the location + species selections to the report dialog."""

        # Create a scrolled window.
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Locations and Species Selections")
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 200)
        # Add columns to the tree view.
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Locations and Species Selections", cell,
            text=0)
        tree.append_column(column)
        # To store the data, we use the TreeStore object.
        treestore = gtk.TreeStore(gobject.TYPE_STRING)

        # Add the species selection to the model.
        species_selection = self.reader.get_species_selection(slot=0)
        treeiter = treestore.append(parent=None, row=["Species selection (1)"])
        check = 0
        for spe in species_selection:
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Add the second species selection to the model.
        species_selection = self.reader.get_species_selection(slot=1)
        treeiter = treestore.append(parent=None, row=["Species selection (2)"])
        check = 0
        for spe in species_selection:
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Add the locations selection to the model.
        treeiter = treestore.append(parent=None, row=["Locations selection (1)"])
        locations_selection = self.reader.get_locations_selection(slot=0)
        check = 0
        for loc in locations_selection:
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Add the second locations selection to the model.
        treeiter = treestore.append(parent=None, row=["Locations selection (2)"])
        locations_selection = self.reader.get_locations_selection(slot=1)
        check = 0
        for loc in locations_selection:
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Set the tree model.
        tree.set_model(treestore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the scorred window to the vertical box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_species_selections(self):
        """Add the species selection(s) to the report dialog."""

        # Create a scrolled window.
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Species Selection(s)")
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 150)
        # Add columns to the tree view.
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Species Selection(s)", cell, text=0)
        tree.append_column(column)
        # To store the data, we use the TreeStore object.
        treestore = gtk.TreeStore(gobject.TYPE_STRING)

        # Add the species selection to the model.
        species_selection = self.reader.get_species_selection(slot=0)
        treeiter = treestore.append(parent=None, row=["Species selection (1)"])
        check = 0
        for spe in species_selection:
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Add the second species selection to the model.
        species_selection = self.reader.get_species_selection(slot=1)
        treeiter = treestore.append(parent=None, row=["Species selection (2)"])
        check = 0
        for spe in species_selection:
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Set the tree model.
        tree.set_model(treestore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the scorred window to the vertical box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_locations_selections(self):
        """Add the locations selection(s) to the report dialog."""

        # Create a scrolled window.
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Locations Selection(s)")
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 150)
        # Add columns to the tree view.
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Locations Selection(s)", cell, text=0)
        tree.append_column(column)
        # To store the data, we use the TreeStore object.
        treestore = gtk.TreeStore(gobject.TYPE_STRING)

        # Add the locations selection to the model.
        treeiter = treestore.append(parent=None, row=["Locations selection (1)"])
        locations_selection = self.reader.get_locations_selection(slot=0)
        check = 0
        for loc in locations_selection:
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Add the second locations selection to the model.
        treeiter = treestore.append(parent=None, row=["Locations selection (2)"])
        locations_selection = self.reader.get_locations_selection(slot=1)
        check = 0
        for loc in locations_selection:
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])
            check = 1
        if check == 0:
            treestore.remove(treeiter)

        # Set the tree model.
        tree.set_model(treestore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the scorred window to the vertical box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_plate_areas_definition(self):
        """Add the plate areas definition to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-plate-areas-definition'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 120)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Area ID", cell, text=0)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Plate Area Surfaces", cell, text=1)
        tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        # Add the distances to the model.
        spots_definition = self.reader.get_plate_areas_definition()

        for area_id, spots in sorted(spots_definition.iteritems()):
            spots = ", ".join(spots)
            liststore.append([area_id, spots])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_area_totals(self):
        """Add the species totals per plate area to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-plate-area-totals'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 120)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column = gtk.TreeViewColumn("Area ID", cell, text=0)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Observed Totals", cell, text=1)
        tree.append_column(column)

        column = gtk.TreeViewColumn("Expected Totals", cell, text=2)
        tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(gobject.TYPE_STRING,
            gobject.TYPE_STRING, gobject.TYPE_STRING)

        # Add the distances to the model.
        totals_observed = self.reader.get_area_totals_observed()
        totals_expected = self.reader.get_area_totals_expected()
        for area_id in sorted(totals_observed):
            liststore.append([area_id, totals_observed[area_id],
                totals_expected[area_id]])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_spots(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-wilcoxon-rank-sum'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('wilcoxon_spots')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                int(attr['n_positive_spots']),
                int(attr['n_plates']),
                int(attr['n']),
                float(items['p_value']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_ratios(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-wilcoxon-rank-sum'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Ratio Group','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('wilcoxon_ratios')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                int(attr['ratio_group']),
                int(attr['n_plates']),
                int(attr['n']),
                float(items['p_value']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon_areas(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-wilcoxon-rank-sum'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 220)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Plate Area','n (totals)','n (observed species)',
            'n (expected species)', 'P-value','Mean Observed','Mean Expected',
            'Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('wilcoxon_areas')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                attr['plate_area'],
                int(attr['n']),
                int(attr['n_sp_observed']),
                int(attr['n_sp_expected']),
                float(items['p_value']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_spots(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-pearson-chisq'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Chi squared','df',
            'Mean Observed','Mean Expected','Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('chi_squared_spots')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                int(attr['n_positive_spots']),
                int(attr['n_plates']),
                int(attr['n']),
                float(items['p_value']),
                float(items['chi_squared']),
                float(items['df']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_areas(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-pearson-chisq'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 100)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['P-value','Chi squared','df','Remarks']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('chi_squared_areas')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                float(items['p_value']),
                float(items['chi_squared']),
                float(items['df']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq_ratios(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-pearson-chisq'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ('Ratio Group','n (plates)',
            'n (distances)','P-value','Chi squared','df',
            'Mean Observed','Mean Expected','Remarks')

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('chi_squared_ratios')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = make_remarks(items,attr)

            # Add all result items to the tree model.
            liststore.append([
                int(attr['ratio_group']),
                int(attr['n_plates']),
                int(attr['n']),
                float(items['p_value']),
                float(items['chi_squared']),
                float(items['df']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_normality(self):
        """Add the statistic results for normality to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-results-shapiro-wilk'))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 250)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        columns = ['Positive Spots','n (distances)','P-value','W',
            'Method','Normality']

        for i, name in enumerate(columns):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics_normality()

        for attr,items in statistics:
            null_hypothesis = "True"
            if float(items['p_value']) < setlyze.config.cfg.get('normality-alpha'):
                null_hypothesis = "False"

            liststore.append([
                int(attr['n_positive_spots']),
                int(attr['n']),
                float(items['p_value']),
                float(items['w']),
                null_hypothesis,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_areas(self, element_name, testname):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text(
            't-significance-results-repeats', testname))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 220)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Plate Area','n (totals)','n (observed species)',
            'n (significant)','n (non-significant)','n (preference)',
            'n (rejection)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        # Add the results to the model.
        statistics = self.reader.get_statistics(element_name)
        statistics_repeats = self.reader.get_statistics_repeats(element_name)

        for attr,items in statistics:
            plate_area = attr['plate_area']
            liststore.append([
                plate_area,
                int(attr['n']),
                int(attr['n_sp_observed']),
                int(statistics_repeats[plate_area]['n_significant']),
                int(int(statistics_repeats['repeats']) - int(statistics_repeats[plate_area]['n_significant'])),
                int(statistics_repeats[plate_area]['n_preference']),
                int(statistics_repeats[plate_area]['n_rejection']),
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_spots(self, element_name, testname):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-significance-results-repeats', testname))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 270)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Positive Spots','n (plates)','n (distances)',
            'n (significant)','n (non-significant)','n (attraction)',
            'n (repulsion)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        # Add the results to the model.
        statistics = self.reader.get_statistics(element_name)
        statistics_repeats = self.reader.get_statistics_repeats(element_name)

        for attr,items in statistics:
            n_spots = attr['n_positive_spots']

            liststore.append([
                n_spots,
                int(attr['n_plates']),
                int(attr['n']),
                int(statistics_repeats[n_spots]['n_significant']),
                int(int(statistics_repeats['repeats']) - int(statistics_repeats[n_spots]['n_significant'])),
                int(statistics_repeats[n_spots]['n_attraction']),
                int(statistics_repeats[n_spots]['n_repulsion']),
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_ratios(self, element_name, testname):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander(setlyze.locale.text('t-significance-results-repeats', testname))
        expander.set_expanded(False)
        # Add the scrolled window to the expander.
        expander.add(scrolled_window)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, 190)
        # Set horizontal rules, makes it easier to read items.
        tree.set_rules_hint(True)

        # Add columns to the tree view.
        cell = gtk.CellRendererText()

        column_names = ['Ratio Group','n (plates)','n (distances)',
            'n (significant)','n (non-significant)','n (attraction)',
            'n (repulsion)']

        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, cell, text=i)
            column.set_sort_column_id(i) # Make column sortable.
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            gobject.TYPE_INT,
            )

        # Add the results to the model.
        statistics = self.reader.get_statistics(element_name)
        statistics_repeats = self.reader.get_statistics_repeats(element_name)

        for attr,items in statistics:
            ratio_group = attr['ratio_group']

            liststore.append([
                ratio_group,
                int(attr['n_plates']),
                int(attr['n']),
                int(statistics_repeats[ratio_group]['n_significant']),
                int(int(statistics_repeats['repeats']) - int(statistics_repeats[ratio_group]['n_significant'])),
                int(statistics_repeats[ratio_group]['n_attraction']),
                int(statistics_repeats[ratio_group]['n_repulsion']),
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

class SelectExportElements(gtk.Dialog):
    """Display a dialog for allowing the user to select which report
    elements to export. The argument `reader` is an instance of
    :class:`setlyze.report.ReportReader`.
    """

    def __init__(self, reader):
        super(SelectExportElements, self).__init__()
        self.set_report_reader(reader)

        self.set_size_request(400, -1)
        self.set_border_width(10)
        self.set_keep_above(True)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_title("Select Report Elements to Export")
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        self.set_has_separator(True)

        # Add widgets to the GTK dialog.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def set_report_reader(self, reader):
        """Set the report reader."""
        self.reader = reader

    def get_selected_elements(self):
        """Return a list with the names of the selected report
        elements.
        """
        selected = []
        for element,button in self.check_buttons.iteritems():
            if button.get_active():
                selected.append(element)
        return selected

    def create_layout(self):
        """Add widgets to the dialog."""

        # Get gtk.Dialog's vertical box.
        vbox = self.get_content_area()

        # Create a label.
        self.descr_label = gtk.Label()
        self.descr_label.set_line_wrap(True)
        self.descr_label.set_text("Please check the elements to export.")
        self.descr_label.set_alignment(xalign=0, yalign=0)
        vbox.pack_start(self.descr_label, expand=False, fill=False, padding=5)

        # Create a dictionary of all known report elements and their
        # name.
        element_names = {'spot_distances': "Spot Distances",
            'location_selections': "Locations Selection(s)",
            'species_selections': "Species Selection(s)",
            'plate_areas_definition': setlyze.locale.text('t-plate-areas-definition'),
            'area_totals': setlyze.locale.text('t-plate-area-totals'),
            'wilcoxon_spots': setlyze.locale.text('t-results-wilcoxon-rank-sum'),
            'wilcoxon_ratios': setlyze.locale.text('t-results-wilcoxon-rank-sum'),
            'wilcoxon_areas': setlyze.locale.text('t-results-wilcoxon-rank-sum'),
            'wilcoxon_spots_repeats': setlyze.locale.text(
                't-significance-results-repeats', 'Wilcoxon'),
            'wilcoxon_ratios_repeats': setlyze.locale.text(
                't-significance-results-repeats', 'Wilcoxon'),
            'wilcoxon_areas_repeats': setlyze.locale.text(
                't-significance-results-repeats', 'Wilcoxon'),
            'chi_squared_spots': setlyze.locale.text(
                't-results-pearson-chisq'),
            'chi_squared_ratios': setlyze.locale.text(
                't-results-pearson-chisq'),
            'chi_squared_areas': setlyze.locale.text(
                't-results-pearson-chisq'),
            }

        # Create check buttons.
        self.check_buttons = {}
        for element in self.reader.get_child_names():
            # Don't add the 'statistics' element, but do add its sub
            # elements.
            if element == 'statistics':
                stats = self.reader.get_element(self.reader.doc, 'statistics')
                for element in self.reader.get_child_names(stats):
                    if element in self.check_buttons:
                        continue
                    self.check_buttons[element] = gtk.CheckButton(element_names[element])
                    self.check_buttons[element].set_active(True)
                    vbox.pack_start(self.check_buttons[element],
                        expand=False, fill=True, padding=3)
                continue
            # Group some elements in one element.
            elif element == 'spot_distances_observed':
                element  = 'spot_distances'
            elif element == 'spot_distances_expected':
                element  = 'spot_distances'
            elif element == 'area_totals_observed':
                element  = 'area_totals'
            elif element == 'area_totals_expected':
                element  = 'area_totals'
            # Skip this element.
            elif element == 'analysis':
                continue

            # Don't elements that are already in the list.
            if element in self.check_buttons:
                continue

            self.check_buttons[element] = gtk.CheckButton(element_names[element])
            self.check_buttons[element].set_active(True)
            vbox.pack_start(self.check_buttons[element], expand=False,
                fill=True, padding=3)

        # Uncheck some 'not-so-interesting' report elements.
        uncheck = ('spot_distances')
        for element, button in self.check_buttons.iteritems():
            if element in uncheck:
                button.set_active(False)

class Preferences(gtk.Window):
    """Display a preferences dialog which allows the user to configure
    the application.
    """

    def __init__(self):
        super(Preferences, self).__init__()

        self.set_title("Preferences")
        self.set_size_request(-1, -1)
        self.set_border_width(10)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_resizable(True)
        self.set_keep_above(True)

        # Construct the layout.
        self.create_layout()

    def create_layout(self):
        """Construct the layout."""

        # Create table container
        table = gtk.Table(rows=5, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(5)

        # Create a label
        label_alpha_level = gtk.Label("Alpha level (α) for statistical tests:")
        label_alpha_level.set_justify(gtk.JUSTIFY_FILL)
        label_alpha_level.set_alignment(xalign=0, yalign=0)
        table.attach(label_alpha_level, left_attach=0, right_attach=1,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create an entry for the alpha level.
        self.entry_alpha_level = gtk.Entry(max=5)
        self.entry_alpha_level.set_text(str(setlyze.config.cfg.get('alpha-level')))
        self.entry_alpha_level.set_width_chars(5)

        align1 = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        align1.add(self.entry_alpha_level)

        table.attach(align1, left_attach=1, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a label
        label_test_repeats = gtk.Label("Number of repeats for statistical tests:")
        label_test_repeats.set_justify(gtk.JUSTIFY_FILL)
        label_test_repeats.set_alignment(xalign=0, yalign=0)
        table.attach(label_test_repeats, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create an entry for test repeats.
        self.entry_test_repeats = gtk.Entry(max=0)
        self.entry_test_repeats.set_text(str(setlyze.config.cfg.get('test-repeats')))
        self.entry_test_repeats.set_width_chars(7)

        align3 = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
        align3.add(self.entry_test_repeats)

        table.attach(align3, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL|gtk.SHRINK,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Put a separator above the buttons.
        separator = gtk.HSeparator()
        table.attach(separator, left_attach=0, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create a help button.
        button_help = gtk.Button(stock=gtk.STOCK_HELP)
        button_help.connect("clicked", on_help, 'preferences-dialog')

        # Put the buttons in a horizontal button box.
        button_box_l = gtk.HButtonBox()
        button_box_l.set_layout(gtk.BUTTONBOX_START)
        button_box_l.pack_start(button_help, expand=True, fill=True, padding=0)

        # Add the about button to the table.
        table.attach(button_box_l, left_attach=0, right_attach=1,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Continue button.
        button_ok = gtk.Button(stock=gtk.STOCK_OK)
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_ok)

        # Quit button.
        button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_cancel.set_size_request(70, -1)
        button_cancel.connect("clicked", self.on_cancel)

        # Put the buttons in a horizontal box.
        button_box_r = gtk.HButtonBox()
        button_box_r.set_layout(gtk.BUTTONBOX_END)
        button_box_r.set_spacing(5)
        button_box_r.pack_start(button_cancel, expand=True, fill=True, padding=0)
        button_box_r.pack_start(button_ok, expand=True, fill=True, padding=0)

        # Add the aligned button box to the table.
        table.attach(button_box_r, left_attach=1, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the table to the main window.
        self.add(table)

        # Make it visible.
        self.show_all()

    def on_ok(self, widget, data=None):
        """Save new settings and close the preferences dialog."""
        if not self.set_alpha_level():
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Invalid alpha level")
            dialog.format_secondary_text( setlyze.locale.text('invalid-alpha-level') )
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()

            # Don't destroy the Preferences dialog if saving setting failed.
            return

        if not self.set_test_repeats():
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Invalid number of repeats")
            dialog.format_secondary_text( setlyze.locale.text('invalid-repeats-number') )
            dialog.set_position(gtk.WIN_POS_CENTER)
            response = dialog.run()
            dialog.destroy()

            # Don't destroy the Preferences dialog if saving setting failed.
            return

        self.destroy()

    def set_alpha_level(self):
        """Set the new alpha level for statistical test. Return True if
        succeeded, or False if failed."""
        try:
            alpha_level = float(self.entry_alpha_level.get_text())
        except:
            # Saving setting failed.
            return False

        if not 0.0 < alpha_level < 1.0:
            # Saving setting failed.
            return False

        # Set the new value.
        setlyze.config.cfg.set('alpha-level', alpha_level)

        # Saving setting succeeded.
        return True

    def set_test_repeats(self):
        """Set the new value for the number of repeats for statistical tests.
        Return True if succeeded, or False if failed."""
        try:
            test_repeats = int(self.entry_test_repeats.get_text())
        except:
            # Saving setting failed.
            return False

        if not test_repeats > 1:
            # Saving setting failed.
            return False

        # Set the new value.
        setlyze.config.cfg.set('test-repeats', test_repeats)

        # Saving setting succeeded.
        return True

    def on_cancel(self, widget, data=None):
        """Close the preferences dialog."""
        self.destroy()

    def on_about(self, widget, data=None):
        """Display SETLyze's about dialog."""
        About()

class About(gtk.AboutDialog):
    """Display SETLyze's about dialog."""

    def __init__(self):
        super(About, self).__init__()

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

        # Load the logo file.
        if setlyze.std.we_are_frozen():
            image_path = os.path.join(setlyze.std.module_path(),
                'images/setlyze-logo.png')
        else:
            image_path = pkg_resources.resource_filename('setlyze',
                'images/setlyze-logo.png')
        logo = gtk.gdk.pixbuf_new_from_file(image_path)

        self.set_position(gtk.WIN_POS_CENTER)
        self.set_program_name("SETLyze")
        self.set_version(__version__)
        self.set_copyright(__copyright__)
        self.set_authors(["Project Leader/Contact Person:\n"
            "\tArjan Gittenberger <gittenberger@gimaris.com>",
            "Application Developers:\n"
            "\tJonathan den Boer",
            "\tSerrano Pereira <serrano.pereira@gmail.com>",
            "\tAdam van Adrichem <a.v.adrichem@gmail.com>",
            "\tFedde Schaeffer <fedde.schaeffer@gmail.com>"])
        self.set_comments("A tool for analyzing the settlement of species \non SETL plates.")
        self.set_artists(["Serrano Pereira <serrano.pereira@gmail.com>"])
        self.set_license(license)
        self.set_website("http://www.gimaris.com/")
        self.set_logo(logo)
        self.run()
        self.destroy()
