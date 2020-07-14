# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014-2020 Joan Sala Soler <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk
from i18n import gettext as _


@Gtk.Template(resource_path='/com/joansala/auale/gtk/dialogs/scoresheet_dialog.ui')
class ScoresheetDialog(Gtk.Dialog):
    """Match scoresheet dialog"""

    __gtype_name__ = 'ScoresheetDialog'

    _liststore = Gtk.Template.Child('properties_liststore')
    _treeview = Gtk.Template.Child('properties_treeview')
    _value_column = Gtk.Template.Child('value_treeviewcolumn')
    _value_cell = Gtk.Template.Child('value_cellrenderertext')
    _protected_tags = ('FEN', 'Variant')

    def __init__(self, window):
        super(ScoresheetDialog, self).__init__()

        self.set_transient_for(window)
        self.connect('delete-event', self.on_delete_event)
        self._treeview.connect('row-activated', self.on_treeview_row_activated)
        self._value_cell.connect('edited', self.on_value_cell_edited)
        self._tags = dict()

    def on_delete_event(self, dialog, event):
        """Hide the dialog when delete is emitted"""

        return self.hide_on_delete()

    def get_match_tags(self):
        """Gets the displayed match tags"""

        return tuple(self._tags.items())

    def set_from_match(self, match):
        """Show a match tags edition dialog"""

        self._liststore.clear()
        self._tags = dict(match.get_tags())

        for name, value in self._tags.items():
            if name not in self._protected_tags:
                values = (name, _(name), value)
                self._liststore.append(values)

        self._treeview.set_cursor(0)
        self._treeview.grab_focus()

    def on_treeview_row_activated(self, widget, path, column):
        """Toggle the edition mode when a row is activated"""

        self._value_column.focus_cell(self._value_cell)
        widget.set_cursor(path, self._value_column, True)

    def on_value_cell_edited(self, widget, path, value):
        """Updates the listore after a value was edited"""

        iterator = self._liststore.get_iter(path)
        name = self._liststore.get_value(iterator, 0)
        self._liststore.set_value(iterator, 2, value)
        self._tags[name] = value
