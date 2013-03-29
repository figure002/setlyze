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
__version__ = "0.3"
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
    text = "<span size='x-large' weight='bold'>%s</span>" % (text)
    return text

def markup_subheader(text):
    """Apply Pango markup to `text` to make it look like a header."""
    text = "<span size='large' weight='bold'>%s</span>" % (text)
    return text

class SelectAnalysis(object):
    """Display a window that allows the user to select an analysis.

    Design Part: 1.86
    """

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/select_analysis.glade'))

        # Get some GTK objects.
        self.window = self.builder.get_object('window_select_analysis')
        self.radio_spot_pref = self.builder.get_object('radio_spot_pref')
        self.radio_attraction_intra = self.builder.get_object('radio_attraction_intra')
        self.radio_attraction_inter = self.builder.get_object('radio_attraction_inter')
        self.radio_batch_mode = self.builder.get_object('radio_batch_mode')
        self.frame_descr = self.builder.get_object('frame_descr')
        self.label_descr = self.builder.get_object('label_descr')
        image_logo = self.builder.get_object('image_logo')

        # Load an image for the logo.
        if setlyze.std.we_are_frozen():
            image_path = os.path.join(setlyze.std.module_path(),
                'images/setlyze-logo.png')
        else:
            image_path = pkg_resources.resource_filename('setlyze',
                'images/setlyze-logo.png')
        image_logo.set_from_file(image_path)

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Updated the analysis description.
        self.on_toggled()

        # Handle application signals.
        self.signal_handlers = {
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.on_analysis_started),
            'analysis-closed': setlyze.std.sender.connect('analysis-closed', self.on_analysis_closed),
            'local-db-created': setlyze.std.sender.connect('local-db-created', self.on_continue),
        }

    def show(self, widget=None, data=None):
        """Show the window."""
        self.window.show()

    def hide(self, widget=None, data=None):
        """Hide the window."""
        self.window.hide()
        # Prevent default action.
        return True

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

    def on_toggled(self, radiobutton=None):
        """Update the description frame."""
        if self.radio_spot_pref.get_active():
            self.frame_descr.set_label("Spot preference")
            self.label_descr.set_text(setlyze.locale.text('analysis1-descr'))
        elif self.radio_attraction_intra.get_active():
            self.frame_descr.set_label("Attraction within species")
            self.label_descr.set_text(setlyze.locale.text('analysis2-descr'))
        elif self.radio_attraction_inter.get_active():
            self.frame_descr.set_label("Attraction between species")
            self.label_descr.set_text(setlyze.locale.text('analysis3-descr'))
        elif self.radio_batch_mode.get_active():
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
        if self.radio_spot_pref.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'spot_preference')
        elif self.radio_attraction_intra.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'attraction_intra')
        elif self.radio_attraction_inter.get_active():
            setlyze.std.sender.emit('on-start-analysis', 'attraction_inter')
        elif self.radio_batch_mode.get_active():
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
            # Use the existing database.
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
            elif source == "data-files":
                source_str = "local data files"
            else:
                raise ValueError("Unknown data source '%s'." % source)

            message = ("The SETL data from the last session is being loaded. "
                "This data was loaded on %s from %s.") % (date, source_str)

            # Show a dialog with the message.
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_OK,
                message_format="Using saved data")
            dialog.format_secondary_text(message)
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()

            # Prevent a new database from being created.
            setlyze.config.cfg.set('data-source', source)
            setlyze.config.cfg.set('make-new-db', False)
            setlyze.config.cfg.set('has-local-db', True)

            # Try again...
            self.on_continue()
        else:
            # No database file was found. Create a new local database file.
            self.on_make_local_db()

    def on_make_local_db(self):
        """Make a new local database."""

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading SETL Data",
            description="Please wait while the data from the SETL database is being loaded...")

        # Make the local database.
        t = setlyze.database.MakeLocalDB(pd)
        t.start()

