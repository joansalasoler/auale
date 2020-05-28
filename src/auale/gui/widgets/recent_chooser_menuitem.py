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

from gi.repository import GLib
from gi.repository import Gtk


@Gtk.Template.from_file('gui/widgets/recent_chooser_menuitem.ui')
class RecentChooserMenuitem(Gtk.Bin):
    """A menuitem on a recent chooser popover menu"""

    __gtype_name__ = 'RecentChooserMenuitem'

    _icon = Gtk.Template.Child('icon')
    _display_name = Gtk.Template.Child('display_name')

    def set_from_gicon(self, gicon):
        """Sets the icon of the menuitem"""

        self._icon.set_from_gicon(gicon, Gtk.IconSize.MENU)

    def set_display_name(self, text):
        """Sets the display name of the menuitem"""

        self._display_name.set_text(text)

    def set_action_name(self, name):
        """Sets the action associated with the menuitem"""

        button = self.get_child()
        button.set_action_name(name)

    def set_action_target_value(self, uri):
        """Sets the value for the associated action"""

        button = self.get_child()
        value = GLib.Variant.new_string(uri)
        button.set_action_target_value(value)
