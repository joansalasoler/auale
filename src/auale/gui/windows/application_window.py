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

import logging

from game import Match
from game import Oware
from gi.repository import Gtk

from ..widgets import OwareBoard


@Gtk.Template.from_file('gui/windows/application_window.ui')
class ApplicationWindow(Gtk.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = 'ApplicationWindow'

    _board_overlay = Gtk.Template.Child('board_overlay')

    def __init__(self, application):
        super(ApplicationWindow, self).__init__()

        self._match = Match(Oware)
        self._canvas = OwareBoard()
        self._settings = None

        self._board_overlay.add(self._canvas)
        self._canvas.grab_focus()

    def get_local_settings(self):
        """Gets this window's local settings instance"""

        return self._settings

    def set_local_settings(self, settings):
        """Sets this window's local settings instance"""

        self._settings = settings

    def set_engine_command(self, command):
        """Sets the engine used by this window"""

        pass

    def on_about_action_activate(self, action, value):
        """..."""

        pass

    def on_close_action_activate(self, action, value):
        """..."""

        pass

    def on_move_action_activate(self, action, value):
        """..."""

        pass

    def on_new_action_activate(self, action, value):
        """..."""

        pass

    def on_open_action_activate(self, action, value):
        """..."""

        pass

    def on_redo_all_action_activate(self, action, value):
        """..."""

        pass

    def on_redo_action_activate(self, action, value):
        """..."""

        pass

    def on_rules_action_activate(self, action, value):
        """..."""

        pass

    def on_save_as_action_activate(self, action, value):
        """..."""

        pass

    def on_save_action_activate(self, action, value):
        """..."""

        pass

    def on_scoresheet_action_activate(self, action, value):
        """..."""

        pass

    def on_stop_action_activate(self, action, value):
        """..."""

        pass

    def on_undo_all_action_activate(self, action, value):
        """..."""

        pass

    def on_undo_action_activate(self, action, value):
        """..."""

        pass

    def on_engine_setting_changed(self, action, value):
        """..."""

        pass

    def on_mute_setting_changed(self, action, value):
        """..."""

        pass

    def on_strength_setting_changed(self, action, value):
        """..."""

        pass

    def on_immersive_action_change_state(self, action, value):
        """..."""

        action.set_state(value)

    def on_rotate_action_change_state(self, action, value):
        """..."""

        action.set_state(value)

    def on_side_action_change_state(self, action, value):
        """..."""

        action.set_state(value)