class SelectBatchAnalysis(object):
    """Display a window that allows the user to select an analysis for batch mode."""

    def __init__(self):
        # Get some GTK objects.
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/select_batch_analysis.glade'))
        self.dialog = self.builder.get_object('dialog_select_analysis')
        self.radio_ana_spot_pref = self.builder.get_object('radio_ana_spot_pref')
        self.radio_ana_attraction_intra = self.builder.get_object('radio_ana_attraction_intra')
        self.radio_ana_attraction_inter = self.builder.get_object('radio_ana_attraction_inter')
        self.frame_descr = self.builder.get_object('frame_descr')
        self.label_descr = self.builder.get_object('label_descr')
        self.chooser_save_path = self.builder.get_object('chooser_save_path')

        # Handle window signals.
        self.dialog.connect('delete-event', self.hide)

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Updated the analysis description.
        self.on_toggled()

        # Handle application signals.
        self.signal_handlers = {
            'beginning-analysis': setlyze.std.sender.connect('beginning-analysis', self.hide),
        }

    def show(self, widget=None, data=None):
        """Show the window."""
        self.dialog.show()

    def hide(self, widget=None, data=None):
        """Hide the window."""
        self.dialog.hide()
        # Prevent default action.
        return True

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

    def on_ok(self, button):
        """Send the `on-start-analysis` signal with the selected analysis as
        signal attribute.
        """
        if self.radio_ana_spot_pref.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'spot_preference')
        elif self.radio_ana_attraction_intra.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'attraction_intra')
        elif self.radio_ana_attraction_inter.get_active():
            setlyze.std.sender.emit('batch-analysis-selected', 'attraction_inter')

    def on_close(self, button):
        """Go back to the main window."""
        # Hide the window.
        self.hide()
        # Emit the signal that the Back button was pressed.
        setlyze.std.sender.emit('select-batch-analysis-window-back')
        # Prevent default action of the close button.
        return False

