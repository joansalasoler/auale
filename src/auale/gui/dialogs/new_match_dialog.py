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
from ..values import Side


@Gtk.Template(resource_path='/com/joansala/auale/gtk/dialogs/new_match_dialog.ui')
class NewMatchDialog(Gtk.Dialog):
    """Dialog to start a new match"""

    __gtype_name__ = 'NewMatchDialog'

    _south_button = Gtk.Template.Child('south_button')
    _north_button = Gtk.Template.Child('north_button')
    _watch_button = Gtk.Template.Child('watch_button')
    _edit_button = Gtk.Template.Child('edit_button')

    def __init__(self, window):
        super(NewMatchDialog, self).__init__()

        self._side = Side.SOUTH
        self.set_transient_for(window)
        self.connect('delete-event', self.on_delete_event)
        self.connect_button(self._edit_button, Side.NEITHER)
        self.connect_button(self._north_button, Side.SOUTH)
        self.connect_button(self._south_button, Side.NORTH)
        self.connect_button(self._watch_button, Side.BOTH)

    def on_delete_event(self, dialog, event):
        """Hide the dialog when delete is emitted"""

        return self.hide_on_delete()

    def get_engine_side(self):
        """Obtains the selected computer side"""

        return self._side

    def on_option_selected(self, button, side):
        """Emitted when the user selects an option"""

        self._side = side
        self.response(Gtk.ResponseType.ACCEPT)

    def connect_button(self, button, side):
        """Connects a button to the selection handler"""

        button.connect('clicked', self.on_option_selected, side)

    def inquire(self):
        """Runs the dialog and then hides it"""

        response = self.run()
        self.hide()

        return response
