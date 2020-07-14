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
from gi.repository import GLib
from gi.repository import Gtk
from i18n import gettext as _

from ..canvas import Board
from ..dialogs import AboutDialog
from ..dialogs import NewMatchDialog
from ..dialogs import OpenMatchDialog
from ..dialogs import RequestOverwriteDialog
from ..dialogs import RequestSaveDialog
from ..dialogs import SaveMatchDialog
from ..dialogs import ScoresheetDialog
from ..services import MatchManager
from ..values import Rotation
from ..values import Side
from ..widgets import MatchInfobar
from ..widgets import RecentChooserPopoverMenu
from ..mixer import SoundContext


@Gtk.Template(resource_path='/com/joansala/auale/gtk/windows/auale_window.ui')
class AualeWindow(Gtk.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = 'AualeWindow'

    _headerbar = Gtk.Template.Child('main_headerbar')
    _recents_menu_box = Gtk.Template.Child('recents_menu_box')
    _unsaved_indicator = Gtk.Template.Child('unsaved_indicator')

    __sounds_path = '/com/joansala/auale/sounds/theme.json'

    def __init__(self, application):
        super(AualeWindow, self).__init__()

        self._settings = None
        self._canvas = Board()
        self._match = Match(Oware)
        self._infobar = MatchInfobar()
        self._match_manager = MatchManager()
        self._sound_context = SoundContext()

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
        self._infobar.show_match_information(match)
        self._canvas.set_current_match(match)
        self._canvas.grab_focus()
        self.add(self._canvas)

    def connect_window_signals(self):
        """Connects the required signals to this window"""

        self.connect('delete-event', self.on_window_delete_event)
        self.connect('destroy', self.on_window_destroy)
        self.connect('realize', self.on_window_realize)
        self._canvas.connect('house-activated', self.on_canvas_house_activated)
        self._match_manager.connect('file_overwrite', self.on_match_file_overwrite)
        self._match_manager.connect('file-changed', self.on_match_file_changed)
        self._match_manager.connect('file-load-error', self.on_match_file_load_error)
        self._match_manager.connect('file-save-error', self.on_match_file_save_error)
        self._match_manager.connect('file-unload', self.on_match_file_unload)

    def connect_sound_signals(self):
        """Connects this window to the sound mixer"""

        self._sound_context.load_script(self.__sounds_path)
        self._sound_context.connect_signals(self._canvas)
        self._sound_context.connect_signals(self)

    def apply_sound_settings(self):
        """Applies the sound setting to the context"""

        context = self._sound_context
        is_muted = self._settings.get_value('mute')
        context.mute_context() if is_muted else context.unmute_context()

    def get_local_settings(self):
        """Gets this window's local settings instance"""

        return self._settings

    def set_local_settings(self, settings):
        """Sets this window's local settings instance"""

        self._settings = settings

    def set_engine_command(self, command):
        """Sets the engine used by this window"""

        value = GLib.Variant.new_string(command)
        self.activate_action('engine', value)

    def set_immersive_mode(self, value):
        """Sets the immersive used by this window"""

        action = self.lookup_action('immersive')
        value = GLib.Variant.new_boolean(value)
        action.change_state(value)

    def set_engine_side(self, side):
        """Sets the engine site to move"""

        value = GLib.Variant.new_string(side.nick)
        self.activate_action('side', value)

    def set_match_from_uri(self, uri):
        """Open a match file on this window"""

        value = GLib.Variant.new_string(uri)
        self.activate_action('open', value)

    def on_match_file_changed(self, manager, match):
        """Emitted when the match file changed"""

        file = manager.get_file()
        name = file and file.get_parse_name()

        self._unsaved_indicator.hide()
        self._headerbar.set_subtitle(name)
        self._infobar.show_match_information(match)
        self._canvas.set_current_match(match)
        self.set_engine_side(Side.NEITHER)

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
                self.activate_action('save-as')

            if not manager.has_unsaved_changes():
                discard_changes = True

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
        """Close this application window"""

        self.destroy()

    def on_move_action_activate(self, action, value):
        """..."""

    def on_move_from_action_activate(self, action, value):
        """..."""

    def on_choose_action_activate(self, action, value):
        """Activates the board house that has the focus"""

        house = self._canvas.get_focused_house()
        self._canvas.activate_house(house) if house else None
        self._canvas.focus_first_house()

    def on_left_action_activate(self, action, value):
        """Focus the previous house on the board"""

        self._canvas.focus_previous_house()

    def on_right_action_activate(self, action, value):
        """Focus the next house on the board"""

        self._canvas.focus_next_house()

    def on_up_action_activate(self, action, value):
        """Focus the first house on the board"""

        self._canvas.focus_first_house()

    def on_down_action_activate(self, action, value):
        """Focus the last house on the board"""

        self._canvas.focus_last_house()

    def on_canvas_house_activated(self, canvas, house):
        """..."""

    def on_new_action_activate(self, action, value):
        """Starts a new match on user request"""

        response = self._new_match_dialog.inquire()

        if response == Gtk.ResponseType.ACCEPT:
            self._match_manager.load_new_match()

            if not self._match_manager.has_unsaved_changes():
                side = self._new_match_dialog.get_engine_side()
                self.set_engine_side(side)

    def on_open_action_activate(self, action, value):
        """Opens a match from a file"""

        uri = value.get_string() or None
        response = uri or self._open_match_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            uri = self._open_match_dialog.get_uri()

        if uri and isinstance(uri, str):
            self._match_manager.load_from_uri(uri)

    def on_rules_action_activate(self, action, value):
        """..."""

        pass

    def on_save_as_action_activate(self, action, value):
        """Saves the current match to a new file"""

        file = self._match_manager.get_file()
        name = '' if file else _('untitled.ogn')
        uri = file.get_uri() if file else ''

        self._save_match_dialog.set_uri(uri)
        self._save_match_dialog.set_current_name(name)

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
        """Shows the scoresheet dialog for the current match"""

        match = self._match_manager.get_match()
        self._scoresheet_dialog.set_from_match(match)
        self._scoresheet_dialog.run()

        tags = self._scoresheet_dialog.get_match_tags()
        match.set_tags(tags)
        self.refresh_view()

    def on_stop_action_activate(self, action, value):
        """..."""

        pass

    def on_undo_all_action_activate(self, action, value):
        """..."""

    def on_undo_action_activate(self, action, value):
        """..."""

    def on_redo_all_action_activate(self, action, value):
        """..."""

    def on_redo_action_activate(self, action, value):
        """..."""

    def on_engine_setting_changed(self, action, value):
        """..."""

        pass

    def on_mute_setting_changed(self, action, value):
        """Toggles the mute on the sound context"""

        self.apply_sound_settings()

    def on_strength_setting_changed(self, action, value):
        """..."""

        pass

    def on_immersive_action_change_state(self, action, value):
        """Toggles the immersive state of the window"""

        is_immersive = value.get_boolean()
        self.fullscreen() if is_immersive else self.unfullscreen()
        action.set_state(value)

    def on_windowed_action_activate(self, action, value):
        """Toggles off the immersive state of the window"""

        self.set_immersive_mode(False)

    def on_rotate_action_change_state(self, action, value):
        """Flips the board canvas"""

        is_rotated = value.get_boolean()
        rotation = is_rotated and Rotation.ROTATED or Rotation.BASE
        self._canvas.set_rotation(rotation)
        action.set_state(value)

    def on_side_action_change_state(self, action, value):
        """Emitted on engine playing side changes"""

        engine_side = Side.value_of(value.get_string())
        self._canvas.set_rotation(engine_side.rotation)
        action.set_state(value)

    def on_window_realize(self, window):
        """Emitted when the window is realized"""

        self.apply_sound_settings()
        self.connect_sound_signals()

    def on_window_delete_event(self, window, event):
        """Emitted when the user asks to close the window"""

        return self._match_manager.unload()

    def on_window_destroy(self, window):
        """Emitted to finalize the window"""

        self._sound_context.mute_context()
