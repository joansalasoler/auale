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

from game import Match
from game import Oware
from gi.repository import Gtk
from i18n import gettext as _

from ..services import MatchManager
from ..widgets import MatchInfobar
from ..widgets import OwareBoard
from ..widgets import RecentChooserPopoverMenu


@Gtk.Template(resource_path='/com/joansala/auale/gtk/windows/application_window.ui')
class ApplicationWindow(Gtk.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = 'ApplicationWindow'

    _board_overlay = Gtk.Template.Child('board_overlay')
    _headerbar = Gtk.Template.Child('main_headerbar')
    _recents_menu_box = Gtk.Template.Child('recents_menu_box')

    def __init__(self, application):
        super(ApplicationWindow, self).__init__()

        self._match = Match(Oware)
        self._canvas = OwareBoard()
        self._infobar = MatchInfobar()
        self._match_manager = MatchManager()
        self._settings = None

        self.setup_window_widgets()
        self.connect_window_signals()

    def setup_window_widgets(self):
        """Attach an initialize this window's widgets"""

        match = self._match_manager.get_match()

        recents_menu = RecentChooserPopoverMenu()
        recents_menu.set_action_name('win.open')

        self._recents_menu_box.add(recents_menu)
        self._board_overlay.add_overlay(self._infobar)
        self._board_overlay.add(self._canvas)

        self._infobar.show_match_information(match)
        self._canvas.set_board(match.get_board())
        self._canvas.grab_focus()

    def connect_window_signals(self):
        """Connects the required signals to this window"""

        self._canvas.connect('house-pressed', self.on_canvas_house_pressed)
        self._match_manager.connect('file-changed', self.on_match_file_changed)

    def get_local_settings(self):
        """Gets this window's local settings instance"""

        return self._settings

    def set_local_settings(self, settings):
        """Sets this window's local settings instance"""

        self._settings = settings

    def set_engine_command(self, command):
        """Sets the engine used by this window"""

        pass

    def open_match_from_uri(self, uri):
        """Open a match on this window given an URI path"""

        try:
            self._match_manager.load_from_uri(uri)
        except BaseException:
            title = _("Error opening match")
            summary = _('Match file cannot be opened')
            self._infobar.show_error_message(f'<b>{ title }</b>: { summary }')

    def on_match_file_changed(self, manager, match):
        """Emitted when the match file changes"""

        file = manager.get_file()
        name = file.get_parse_name()
        board = match.get_board()

        self._infobar.show_match_information(match)
        self._headerbar.set_subtitle(name)
        self._canvas.set_board(board)

    def on_about_action_activate(self, action, value):
        """..."""

        pass

    def on_close_action_activate(self, action, value):
        """..."""

        pass

    def on_move_action_activate(self, action, value):
        """..."""

        pass

    def on_move_from_action_activate(self, action, move):
        """..."""

        pass

    def on_canvas_house_pressed(self, canvas, house):

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
