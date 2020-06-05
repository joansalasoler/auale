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
from gi.repository import GLib
from i18n import gettext as _

from ..dialogs import AboutDialog
from ..dialogs import NewMatchDialog
from ..dialogs import OpenMatchDialog
from ..dialogs import RequestOverwriteDialog
from ..dialogs import RequestSaveDialog
from ..dialogs import SaveMatchDialog
from ..dialogs import ScoresheetDialog
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
    _unsaved_indicator = Gtk.Template.Child('unsaved_indicator')

    def __init__(self, application):
        super(ApplicationWindow, self).__init__()

        self._settings = None
        self._match = Match(Oware)
        self._canvas = OwareBoard()
        self._infobar = MatchInfobar()
        self._match_manager = MatchManager()

        self._about_dialog = AboutDialog(self)
        self._new_match_dialog = NewMatchDialog(self)
        self._open_match_dialog = OpenMatchDialog(self)
        self._request_save_dialog = RequestSaveDialog(self)
        self._request_overwrite_dialog = RequestOverwriteDialog(self)
        self._save_match_dialog = SaveMatchDialog(self)
        self._scoresheet_dialog = ScoresheetDialog(self)

        self.setup_window_widgets()
        self.connect_window_signals()

    def setup_window_widgets(self):
        """Attach an initialize this window's widgets"""

        match = self._match_manager.load_new_match()

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

        self.connect('destroy', self.on_window_destroy)
        self.connect('delete-event', self.on_window_delete_event)
        self._canvas.connect('house-pressed', self.on_canvas_house_pressed)
        self._match_manager.connect('file_overwrite', self.on_match_file_overwrite)
        self._match_manager.connect('file-changed', self.on_match_file_changed)
        self._match_manager.connect('file-load-error', self.on_match_file_load_error)
        self._match_manager.connect('file-save-error', self.on_match_file_save_error)
        self._match_manager.connect('file-unload', self.on_match_file_unload)

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

        self._match_manager.load_from_uri(uri)

    def on_match_file_changed(self, manager, match):
        """Emitted when the match file changed"""

        file = manager.get_file()
        name = file.get_parse_name()
        board = match.get_board()

        self._unsaved_indicator.hide()
        self._infobar.show_match_information(match)
        self._headerbar.set_subtitle(name)
        self._canvas.set_board(board)

    def on_match_file_unload(self, manager, match):
        """Emitted before the match file is unloaded"""

        discard_changes = True
        is_unsaved = manager.has_unsaved_changes()
        is_stored = self._match_manager.has_file_storage()
        can_prompt = self._settings.get_boolean('prompt-unsaved')

        if is_unsaved and (can_prompt or is_stored):
            response = self._request_save_dialog.confirm()
            discard_changes = (response == Gtk.ResponseType.ACCEPT)

            if response == Gtk.ResponseType.REJECT:
                value = GLib.Variant.new_string('')
                self.activate_action('save', value)

            if not manager.has_unsaved_changes():
                self.destroy()

        return discard_changes

    def on_match_file_overwrite(self, manager, match):
        """Emitted before a file that changed on disk is overwritten"""

        response = self._request_overwrite_dialog.confirm()
        overwrite_changes = (response == Gtk.ResponseType.ACCEPT)

        return overwrite_changes

    def on_match_file_load_error(self, manager, error):
        """Handle  match load errors"""

        title = _('Error opening match')
        summary = _('Match file cannot be opened')
        message = f'<b>{ title }</b>: { summary }'

        self._infobar.show_error_message(message)

    def on_match_file_save_error(self, manager, error):
        """Handle  match load errors"""

        title = _("Error saving match")
        summary = _('Cannot save current match')
        message = f'<b>{ title }</b>: { summary }'

        self._infobar.show_error_message(message)

    def on_about_action_activate(self, action, value):
        """..."""

        self._about_dialog.run()

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

        self._new_match_dialog.run()

    def on_open_action_activate(self, action, value):
        """..."""

        self._open_match_dialog.run()

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
        """Saves the current match to a new file"""

        response = self._save_match_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            uri = self._save_match_dialog.get_uri()
            self._match_manager.save_to_uri(uri)

    def on_save_action_activate(self, action, value):
        """Saves the current match to its file"""

        if not self._match_manager.has_file_storage():
            return self.activate_action('save-as')

        file = self._match_manager.get_file()
        uri = value.get_string() or file.get_uri()
        self._match_manager.save_to_uri(uri)

    def on_scoresheet_action_activate(self, action, value):
        """..."""

        self._scoresheet_dialog.run()

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

    def on_window_delete_event(self, window, event):
        """Emitted when the user asks to close the window"""

        return self._match_manager.unload()

    def on_window_destroy(self, window):
        """Emitted to finalize the window"""

        pass
