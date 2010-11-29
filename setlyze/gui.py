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

"""This module provides the graphical user interfaces ("GUIs") for SETLyze.

We use GTK+ for the GUI creation. GTK+ is a highly usable, feature rich
toolkit for creating graphical user interfaces which boasts cross
platform compatibility and an easy to use API.

GTK+ is an event driven toolkit, which means it will sleep in gtk.main()
until an event occurs and control is passed to the appropriate function.
To understand the code, it's important that you gain basic
understanding of signals and callbacks, as these are used throughout
the application (not just this module). The following tutorial is a good
place to start: `Theory of Signals and Callbacks <http://www.pygtk.org/pygtk2tutorial/sec-TheoryOfSignalsAndCallbacks.html>`_

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
import pkg_resources

import pygtk
pygtk.require('2.0')
import gtk
import gobject

import setlyze.locale
import setlyze.config
import setlyze.database

__author__ = "Serrano Pereira"
__copyright__ = "Copyright 2010, GiMaRIS"
__license__ = "GPL3"
__maintainer__ = "Serrano Pereira"
__email__ = "serrano.pereira@gmail.com"
__status__ = "Production"
__date__ = "2010/09/22"

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
        self.set_border_width(10)
        self.set_resizable(True)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', self.on_close_dialog)

        # Handle application signals.
        self.handler1 = setlyze.std.sender.connect('local-db-created', self.update_tree)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def create_layout(self):
        """Construct the layout for the selection dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=2, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)

        # Create a vertical box to place the widgets in.
        vbox = gtk.VBox(homogeneous=False, spacing=5)

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
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL|gtk.EXPAND,
            yoptions=gtk.FILL|gtk.EXPAND, xpadding=0, ypadding=0)

        # User Data File button
        self.button_chg_source = gtk.Button(" Change Data Source ")
        self.button_chg_source.set_size_request(-1, -1)
        self.button_chg_source.connect("clicked", self.on_select_data_files)
        # Align the button to the left.
        csv_align = gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        csv_align.add(self.button_chg_source)
        # Add the aligned button to the table.
        table.attach(csv_align, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Continue button
        button_ok = gtk.Button("Continue")
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_continue)

        # Back button
        button_back = gtk.Button("Back")
        button_back.set_size_request(70, -1)
        button_back.connect("clicked", self.on_back)

        # Put the buttons in a horizontal box.
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(button_back)
        button_box.add(button_ok)

        # Align the button box to the right.
        buttons_align = gtk.Alignment(xalign=1.0, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the aligned button box to the table.
        table.attach(child=buttons_align, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Add the table to the main window.
        self.add(table)

    def destroy_handler_connections(self):
        """Disconnect all signal handlers created by this class."""
        setlyze.std.sender.disconnect(self.handler1)

    def set_header(self, header):
        """Set the header text to `header`."""
        header = "<span size='large' weight='bold'>%s</span>" % (header)
        self.header.set_markup(header)

    def set_description(self, description):
        """Set the description text to `description`."""
        self.label_descr.set_text(description)

    def set_save_slot(self, slot):
        """Set the localities/species selection save slot to `slot`.

        The selection variable has two slots available for saving
        selections (in analysis 2.2, two selections need to be saved,
        hence two slots were created).

        The possible values of `slot` are ``0`` for the first selection,
        and ``1`` for the second selection.
        """
        if slot not in (0,1):
            logging.error("Attempt to set setlyze.gui.SelectionWindow.save_slot \
                to '%s'. Slot can be either 0 or 1." % slot)
            sys.exit(1)
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
            response = dialog.run()

            if response == gtk.RESPONSE_OK:
                dialog.destroy()
                return

        # Save the selection. This method is present in one of the sub
        # classes.
        self.save_selection()

        # Destroy the handlers.
        self.destroy_handler_connections()

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
        self.destroy_handler_connections()

        # Emit the signal that a selection dialog was closed.
        setlyze.std.sender.emit('selection-dialog-closed')

    def on_select_data_files(self, button):
        """Display the ChangeDataSource window.

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
        self.destroy_handler_connections()

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
        self.destroy_handler_connections()

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
        """Create a model for the tree view from the specie IDs and
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

    def create_columns(self, treeview):
        """Create columns for the tree view."""
        renderer_text = gtk.CellRendererText()
        # Notice text=2, which means that we let the column display the
        # attribute values for the cell renderer from column 2 in the
        # TreeModel. Column 2 contains the species names (latin).
        column = gtk.TreeViewColumn("Specie (latin)", renderer_text, text=2)
        # Sort on column 2 from the model.
        column.set_sort_column_id(2)
        column.set_resizable(True)
        # Add the column to the tree view.
        treeview.append_column(column)

        renderer_text = gtk.CellRendererText()
        # Notice text=1, which means that we let the column display the
        # attribute values for the cell renderer from column 1 in the
        # TreeModel. Column 1 contains the species names (venacular).
        column = gtk.TreeViewColumn("Specie (venacular)", renderer_text, text=1)
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

    def __init__(self, title="Define SETL-plate Areas"):
        super(DefinePlateAreas, self).__init__()

        self.set_title(title)
        self.set_size_request(-1, -1)
        self.set_border_width(10)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # The areas definition.
        self.definition = None

        # Handle window signals.
        self.connect('delete-event', self.on_close_dialog)

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

        # Create a description label.
        label_descr = gtk.Label( setlyze.locale.text('define-plate-areas') )
        label_descr.set_line_wrap(True)
        label_descr.set_justify(gtk.JUSTIFY_FILL)
        # Add the label to the table.
        table.attach(child=label_descr, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Load an image of the SETL grid.
        setl_grid = gtk.Image()
        setl_grid.set_from_file(pkg_resources.resource_filename(__name__,
            'images/setl-grid.png'))
        # Add the image to the table.
        table.attach(setl_grid, left_attach=1, right_attach=2,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Create the definition table.
        def_table = self.create_definition_table()
        # Add def_table to the main table.
        table.attach(def_table, left_attach=0, right_attach=1,
            top_attach=1, bottom_attach=2, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Continue button
        button_ok = gtk.Button("Continue")
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_continue)

        # Back button
        button_back = gtk.Button("Back")
        button_back.set_size_request(70, -1)
        button_back.connect("clicked", self.on_back)

        # Put the buttons in a box.
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(button_back)
        button_box.add(button_ok)

        # Center the button box.
        buttons_align = gtk.Alignment(xalign=1, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the aligned box to the table
        table.attach(child=buttons_align, left_attach=1, right_attach=2,
            top_attach=3, bottom_attach=4, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

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
                    message_format="Invalid spot definition")
                dialog.format_secondary_text( setlyze.locale.text('error-single-plate-area') )
                response = dialog.run()

                if response == gtk.RESPONSE_OK:
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

        * TODO: The remote SETL database. This requires a direct
          connection with the SETL database server.

    Design Part: 1.90
    """

    def __init__(self):
        super(ChangeDataSource, self).__init__()

        self.set_title("Change Data Source")
        self.set_size_request(-1, -1)
        self.set_border_width(10)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_resizable(False)
        self.set_keep_above(False)
        self.set_modal(True)

        # Create the layout for the dialog.
        self.create_layout()

        # Display all widgets.
        self.show_all()

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

        # Add the pages to the notebook.
        label_csv = gtk.Label("CSV from MS Access SETL")
        notebook.append_page(page_csv, label_csv)

        label_db = gtk.Label("SETL database server")
        notebook.append_page(page_db, label_db)

        # Add a header to the dialog.
        label_header = gtk.Label()
        label_header.set_alignment(xalign=0, yalign=0)
        label_header.set_line_wrap(True)
        label_header.set_justify(gtk.JUSTIFY_FILL)
        header = "<span size='large' weight='bold'>Change Data Source</span>"
        label_header.set_markup(header)
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

        # Create a filter fot the file chooser.
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
        self.loc_file_chooser.connect('current-folder-changed', self.update_working_folder)

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
        button_ok.set_size_request(70, -1)
        button_ok.connect("clicked", self.on_csv_ok)

        # Cancel button
        button_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        button_cancel.set_size_request(70, -1)
        button_cancel.connect("clicked", self.on_cancel)

        # Put the buttons in a box
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(button_cancel)
        button_box.add(button_ok)

        # Align the button box
        buttons_align = gtk.Alignment(xalign=1.0, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the aligned box to the table
        table.attach(child=buttons_align, left_attach=1, right_attach=2,
            top_attach=5, bottom_attach=6, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        return table

    def on_csv_ok(self, widget, data=None):
        """Save the paths to the CSV files, set the new value for the
        data source configuration, load the SETL data from the CSV file
        into the local database, and close the dialog.
        """

        # TODO: Check if all files are selected.

        # Save the paths.
        setlyze.config.cfg.set('localities-file', self.loc_file_chooser.get_filename() )
        setlyze.config.cfg.set('species-file', self.spe_file_chooser.get_filename() )
        setlyze.config.cfg.set('records-file', self.rec_file_chooser.get_filename() )
        setlyze.config.cfg.set('plates-file', self.pla_file_chooser.get_filename() )

        # Let the application know that we are now using user selected
        # CSV files.
        setlyze.config.cfg.set('data-source', "csv-msaccess")

        # Show a progress dialog.
        pd = setlyze.gui.ProgressDialog(title="Loading data",
            description="Please wait while the data is being loaded...")
        setlyze.config.cfg.set('progress-dialog', pd)

        # Make a new local database.
        t = setlyze.database.MakeLocalDB()
        t.start()

        # Close ChangeDataSource window.
        self.destroy()

    def on_cancel(self, widget, data=None):
        """Close the dialog."""
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
            self.spe_file_chooser.set_current_folder(folder)
            self.rec_file_chooser.set_current_folder(folder)
            self.pla_file_chooser.set_current_folder(folder)

class ProgressDialog(gtk.Window):
    """Display a progress dialog.

    This progress dialog is useful if you have a process that could
    take a long time to run. This class allows you to display a progress
    dialog which shows the progress for a long process (called the worker
    process). This worker process needs to run in a separate thread for
    this to work.

    Follow these steps to get the progress dialog working:

    1) Create an instance of this class, ::

        pd = setlyze.gui.ProgressDialog(title="Analyzing",
            description="Performing heavy calculations, please wait...")

    2) Register the progress dialog using the ``config`` module, ::

        setlyze.config.cfg.set('progress-dialog', pd)

    3) Edit the worker process to automatically update the progress
       dialog. This is as easy as calling the custom update method
       between the lines of your code, ::

        setlyze.std.update_progress_dialog(0.0, "Calculating this...")
        ...
        setlyze.std.update_progress_dialog(0.5, "Calculating that...")
        ...
        setlyze.std.update_progress_dialog(1.0, "Finished!")

    4) Then start your worker process in a separate thread (if you're
       new to threading, start with the
       `threading documentation <http://docs.python.org/library/threading.html>`_) ::

        t = MyClass()
        t.start()

    Then run your application and watch the progress bar grow.

    Design Part: 1.92
    """

    def __init__(self, title, description):
        super(ProgressDialog, self).__init__()

        self.description = description

        self.set_size_request(400, -1)
        self.set_title(title)
        self.set_border_width(0)
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

        pbar_align = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=1.0, yscale=0.0)
        pbar_align.add(self.pbar)

        # Close button
        self.button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        self.button_close.set_size_request(70, -1)
        self.button_close.connect("clicked", self.on_close)
        # Disable this button by default, because we don't want the user
        # to press this button while a process is running.
        self.button_close.set_sensitive(False)

        # Put the buttons in a box.
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(self.button_close)
        # Align the box to the right.
        buttons_align = gtk.Alignment(xalign=1.0, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the alignment objects to the vertical container.
        vbox.pack_start(self.descr_label, expand=False, fill=False, padding=5)
        vbox.pack_start(pbar_align, expand=False, fill=False, padding=5)
        vbox.pack_start(self.action, expand=False, fill=True, padding=0)
        vbox.pack_start(buttons_align, expand=False, fill=False, padding=0)

        self.add(vbox)

    def destroy_silent(self):
        """Destroy the dialog without sending the
        ``progress-dialog-closed`` signal.
        """
        self.destroy()

    def on_close(self, widget=None):
        """Destroy the dialog and send the ``progress-dialog-closed``
        signal.
        """
        self.destroy()
        setlyze.std.sender.emit('progress-dialog-closed')

class DisplayReport(gtk.Window):
    """Display a dialog visualizing the elements in the XML DOM analysis
    data object.

    This class uses :class:`setlyze.std.ReportReader` to read the data
    from the XML DOM analysis data object.

    Design Part: 1.89
    """

    def __init__(self, report=None):
        super(DisplayReport, self).__init__()

        # Set the XML DOM for the ReportReader.
        self.set_report_reader(report)

        self.set_title("Analysis Report")
        self.set_size_request(600, 500)
        self.set_border_width(10)
        self.set_resizable(True)
        self.set_keep_above(False)
        self.set_position(gtk.WIN_POS_CENTER)

        # Handle window signals.
        self.connect('delete-event', self.on_close)

        # Add widgets to the GTK window.
        self.create_layout()

        # Display all widgets.
        self.show_all()

    def set_report_reader(self, report):
        """Create a report reader and pass the XML DOM report data
        object `report` to the reader. `report` can also be the path to
        a report data XML file.
        """
        self.reader = setlyze.std.ReportReader(report)

    def set_text(self, text):
        textbuffer = self.textbox.get_buffer()
        textbuffer.set_text(text)

    def create_layout(self):
        """Construct the layout for the dialog."""

        # Create a table to organize the widgets.
        table = gtk.Table(rows=3, columns=2, homogeneous=False)
        table.set_col_spacings(10)
        table.set_row_spacings(10)

        # Create a vertical box for widgets that go on the top of the
        # report window, like the report header.
        self.vbox_top = gtk.VBox(homogeneous=False, spacing=1)

        # Add the vbox_top to the table.
        table.attach(self.vbox_top, left_attach=0, right_attach=2,
            top_attach=0, bottom_attach=1,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.SHRINK | gtk.FILL,
            xpadding=0, ypadding=0)

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
            top_attach=1, bottom_attach=2,
            xoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.SHRINK | gtk.FILL,
            xpadding=0, ypadding=0)

        # Add report elements.
        self.add_report_elements()

        # Create save button.
        button_save = gtk.Button("Save Analysis Report")
        button_save.set_size_request(-1, -1)
        button_save.connect("clicked", self.on_save)
        # Align the save button to the left.
        about_align = gtk.Alignment(xalign=0, yalign=0, xscale=0, yscale=0)
        about_align.add(button_save)
        # Add the save button to the table.
        table.attach(child=about_align, left_attach=0, right_attach=1,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

        # Close button
        button_close = gtk.Button(stock=gtk.STOCK_CLOSE)
        button_close.set_size_request(70, -1)
        button_close.connect("clicked", self.on_close)

        # Put the buttons in a horizontal box.
        button_box = gtk.HBox(homogeneous=True, spacing=5)
        button_box.add(button_close)
        # Align the button box to the right.
        buttons_align = gtk.Alignment(xalign=1.0, yalign=0, xscale=0, yscale=0)
        buttons_align.add(button_box)

        # Add the aligned button box to the table.
        table.attach(child=buttons_align, left_attach=1, right_attach=2,
            top_attach=2, bottom_attach=3, xoptions=gtk.FILL,
            yoptions=gtk.SHRINK, xpadding=0, ypadding=0)

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

        Two types of files can be exported:
            * An analysis data file containing the settings, data, and
              results for the analysis (XML format).
            * TODO: A document containing the analysis results (plain text,
              LaTeX).
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
        chooser.add_filter(xml_filter)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            # Let the ReportReader save the report.
            path = chooser.get_filename()
            type = chooser.get_filter().get_name()
            self.reader.save_report(path, type)

        chooser.destroy()

    def add_report_elements(self):
        """Add the report elements present in the XML DOM object to the
        report dialog.
        """
        if not self.reader.doc:
            return

        report_elements = self.reader.get_child_names()

        # Add a header with the analysis name.
        self.add_title_header()

        if 'specie_selections' in report_elements:
            self.add_species_selections()

        if 'location_selections' in report_elements:
            self.add_locations_selections()

        if 'spot_distances_observed' in report_elements and \
                'spot_distances_expected' in report_elements:
            self.add_distances()

        if 'plate_areas_definition' in report_elements:
            self.add_plate_areas_definition()

        if 'area_totals_observed' in report_elements and \
                'area_totals_expected' in report_elements:
            self.add_area_totals()

        if 'statistics' in report_elements:
            stats = self.reader.get_element(self.reader.doc, 'statistics')
            elements = self.reader.get_child_names(stats)

            if 'normality' in elements:
                self.add_statistics_normality()

            if 'wilcoxon' in elements:
                self.add_statistics_wilcoxon()

            if 't_test' in elements:
                self.add_statistics_ttest()

            if 'chi_squared' in elements:
                self.add_statistics_chisq()

        # Create a text box.
        #self.textbox = gtk.TextView()
        #self.textbox.set_editable(False)
        #self.textbox.set_cursor_visible(True)
        #self.textbox.set_wrap_mode(gtk.WRAP_NONE)
        #self.textbox.set_pixels_above_lines(5)

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
        analysis_name = "<span size='large' weight='bold'>Analysis Report: %s</span>" % \
            (analysis_name)
        header.set_markup(analysis_name)

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
        treeiter = treestore.append(parent=None, row=["Selected species (1)"])
        species_selection = self.reader.get_species_selection(slot=0)
        for spe in species_selection:
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])

        # Add the second species selection to the model.
        treeiter = treestore.append(parent=None, row=["Selected species (2)"])
        species_selection = self.reader.get_species_selection(slot=1)
        for spe in species_selection:
            if not spe:
                treestore.remove(treeiter)
                break
            species = "%s (%s)" % (spe['name_latin'], spe['name_venacular'])
            treestore.append(parent=treeiter, row=[species])

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
        treeiter = treestore.append(parent=None, row=["Selected locations (1)"])
        locations_selection = self.reader.get_locations_selection(slot=0)
        for loc in locations_selection:
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])

        # Add the second locations selection to the model.
        treeiter = treestore.append(parent=None, row=["Selected locations (2)"])
        locations_selection = self.reader.get_locations_selection(slot=1)
        for loc in locations_selection:
            if not loc:
                treestore.remove(treeiter)
                break
            location = "%s" % (loc['name'])
            treestore.append(parent=treeiter, row=[location])

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
        expander = gtk.Expander("Plate Areas Definition")
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

        column = gtk.TreeViewColumn("Plate Area Spots", cell, text=1)
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
        expander = gtk.Expander("Species Totals per Plate Area")
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
            liststore.append([area_id, totals_observed[area_id], totals_expected[area_id]])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_wilcoxon(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Results for Wilcoxon signed-rank test")
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

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Mean Observed','Mean Expected',
            'Conf. interval start','Conf. interval end','Remarks']

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
            gobject.TYPE_FLOAT,
            gobject.TYPE_FLOAT,
            gobject.TYPE_STRING,
            )

        # Add the distances to the model.
        statistics = self.reader.get_statistics('wilcoxon')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = []
            if float(items['p_value']) > 0.05:
                remarks.append("Not significant")
            else:
                remarks.append("Significant")

                if float(items['mean_observed']) < float(items['mean_expected']):
                    remarks.append("Attraction")
                else:
                    remarks.append("Repulsion")

            if float(items['p_value']) < 0.001:
                remarks.append("P < 0.001")
            elif float(items['p_value']) < 0.01:
                remarks.append("P < 0.01")
            elif float(items['p_value']) < 0.05:
                remarks.append("P < 0.05")
            else:
                remarks.append("P > 0.05")

            if int(attr['n']) > 20:
                remarks.append("n > 20")
            else:
                remarks.append("n < 20")

            remarks = "; ".join(remarks)

            # Add all result items to the tree model.
            liststore.append([
                int(attr['n_positive_spots']),
                int(attr['n_plates']),
                int(attr['n']),
                float(items['p_value']),
                float(items['mean_observed']),
                float(items['mean_expected']),
                float(items['conf_int_start']),
                float(items['conf_int_end']),
                #attr['method'],
                remarks,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)

    def add_statistics_chisq(self):
        """Add the statistic results to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Results for Pearson's Chi-squared Test for Count Data")
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

        column_names = ['Positive Spots','n (plates)',
            'n (distances)','P-value','Chi squared','df',
            'Mean Expected','Mean Observed','Remarks']

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
        statistics = self.reader.get_statistics('chi_squared')

        for attr,items in statistics:
            # Create a remarks string which allows for easy recognition
            # of interesting results.
            remarks = []
            if float(items['p_value']) > 0.05:
                remarks.append("Not significant")
            else:
                remarks.append("Significant")

                if float(items['mean_observed']) < float(items['mean_expected']):
                    remarks.append("Attraction")
                else:
                    remarks.append("Repulsion")

            if float(items['p_value']) < 0.001:
                remarks.append("P < 0.001")
            elif float(items['p_value']) < 0.01:
                remarks.append("P < 0.01")
            elif float(items['p_value']) < 0.05:
                remarks.append("P < 0.05")
            else:
                remarks.append("P > 0.05")

            if int(attr['n']) > 20:
                remarks.append("n > 20")
            else:
                remarks.append("n < 20")

            remarks = "; ".join(remarks)

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

    def add_statistics_normality(self):
        """Add the statistic results for normality to the report dialog."""

        # Create a Scrolled Window
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_shadow_type(gtk.SHADOW_NONE)
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        # Create the expander
        expander = gtk.Expander("Statistic Results: Normality")
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
                attr['method'],
                null_hypothesis,
                ])

        # Set the tree model.
        tree.set_model(liststore)

        # Add the tree to the scrolled window.
        scrolled_window.add(tree)

        # Add the ScrolledWindow to the vertcal box.
        self.vbox.pack_start(expander, expand=False, fill=True, padding=0)