class SelectionWindow(gtk.Window):
    """Super class for :class:`SelectLocations` and :class:`SelectSpecies`."""

    def __init__(self, title, description, width, slot):
        super(SelectionWindow, self).__init__()
        self.header = title
        self.description = description
        self.width = width
        self.selection = []
        self.selection_minimum = 1
        self.selection_minimum_msg = ("No items were selected. Please "
                "select at least one item from the list.")
        self.set_save_slot(slot)
        self.back_signal = 'dialog-back'
        self.saved_signal = 'selection-saved'

        self.set_icon_name('setlyze')
        self.set_title(title)
        self.set_size_request(self.width, 500)
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

    def set_selection_minimum(self, n, message):
        """Set the minimum number of options `n` that must be selected.

        Display an error message containing the message `message` when too
        few items are selected.
        """
        self.selection_minimum = int(n)
        self.selection_minimum_msg = message

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

    def on_back(self, widget, data=None):
        """Destroy the dialog and send the back signal.

        The back signal is set in attribute `back_signal`. The save slot
        (attribute `save_slot`) is an attribute of the signal.

        This function is called when the user presses the Back button in
        a species selection window.

        Design Part: 1.46
        """
        self.destroy()
        self.unset_signal_handlers()
        setlyze.std.sender.emit(self.back_signal, self.save_slot)

    def on_continue(self, button):
        """Emit the selection saved signal and close the dialog.

        The saved signal is set in attribute `saved_signal`. The selection
        `selection` and the save slot `slot` are attributes of the signal.

        Before emitting the signal, check if the selection is valid. If not,
        display a message dialog. If yes, call :meth:`emit_signal` to emit
        the signal (that method must be set in a sub class), then close the
        selection dialog.

        Design Part: 1.44
        """

        # Display an error dialog if too few items were selected.
        if len(self.selection) < self.selection_minimum:
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Not enough items selected")
            dialog.format_secondary_text("%s\n\n"
                "Tip: Hold Ctrl or Shift to select multiple items. To "
                "select all items, press Ctrl+A." % self.selection_minimum_msg)
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return

        # Emit the signal. This method is present in one of the sub classes.
        setlyze.std.sender.emit(self.saved_signal, self.selection, self.save_slot)

        # Destroy the signal handlers and close this window.
        self.unset_signal_handlers()
        self.destroy()

    def on_changed(self, treeview):
        """Save the selection from a gtk.TreeView `treeview`.

        This method is called whenever the selection changes.
        """
        (model, rows) = treeview.get_selected_rows()
        self.selection = []
        for row in rows:
            iter = model.get_iter(row)
            # We use column=0, because the first column in the TreeModels
            # contain the ID, which we'll need for the SQL queries.
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
            description="Select the locations:", width=400, slot=0):
        super(SelectLocations, self).__init__(title, description, width, slot)
        self.info_key = 'info-loc-selection'
        self.back_signal = 'locations-dialog-back'
        self.saved_signal = 'locations-selection-saved'

    def create_model(self):
        """Create a tree model for the locations.

        Design Part: 1.42
        """
        db = setlyze.database.get_database_accessor()
        self.store = gtk.ListStore(gobject.TYPE_INT, gobject.TYPE_STRING)
        for id,name in db.get_locations():
            self.store.append([id,name])
        self.model = gtk.TreeModelSort(self.store)
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

    def __init__(self, locations, title="Species Selection",
            description="Select the species:", width=600, slot=0):
        self.locations = locations
        super(SelectSpecies, self).__init__(title, description, width, slot)
        self.back_signal = 'species-dialog-back'
        self.saved_signal = 'species-selection-saved'
        self.info_key = 'info-spe-selection'

    def create_model(self):
        """Create a model for the tree view from the species IDs and
        names.

        Design Part: 1.43
        """
        db = setlyze.database.AccessLocalDB()
        self.store = gtk.ListStore(gobject.TYPE_INT,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        for id,common,latin in db.get_species(self.locations):
            self.store.append([id,common,latin])

        self.model = gtk.TreeModelSort(self.store)
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
        # TreeModel. Column 1 contains the species names (common).
        column = gtk.TreeViewColumn("Species (common)", renderer_text, text=1)
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
        self.set_icon_name('setlyze')
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
        """Emit the "plate-areas-defined" signal.

        First checks if the user made a correct definition. If yes, normalize
        the definition and emit the signal with the definition as an attribute.
        """

        # Get the user selected plate areas definition.
        definition = self.get_selection()

        # Check if the definition is any good.
        if not self.iscorrect(definition):
            return

        # Then close this window.
        self.destroy()

        # Normalize the definition.
        definition = self.normalize(definition)

        # Emit the signal that the plate areas are defined.
        setlyze.std.sender.emit('plate-areas-defined', definition)

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

class ChangeDataSource(object):
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
        # Get some GTK objects.
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/load_data.glade'))
        self.dialog = self.builder.get_object('dialog_load_data')
        self.notebook = self.builder.get_object('notebook')
        self.button_cancel = self.builder.get_object('button_cancel')
        self.button_ok = self.builder.get_object('button_ok')
        self.filechooserbutton_loc = self.builder.get_object('filechooserbutton_loc')
        self.filechooserbutton_spe = self.builder.get_object('filechooserbutton_spe')
        self.filechooserbutton_rec = self.builder.get_object('filechooserbutton_rec')
        self.filechooserbutton_pla = self.builder.get_object('filechooserbutton_pla')

        # Create file filterz for the file chooser.
        filefilter_all = gtk.FileFilter()
        filefilter_all.set_name("All supported")
        filefilter_all.add_mime_type("text/csv")
        filefilter_all.add_mime_type("application/vnd.ms-excel")
        filefilter_all.add_pattern("*.csv")
        filefilter_all.add_pattern("*.txt")
        filefilter_all.add_pattern("*.xls")

        filefilter_csv = gtk.FileFilter()
        filefilter_csv.set_name("Comma Separated File (*.csv, *.txt)")
        filefilter_csv.add_mime_type("text/csv")
        filefilter_csv.add_pattern("*.csv")
        filefilter_csv.add_pattern("*.txt")

        filefilter_xls = gtk.FileFilter()
        filefilter_xls.set_name("Excel File (*.xls)")
        filefilter_xls.add_mime_type("application/vnd.ms-excel")
        filefilter_xls.add_pattern("*.xls")

        # Set the filters.
        self.filechooserbutton_loc.add_filter(filefilter_all)
        self.filechooserbutton_loc.add_filter(filefilter_csv)
        self.filechooserbutton_loc.add_filter(filefilter_xls)
        self.filechooserbutton_pla.add_filter(filefilter_all)
        self.filechooserbutton_pla.add_filter(filefilter_csv)
        self.filechooserbutton_pla.add_filter(filefilter_xls)
        self.filechooserbutton_rec.add_filter(filefilter_all)
        self.filechooserbutton_rec.add_filter(filefilter_csv)
        self.filechooserbutton_rec.add_filter(filefilter_xls)
        self.filechooserbutton_spe.add_filter(filefilter_all)
        self.filechooserbutton_spe.add_filter(filefilter_csv)
        self.filechooserbutton_spe.add_filter(filefilter_xls)

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

        # Bind handles to application signals.
        self.signal_handlers = {}
        self.set_signal_handlers()

        # Display all widgets.
        self.dialog.show_all()

    def set_signal_handlers(self):
        """Respond to signals emitted by the application."""
        self.signal_handlers = {
            # Show an epic fail message when import fails.
            'file-import-failed': setlyze.std.sender.connect('file-import-failed', self.on_import_failed),
            # Make sure the above handle is disconnected when loading new SETL data succeeds.
            'local-db-created': setlyze.std.sender.connect('local-db-created', self.unset_signal_handlers)
        }

    def unset_signal_handlers(self, sender=None, data=None):
        """Disconnect all signal handlers created by this class."""
        for handler in self.signal_handlers.values():
            setlyze.std.sender.disconnect(handler)

    def update_working_folder(self, chooser, data=None):
        """Set the working folder for the file choosers to the folder
        where the first data file was selected from.

        This way the user doesn't have to navigate to the same folder
        multiple times.
        """
        path = chooser.get_filename()
        if path:
            folder = os.path.dirname(path)
            self.filechooserbutton_spe.set_current_folder(folder)
            self.filechooserbutton_rec.set_current_folder(folder)
            self.filechooserbutton_pla.set_current_folder(folder)

    def on_button_ok_clicked(self, widget, data=None):
        """Save the paths to the CSV files, set the new value for the
        data source configuration, load the SETL data from the CSV file
        into the local database, and close the dialog.
        """

        # Check if all files are selected.
        if not (self.filechooserbutton_loc.get_filename() and \
            self.filechooserbutton_spe.get_filename() and \
            self.filechooserbutton_rec.get_filename() and \
            self.filechooserbutton_pla.get_filename()):
            dialog = gtk.MessageDialog(parent=None, flags=0,
                type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
                message_format="Not all data files selected")
            dialog.format_secondary_text("Not all data files were selected. "
                "Four data files are required as input. See the user manual "
                "for more information. Please select all four files and try again.")
            dialog.set_position(gtk.WIN_POS_CENTER)
            dialog.run()
            dialog.destroy()
            return False

        # Save the paths.
        setlyze.config.cfg.set('localities-file',
            self.filechooserbutton_loc.get_filename() )
        setlyze.config.cfg.set('species-file',
            self.filechooserbutton_spe.get_filename() )
        setlyze.config.cfg.set('records-file',
            self.filechooserbutton_rec.get_filename() )
        setlyze.config.cfg.set('plates-file',
            self.filechooserbutton_pla.get_filename() )

        # Let the application know that we are now using user selected data files.
        setlyze.config.cfg.set('data-source', 'data-files')

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading data",
            description="Please wait while the data is being loaded...")

        # Make a new local database.
        t = setlyze.database.MakeLocalDB(pd)
        t.start()

        # Close the dialog.
        self.dialog.destroy()

    def on_import_failed(self, sender, error, data=None):
        """Display an error message showing the user that importing SETL data
        from the selected CSV or XLS files failed.
        """
        self.unset_signal_handlers()

        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
            message_format="Loading SETL data failed")
        dialog.format_secondary_text("Failed to load SETL data from one of the "
            "selected data files. This is probably caused by an incorrect "
            "format of the input file. Please see the user manual for the "
            "supported formats.\n\n"
            "The error returned was: %s" % error)
        dialog.set_position(gtk.WIN_POS_CENTER)
        dialog.run()
        dialog.destroy()

        # Returning True indicates that the event has been handled, and that
        # it should not propagate further.
        return True

    def on_button_cancel_clicked(self, widget, data=None):
        """Close the dialog."""
        self.unset_signal_handlers()
        self.dialog.destroy()

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
        self.set_icon_name('setlyze')
        self.set_size_request(400, -1)
        self.set_title(title)
        self.set_border_width(0)
        self.set_deletable(True)
        self.set_resizable(False)
        self.set_modal(False)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.description = description

        # Handle window signals.
        self.connect('delete-event', self.on_cancel)

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
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO,
                message_format="Cancel the analysis?")
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        dialog.destroy()

        if response == gtk.RESPONSE_NO:
            return True

        logging.info("Cancel button is pressed")
        self.destroy()
        setlyze.std.sender.emit('analysis-canceled')

        # Return True to stop other handlers from being invoked for the
        # 'delete-event' signal. This prevents the GTK window that calles
        # this function from closing anyway.
        return True

