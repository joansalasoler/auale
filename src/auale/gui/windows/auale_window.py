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

import os

from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import Gtk
from config import theme
from i18n import gettext as _
from game import Match
from book import OpeningBook
from uci import Engine
from uci import Human
from uci import Strength

from ..dialogs import AboutDialog
from ..dialogs import NewMatchDialog
from ..dialogs import OpenMatchDialog
from ..dialogs import RequestOverwriteDialog
from ..dialogs import RequestSaveDialog
from ..dialogs import SaveMatchDialog
from ..dialogs import ScoresheetDialog
from ..services import GameLoop
from ..services import MatchManager
from ..services import PlayerManager
from ..values import Rotation
from ..values import Side
from ..widgets import BoardCanvas
from ..widgets import RecentChooserPopoverMenu


@Gtk.Template(resource_path='/com/joansala/auale/gtk/windows/auale_window.ui')
class AualeWindow(Gtk.ApplicationWindow):
    """Main application window"""

    __gtype_name__ = 'AualeWindow'

    _headerbar = Gtk.Template.Child('main_headerbar')
    _recents_menu_box = Gtk.Template.Child('recents_menu_box')
    _unsaved_indicator = Gtk.Template.Child('unsaved_indicator')

    def __init__(self, application):
        super(AualeWindow, self).__init__()

        self._settings = None
        self._active_player = None
        self._board_canvas = BoardCanvas()
        self._game_loop = GameLoop()
        self._match_manager = MatchManager()
        self._player_manager = PlayerManager()
        self._sound_context = theme.create_sound_context()
        self._book = self.create_opening_book()

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

        recents_menu = RecentChooserPopoverMenu()
        recents_menu.set_action_name('win.open')

        self._match_manager.load_new_match()
        self._recents_menu_box.add(recents_menu)
        self.add(self._board_canvas)

    def connect_window_signals(self):
        """Connects the required signals to this window"""

        self.connect('delete-event', self.on_window_delete_event)
        self.connect('destroy', self.on_window_destroy)
        self.connect('realize', self.on_window_realize)
        self.connect('motion-notify-event', self.on_motion_notify)
        self._board_canvas.connect('house-activated', self.on_board_canvas_house_activated)
        self._board_canvas.connect('animation-completed', self.on_move_animation_completed)
        self._board_canvas.connect('canvas_updated', self.on_canvas_updated)
        self._match_manager.connect('file_overwrite', self.on_match_file_overwrite)
        self._match_manager.connect('file-changed', self.on_match_file_changed)
        self._match_manager.connect('file-load-error', self.on_match_file_load_error)
        self._match_manager.connect('file-save-error', self.on_match_file_save_error)
        self._match_manager.connect('file-unload', self.on_match_file_unload)
        self._player_manager.connect('engine-start-error', self.on_engine_start_error)
        self._player_manager.connect('engine-failure-error', self.on_engine_failure_error)
        self._game_loop.connect('move-received', self.on_player_move_received)
        self._game_loop.connect('info-received', self.on_player_info_received)

    def connect_sound_signals(self):
        """Connects this window to the sound mixer"""

        self._sound_context.connect_signals(self._board_canvas)
        self._sound_context.connect_signals(self)

    def create_opening_book(self):
        """Instantiates the opening book"""

        file_path = os.path.dirname(__file__)
        base_path = os.path.abspath(os.path.join(file_path, os.pardir))
        book_path = os.path.join(base_path, '../data/engine/oware-book.bin')
        opening_book = OpeningBook(book_path)

        return opening_book

    def apply_engine_settings(self):
        """Applies the strength setting to the engines"""

        value = self._settings.get_value('engine')
        self._player_manager.set_engine_command(value.get_string())

    def apply_sound_settings(self):
        """Applies the sound setting to the context"""

        context = self._sound_context
        is_muted = self._settings.get_value('mute')
        context.mute_context() if is_muted else context.unmute_context()

    def apply_strength_settings(self):
        """Applies the strength setting to the engines"""

        value = self._settings.get_value('strength')
        strength = Strength.value_of(value.get_string())
        self._player_manager.set_engine_strength(strength)

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

    def set_active_player(self, player, match):
        """Set the active player"""

        self._active_player = player

        if isinstance(player, Human):
            self.request_human_move(player, match)
        else:
            self.request_engine_move(player, match)

        GLib.idle_add(self.refresh_view)

    def request_human_move(self, player, match):
        """Request a move to a human player"""

        self._game_loop.request_move(player, match)
        self._board_canvas.show_activables(match)

    def request_engine_move(self, player, match):
        """Request a move to an engine player"""

        strength = player.get_playing_strength()
        self._book.set_strength(strength)

        if not self.request_book_move(match):
            self._game_loop.request_move(player, match)

    def request_book_move(self, match):
        """Request a move from the openings book"""

        book_move = self._book.pick_best_move(match)
        has_move = book_move is not None

        if has_move is True:
            self.make_legal_move(match, book_move)

        return has_move

    def toggle_active_player(self, match):
        """Requests a move to the current player of a match"""

        player = self._player_manager.get_player_for_turn(match)
        self.set_active_player(player, match)

        return player

    def on_match_file_changed(self, manager, match, is_new):
        """Emitted when the match file changed"""

        file = manager.get_file()
        name = file and file.get_parse_name()

        if is_new is True:
            infobar = self._board_canvas.get_object('report')
            infobar.clear_message()
            match.undo_all_moves()

        self._board_canvas.show_match(match)
        self._headerbar.set_subtitle(name)
        self.set_engine_side(Side.NEITHER)
        GLib.idle_add(self.refresh_view)

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

        infobar = self._board_canvas.get_object('infobar')
        infobar.show_error_message(message)

    def on_match_file_save_error(self, manager, error):
        """Handle  match load errors"""

        title = _('Error saving match')
        summary = _('Cannot save current match')
        message = f'<b>{ title }</b>: { summary }'

        infobar = self._board_canvas.get_object('infobar')
        infobar.show_error_message(message)

    def on_engine_start_error(self, manager, error):
        """Handle engine initialization errors"""

        title = _('Computer player is disabled')
        summary = _('Could not start the engine')
        message = f'<b>{ title }</b>: { summary }'

        infobar = self._board_canvas.get_object('report')
        infobar.show_error_message(message)
        self.set_engine_side(Side.NEITHER)
        GLib.idle_add(self.refresh_view)

    def on_engine_failure_error(self, manager, reason):
        """Handle engine failure errors"""

        title = _('Computer player is disabled')
        message = f'<b>{ title }</b>: { _(reason) }'

        infobar = self._board_canvas.get_object('report')
        infobar.show_error_message(message)
        self.set_engine_side(Side.NEITHER)
        GLib.idle_add(self.refresh_view)

    def on_about_action_activate(self, action, value):
        """Shows the about dialog"""

        self._about_dialog.run()

    def on_close_action_activate(self, action, value):
        """Close this application window"""

        self.destroy()

    def on_move_animation_completed(self, canvas):
        """Emitted when a move animation finishes"""

        match = self._match_manager.get_match()

        if isinstance(match, Match):
            player = self.toggle_active_player(match)

            is_human = isinstance(player, Human)
            has_cursor = self._board_canvas.get_cursor_visible()
            is_endgame = match.has_ended()

            if is_human and not has_cursor and not is_endgame:
                self._board_canvas.focus_first_house()

            GLib.idle_add(self.refresh_view)

    def on_motion_notify(self, window, event):
        """Emitted when the cursor moves over the window"""

        if not self._board_canvas.get_cursor_visible():
            self._board_canvas.show_cursor()

    def on_canvas_updated(self, canvas, match):
        """Emitted after a match is show on the canvas"""

        infobar = self._board_canvas.get_object('infobar')
        infobar.show_match_information(match)
        has_message = infobar.has_message()
        self._board_canvas.set_message_visible(has_message)

    def on_move_action_activate(self, action, value):
        """A move from the engine was requested by the user"""

        if self._board_canvas.get_reactive():
            match = self._match_manager.get_match()
            player = self._player_manager.get_engine_player()
            self.set_active_player(player, match)

    def on_move_from_action_activate(self, action, value):
        """A house was activated with a keyboard shortcut"""

        if self._board_canvas.get_reactive():
            key = value.get_string()
            game = self._match_manager.get_game()
            match = self._match_manager.get_match()
            is_south_turn = match.get_turn() == game.SOUTH
            notation = key.upper() if is_south_turn else key
            move = game.to_move(notation)

            self.make_legal_move(match, move)

    def on_board_canvas_house_activated(self, canvas, house):
        """A house was activated on the canvas"""

        match = self._match_manager.get_match()
        self.make_legal_move(match, house.get_move())

    def on_player_move_received(self, game_loop, player, move):
        """A move was received from an engine player"""

        match = self._match_manager.get_match()

        if isinstance(match, Match):
            self.make_legal_move(match, move)

    def on_player_info_received(self, game_loop, player, report):
        """A report was received from an engine player"""

        if report.get('cp') or report.get('pv'):
            infobar = self._board_canvas.get_object('report')
            infobar.show_principal_variation(report)

    def on_choose_action_activate(self, action, value):
        """Activates the board house that has the focus"""

        if self._board_canvas.get_reactive():
            house = self._board_canvas.get_focused_house()
            self._board_canvas.activate_house(house) if house else None
            self._board_canvas.focus_first_house()

    def on_left_action_activate(self, action, value):
        """Focus the previous house on the board"""

        if self._board_canvas.get_reactive():
            self._board_canvas.focus_previous_house()
            self._board_canvas.hide_cursor()

    def on_right_action_activate(self, action, value):
        """Focus the next house on the board"""

        if self._board_canvas.get_reactive():
            self._board_canvas.focus_next_house()
            self._board_canvas.hide_cursor()

    def on_up_action_activate(self, action, value):
        """Focus the first house on the board"""

        if self._board_canvas.get_reactive():
            self._board_canvas.focus_first_house()
            self._board_canvas.hide_cursor()

    def on_down_action_activate(self, action, value):
        """Focus the last house on the board"""

        if self._board_canvas.get_reactive():
            self._board_canvas.focus_last_house()
            self._board_canvas.hide_cursor()

    def on_new_action_activate(self, action, value):
        """Starts a new match on user request"""

        response = self._new_match_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            match = self._match_manager.load_new_match()

            if not self._match_manager.has_unsaved_changes():
                self._game_loop.abort_move()
                side = self._new_match_dialog.get_engine_side()
                self.set_engine_side(side)
                self.toggle_active_player(match)

    def on_open_action_activate(self, action, value):
        """Opens a match from a file"""

        uri = value.get_string() or None
        response = uri or self._open_match_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            uri = self._open_match_dialog.get_uri()

        if uri and isinstance(uri, str):
            self._game_loop.abort_move()
            self._match_manager.load_from_uri(uri)

    def on_rules_action_activate(self, action, value):
        """Show the game rules web site on the default browser"""

        uri = 'https://auale.joansala.com/rules/'
        Gtk.show_uri_on_window(None, uri, Gdk.CURRENT_TIME)

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

        self._board_canvas.show_match(match)
        self.refresh_view()

    def on_stop_action_activate(self, action, value):
        """Stops the current engine computations if any"""

        self._game_loop.abort_move()
        player = self._player_manager.get_human_player()
        match = self._match_manager.get_match()
        self._board_canvas.show_match(match)
        self.set_active_player(player, match)

    def on_undo_all_action_activate(self, action, value):
        """Undoes the all the performed match move"""

        self._game_loop.abort_move()
        player = self._player_manager.get_human_player()
        match = self._match_manager.get_match()
        match.undo_all_moves()
        self._board_canvas.show_match(match)
        self.set_active_player(player, match)

    def on_undo_action_activate(self, action, value):
        """Undoes the last performed match move"""

        self._game_loop.abort_move()
        player = self._player_manager.get_human_player()
        match = self._match_manager.get_match()
        match.undo_last_move()
        self._board_canvas.show_match(match)
        self.set_active_player(player, match)

    def on_redo_all_action_activate(self, action, value):
        """Redoes all the performed match moves"""

        self._game_loop.abort_move()
        player = self._player_manager.get_human_player()
        match = self._match_manager.get_match()
        match.redo_all_moves()
        self._board_canvas.show_match(match)
        self.set_active_player(player, match)

    def on_redo_action_activate(self, action, value):
        """Redoes the last performed match move"""

        self._game_loop.abort_move()
        player = self._player_manager.get_human_player()
        match = self._match_manager.get_match()
        match.redo_last_move()
        self._board_canvas.show_match(match)
        self.set_active_player(player, match)

    def on_engine_setting_changed(self, action, value):
        """Emitted when the engine command changes"""

        self.apply_engine_settings()

    def on_mute_setting_changed(self, action, value):
        """Toggles the mute on the sound context"""

        self.apply_sound_settings()

    def on_strength_setting_changed(self, action, value):
        """Emitted when the engine strength changed"""

        self.apply_strength_settings()

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
        self._board_canvas.set_rotation(rotation)
        action.set_state(value)

    def on_side_action_change_state(self, action, value):
        """Emitted on engine playing side changes"""

        engine_side = Side.value_of(value.get_string())
        self._player_manager.set_engine_side(engine_side)
        action.set_state(value)

        is_rotated = engine_side.rotation == Rotation.ROTATED
        value = GLib.Variant.new_boolean(is_rotated)
        rotate_action = self.lookup_action('rotate')
        rotate_action.change_state(value)

    def on_window_realize(self, window):
        """Emitted when the window is realized"""

        match = self._match_manager.get_match()

        self._player_manager.start_players()
        self._active_player = self._player_manager.get_human_player()
        self._board_canvas.show_match(match)

        self.apply_sound_settings()
        self.apply_strength_settings()
        self.connect_sound_signals()
        self.refresh_view()

    def on_window_delete_event(self, window, event):
        """Emitted when the user asks to close the window"""

        return self._match_manager.unload()

    def on_window_destroy(self, window):
        """Emitted to finalize the window"""

        self._player_manager.quit_players()
        self._sound_context.mute_context()

    def make_legal_move(self, match, move):
        """Makes a move if it is legal for the current match"""

        canvas = self._board_canvas

        if match.is_legal_move(move):
            match.add_move(move)
            canvas.animate_move(match)
            GLib.idle_add(self.refresh_view)

    def refresh_view(self):
        """Updates the state of the window"""

        match = self._match_manager.get_match()
        is_unsaved = self._match_manager.has_unsaved_changes()
        is_animating = self._board_canvas.is_animation_playing()
        is_engine = isinstance(self._active_player, Engine)
        is_human = isinstance(self._active_player, Human)
        is_ongoing_match = match and not match.has_ended()
        can_move = is_human and is_ongoing_match and not is_animating
        can_stop = is_engine and is_ongoing_match or is_animating
        can_undo = match and match.can_undo()
        can_redo = match and match.can_redo()

        self.lookup_action('undo').set_enabled(can_undo)
        self.lookup_action('redo').set_enabled(can_redo)
        self.lookup_action('undo-all').set_enabled(can_undo)
        self.lookup_action('redo-all').set_enabled(can_redo)
        self.lookup_action('move').set_enabled(can_move)
        self.lookup_action('stop').set_enabled(can_stop)

        self._unsaved_indicator.set_visible(is_unsaved)
        self._board_canvas.set_reactive(can_move)