class Report(object):
    """Display a dialog visualizing the elements in a report object.

    The argument `report` must be an instance of
    :class:`setlyze.report.Report`.
    """

    def __init__(self, report, header="Report"):
        self.report = None
        self.set_report(report)

        # Get some GTK objects.
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/report.glade'))
        self.window = self.builder.get_object('window_report')
        self.toolbutton_save_all = self.builder.get_object('toolbutton_save_all')
        toolbutton_help = self.builder.get_object('toolbutton_help')
        self.vbox_top = self.builder.get_object('vbox_top')
        self.vbox_elements = self.builder.get_object('vbox_elements')
        self.label_header = self.builder.get_object('label_header')
        self.label_subheader = self.builder.get_object('label_subheader')

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)
        self.window.connect('delete-event', on_quit)

        # Modify some widgets.
        toolbutton_help.connect('clicked', on_help, 'analysis-report-dialog')

        # Set the report header.
        if header:
            self.set_header(header)

        # Add report elements.
        self.add_report_elements()

        # Display all widgets.
        self.window.show_all()

    def set_report(self, report):
        """Set the report object `report`."""
        if isinstance(report, setlyze.report.Report):
            self.report = report
        else:
            ValueError("Report must be an instance of setlyze.report.Report")

    def set_header(self, text):
        """Set the header of the report dialog to `text`."""
        self.label_header.set_markup(markup_header(text))

    def set_subheader(self, text):
        """Set the subheader of the report dialog to `text`."""
        self.label_subheader.set_markup(markup_subheader(text))

    def on_close(self, button):
        """Close the dialog and emit the `report-dialog-closed` signal."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_OK_CANCEL,
            message_format="Unsaved results will be lost. Continue to the main window?")
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            self.window.destroy()
            setlyze.std.sender.emit('report-dialog-closed')
        dialog.destroy()

    def on_save(self, button):
        """Display a dialog that allows the user to save the report to
        a file.
        """
        chooser = gtk.FileChooserDialog(title="Save Analysis Report As...",
            parent=None,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_SAVE, gtk.RESPONSE_OK),
            backend=None)
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_do_overwrite_confirmation(True)

        # Create a filter for the file chooser.
        rst_filter = gtk.FileFilter()
        rst_filter.set_name("reStructuredText (*.rst)")
        rst_filter.add_pattern("*.rst")

        chooser.add_filter(rst_filter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            # Get the filename to which the data should be exported.
            path = chooser.get_filename()

            # Get the name of the selected file type.
            filter_name = chooser.get_filter().get_name()

            # File type = reStructuredText
            if "*.rst" in filter_name:
                setlyze.report.export(self.report, path, 'rst')

        # Close the filechooser.
        chooser.destroy()

    def on_save_all(self, button):
        """Emit the 'save-individual-reports' signal."""
        setlyze.std.sender.emit('save-individual-reports')

    def on_repeat(self, button):
        """Emit the 'repeat-analysis' signal."""
        setlyze.std.sender.emit('repeat-analysis')

    def add_report_elements(self):
        """Add the report elements present in the report object to the
        report dialog.
        """
        if not self.report:
            return

        if hasattr(self.report, 'analysis_name'):
            self.set_subheader(self.report.analysis_name)

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

        if 'plate_areas_summary' in self.report.statistics:
            for stats in self.report.statistics['plate_areas_summary']:
                self.add_plate_areas_summary(stats)

        if 'positive_spots_summary' in self.report.statistics:
            for stats in self.report.statistics['positive_spots_summary']:
                self.add_positive_spots_summary(stats)

        if 'ratio_groups_summary' in self.report.statistics:
            for stats in self.report.statistics['ratio_groups_summary']:
                self.add_ratio_groups_summary(stats)

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
            for spe_id, spe in species.iteritems():
                species = "%s (%s)" % (spe['name_latin'], spe['name_common'])
                treestore.append(parent=treeiter, row=[species])
                check = 1
            if not check:
                treestore.remove(treeiter)

        # Add the locations selection to the model.
        for i, locations in enumerate(locations_selections, start=1):
            treeiter = treestore.append(parent=None, row=["Locations selection (%d)" % i])
            check = 0
            for loc_id, loc in locations.iteritems():
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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_areas(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeated)" % statistics['attr']['method'])
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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_spots(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeated)" % statistics['attr']['method'])
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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_repeats_ratios(self, statistics):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("%s (repeated)" % statistics['attr']['method'])
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
        self.vbox_elements.pack_start(expander, expand=False, fill=True, padding=0)

    def add_plate_areas_summary(self, statistics):
        """Add a summary report for spot preference to the displayer.

        This report cannot be combined with other report elements in the
        in the displayer.

        Data is passed in the following format ::

            {
                'attr': {
                    'columns': ('Species', 'n (plates)', 'A', 'B', 'C', 'D', 'A+B', 'C+D', 'A+B+C', 'B+C+D', 'Chi sq')
                },
                'results': [
                    ['Obelia dichotoma', 166, 'p', 'n', 'r', 'r', 'p', 'r', 'n', 'r', 's'],
                    ['Obelia geniculata', 88, 'n', 'n', 'r', 'n', 'n', 'r', 'n', 'r', 's'],
                    ...
                ]
            }
        """
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, -1)
        tree.set_rules_hint(True)

        # Create cell renderers.
        render_text = gtk.CellRendererText()
        render_toggle = gtk.CellRendererToggle()

        # Add columns to the tree view.
        column_names = statistics['attr']['columns']
        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, render_text, text=i)
            column.set_sort_column_id(i)
            if i == 0: column.set_expand(True)
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
        )

        for row in statistics['results']:
            liststore.append(row)

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox_elements.pack_start(scrolled_window, expand=True, fill=True, padding=0)

    def add_positive_spots_summary(self, statistics):
        """Add a summary report for spot preference to the displayer.

        This report cannot be combined with other report elements in the
        in the displayer.

        Data is passed in the following format ::

            {
                'attr': {
                    'columns': ('Species', 'n (plates)', 'Wilcoxon 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', 'Chi sq 2-24', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24')
                },
                'results': [
                    ['Obelia dichotoma', 143, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n', 's', 's', 's', 's', 's', 's', 's', 's', 's', 's', 'n', 's', 'n', 's', 's', 's', 'n', 'n', None, 'n', 'n', 'n', 'n', 'n'],
                    ['Obelia geniculata', 62, 'r', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', None, 'n', 'r', 'n', None, 'n', 'r', None, None, None, None, None, None, None, None, 's', 's', 'n', 's', 'n', 'n', 'n', 's', 's', None, 's', 's', 's', None, 's', 's', None, None, None, None, None, None, None, None],
                    ...
                ]
            }
        """
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, -1)
        tree.set_rules_hint(True)

        # Create cell renderers.
        render_text = gtk.CellRendererText()
        render_toggle = gtk.CellRendererToggle()

        # Add columns to the tree view.
        column_names = statistics['attr']['columns']
        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, render_text, text=i)
            column.set_sort_column_id(i)
            if i == 0: column.set_expand(True)
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
        )

        for row in statistics['results']:
            liststore.append(row)

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox_elements.pack_start(scrolled_window, expand=True, fill=True, padding=0)

    def add_ratio_groups_summary(self, statistics):
        """Add a summary report for spot preference to the displayer.

        This report cannot be combined with other report elements in the
        in the displayer.

        Data is passed in the following format ::

            {
                'attr': {
                    'columns': ('Species A', 'Species B', 'n (plates)', 'Wilcoxon 1-5', '1', '2', '3', '4', '5', 'Chi sq 1-5', '1', '2', '3', '4', '5')
                },
                'results': [
                    ['Obelia dichotoma', 'Obelia geniculata', 12, 'n', 'r', 'a', 'n', None, None, 'n', 's', 's', 'n', None, None],
                    ['Obelia dichotoma', 'Obelia longissima', 73, 'r', 'r', 'r', 'r', 'r', 'r', 's', 's', 's', 's', 's', 's'],
                    ...
                ]
            }
        """
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create a TreeView for the selections.
        tree = gtk.TreeView()
        tree.set_size_request(-1, -1)
        tree.set_rules_hint(True)

        # Create cell renderers.
        render_text = gtk.CellRendererText()
        render_toggle = gtk.CellRendererToggle()

        # Add columns to the tree view.
        column_names = statistics['attr']['columns']
        for i, name in enumerate(column_names):
            column = gtk.TreeViewColumn(name, render_text, text=i)
            column.set_sort_column_id(i)
            if i in (0,1): column.set_expand(True)
            tree.append_column(column)

        # To store the data, we use the ListStore object.
        liststore = gtk.ListStore(
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
        )

        for row in statistics['results']:
            liststore.append(row)

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox_elements.pack_start(scrolled_window, expand=True, fill=True, padding=0)

class Preferences(object):
    """Display the preferences dialog.

    The preferences dialog allows the user to customize some settings.
    """

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/preferences.glade'))

        # Get some GTK objects.
        self.window = self.builder.get_object('window_preferences')
        self.entry_alpha_level = self.builder.get_object('entry_alpha_level')
        self.entry_alpha_level.set_text(str(setlyze.config.cfg.get('alpha-level')))
        self.entry_test_repeats = self.builder.get_object('entry_test_repeats')
        self.entry_test_repeats.set_text(str(setlyze.config.cfg.get('test-repeats')))
        self.entry_processes = self.builder.get_object('entry_processes')
        self.entry_processes.set_text(str(setlyze.config.cfg.get('concurrent-processes')))
        button_help = self.builder.get_object('button_help')
        button_help.connect("clicked", on_help, 'preferences-dialog')
        button_cancel = self.builder.get_object('button_cancel')
        button_ok = self.builder.get_object('button_ok')

        # Connect the window signals to the handlers.
        self.builder.connect_signals(self)

    def on_ok(self, widget, data=None):
        """Save new settings and close the preferences dialog."""
        try:
            self.set_alpha_level()
        except ValueError as e:
            self.on_error("Invalid alpha level", "Error: %s" % e)
            return

        try:
            self.set_test_repeats()
        except ValueError as e:
            self.on_error("Invalid number of repeats", "Error: %s" % e)
            return

        try:
            self.set_process_count()
        except ValueError as e:
            self.on_error("Invalid number of processes", "Error: %s" % e)
            return

        # Save the configurations to a config file.
        setlyze.config.cfg.save_to_file()

        # Close the window if all new values were saved successfully.
        self.window.destroy()

    def on_error(self, title, message):
        """Display an error dialog."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
            message_format=title)
        dialog.format_secondary_text(message)
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        dialog.destroy()

    def set_alpha_level(self):
        """Set the new alpha level for statistical test.

        Raises a ValueError if this fails.
        """
        alpha_level = float(self.entry_alpha_level.get_text())
        # Check if the new value is valid.
        if not 0.0 < alpha_level < 1.0:
            raise ValueError("Alpha level must be a float between 0.0 and 1.0.")
        setlyze.config.cfg.set('alpha-level', alpha_level)

    def set_test_repeats(self):
        """Set the new value for the number of repeats for statistical tests.

        Raises a ValueError if this fails.
        """
        test_repeats = int(self.entry_test_repeats.get_text())
        # Check if the new value is valid.
        if not test_repeats > 1:
            raise ValueError("Number of test repeats must be an integer greater than 1.")
        setlyze.config.cfg.set('test-repeats', test_repeats)

    def set_process_count(self):
        """Set the new value for the number of processes for batch mode.

        Raises a ValueError if this fails.
        """
        processes = int(self.entry_processes.get_text())
        cpu_count = setlyze.config.cfg.get('cpu-count')
        # Check if the new value is valid.
        if processes < 1 or processes > cpu_count:
            raise ValueError("The number of processes must be at least 1 and no more than the number of CPUs (=%d)." % cpu_count)
        setlyze.config.cfg.set('concurrent-processes', processes)

    def on_cancel(self, widget, data=None):
        """Close the preferences dialog."""
        self.window.destroy()

    def on_about(self, widget, data=None):
        """Display SETLyze's about dialog."""
        About()

class RepeatAnalysis(object):
    """Display the dialog for repeating an analysis.

    The dialog allows the user to customize some settings before repeating an
    analysis.
    """

    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(module_path(), 'glade/repeat_analysis.glade'))

        # Get some GTK objects.
        self.dialog = self.builder.get_object('dialog_repeat_analysis')
        self.entry_alpha_level = self.builder.get_object('entry_alpha_level')
        self.entry_alpha_level.set_text(str(setlyze.config.cfg.get('alpha-level')))
        self.entry_test_repeats = self.builder.get_object('entry_test_repeats')
        self.entry_test_repeats.set_text(str(setlyze.config.cfg.get('test-repeats')))
        self.entry_processes = self.builder.get_object('entry_processes')
        self.entry_processes.set_text(str(setlyze.config.cfg.get('concurrent-processes')))
        #button_help = self.builder.get_object('button_help')
        #button_help.connect("clicked", on_help, 'preferences-dialog')
        button_cancel = self.builder.get_object('button_cancel')
        button_ok = self.builder.get_object('button_ok')

        # Connect the dialog signals to the handlers.
        self.builder.connect_signals(self)

    def run(self):
        return self.dialog.run()

    def destroy(self):
        self.dialog.destroy()

    def on_ok(self, widget, data=None):
        """Save new settings and close the preferences dialog."""
        try:
            self.set_alpha_level()
        except ValueError as e:
            self.on_error("Invalid alpha level", "Error: %s" % e)
            return

        try:
            self.set_test_repeats()
        except ValueError as e:
            self.on_error("Invalid number of repeats", "Error: %s" % e)
            return

        try:
            self.set_process_count()
        except ValueError as e:
            self.on_error("Invalid number of processes", "Error: %s" % e)
            return

        # Save the configurations to a config file.
        setlyze.config.cfg.save_to_file()

        # Emit the response signal.
        self.dialog.response(gtk.RESPONSE_OK)

    def on_cancel(self, widget, data=None):
        """Close the preferences dialog."""
        self.dialog.response(gtk.RESPONSE_CANCEL)

    def on_about(self, widget, data=None):
        """Display SETLyze's about dialog."""
        About()

    def on_error(self, title, message):
        """Display an error dialog."""
        dialog = gtk.MessageDialog(parent=None, flags=0,
            type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK,
            message_format=title)
        dialog.format_secondary_text(message)
        dialog.set_position(gtk.WIN_POS_CENTER)
        response = dialog.run()
        dialog.destroy()

    def set_alpha_level(self):
        """Set the new alpha level for statistical test.

        Raises a ValueError if this fails.
        """
        alpha_level = float(self.entry_alpha_level.get_text())
        # Check if the new value is valid.
        if not 0.0 < alpha_level < 1.0:
            raise ValueError("Alpha level must be a float between 0.0 and 1.0.")
        setlyze.config.cfg.set('alpha-level', alpha_level)

    def set_test_repeats(self):
        """Set the new value for the number of repeats for statistical tests.

        Raises a ValueError if this fails.
        """
        test_repeats = int(self.entry_test_repeats.get_text())
        # Check if the new value is valid.
        if not test_repeats > 1:
            raise ValueError("Number of test repeats must be an integer greater than 1.")
        setlyze.config.cfg.set('test-repeats', test_repeats)

    def set_process_count(self):
        """Set the new value for the number of processes for batch mode.

        Raises a ValueError if this fails.
        """
        processes = int(self.entry_processes.get_text())
        cpu_count = setlyze.config.cfg.get('cpu-count')
        # Check if the new value is valid.
        if processes < 1 or processes > cpu_count:
            raise ValueError("The number of processes must be at least 1 and no more than the number of CPUs (=%d)." % cpu_count)
        setlyze.config.cfg.set('concurrent-processes', processes)

class About(gtk.AboutDialog):
    """Display SETLyze's about dialog."""

    def __init__(self):
        super(About, self).__init__()
        self.set_icon_name('setlyze')

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

# Instantiate some windows. These windows are not visible by default. Call
# their show() method to make them visible.
select_analysis = SelectAnalysis()
select_batch_analysis = SelectBatchAnalysis()
