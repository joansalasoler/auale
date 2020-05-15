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

import math
import os
import shutil
import threading
import time
import webbrowser

from game import Match
from game import Oware
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import Gtk
from uci import Engine
from uci import Human
from uci import Strength
from utils import Utils

from .animator import Animator
from .canvas import Board
from .constants import Constants
from .loop import GameLoop
from .mixer import Mixer


class GTKView(object):
    """Represents an oware window"""

    __GLADE_PATH = Utils.resource_path('./res/glade/auale.ui')
    __CSS_PATH = Utils.resource_path('./res/glade/auale.css')
    __ENGINE_PATH = Utils.resource_path('./res/engine/Aalina.jar')

    def __init__(self, options={}):
        """Builds this interface and runs it"""

        # Interface options dictionary

        self._options = options

        # Game state attributes

        self._board_lock = threading.Event()
        self._human = Human()
        self._engine = self.start_new_engine()
        self._south = self._human
        self._north = self._engine
        self._filename = None
        self._match_changed = False
        self._strength = Strength.EASY

        # Interface objects

        self._match = Match(Oware)
        self._game_loop = GameLoop()
        self._canvas = Board()
        self._mixer = Mixer()
        self._animator = Animator(self._canvas, self._mixer)
        self._builder = Gtk.Builder()
        self._settings = Utils.get_gio_settings(Constants.APP_ID)

        # Initialize this Gtk interface

        self._add_css_provider(GTKView.__CSS_PATH)
        self._builder.set_translation_domain(Constants.APP_DOMAIN)
        self._builder.add_from_file(GTKView.__GLADE_PATH)
        self._builder.connect_signals(self)

        # References to the main objects

        self._hand_cursor = Gdk.Cursor(Gdk.CursorType.HAND2)
        self._window_group = Gtk.WindowGroup()

        self._main_window = self._builder.get_object('main_window')
        self._undo_group = self._builder.get_object('undo_actiongroup')
        self._redo_group = self._builder.get_object('redo_actiongroup')
        self._move_action = self._builder.get_object('move_now_action')
        self._stop_action = self._builder.get_object('stop_action')
        self._rotate_action = self._builder.get_object('rotate_toggleaction')
        self._spinner = self._builder.get_object('spinner')
        self._infobar = self._builder.get_object('infobar')
        self._about_dialog = self._builder.get_object('about_dialog')
        self._newmatch_dialog = self._builder.get_object('newmatch_dialog')
        self._properties_dialog = self._builder.get_object('properties_dialog')
        self._report_vbox = self._builder.get_object('report_vbox')
        self._report_label = self._builder.get_object('report_label')

        # Pack the objects together

        overlay = self._builder.get_object('board_overlay')
        overlay.add_overlay(self._infobar)
        overlay.add_overlay(self._report_vbox)
        overlay.add(self._canvas)

        self._canvas.grab_focus()
        self._canvas.set_board(self._match.get_board())

        self._window_group.add_window(self._main_window)
        self._window_group.add_window(self._about_dialog)
        self._window_group.add_window(self._newmatch_dialog)
        self._window_group.add_window(self._properties_dialog)

        self._builder.get_object('north_side_radiomenuitem').activate()

        # Connect event signals for custom objects

        self._connect_signals(self._animator)
        self._connect_signals(self._game_loop)
        self._connect_signals(self._canvas)

        self._canvas.connect('leave-notify-event', self.on_canvas_leave_notify_event)
        self._about_dialog.connect('delete-event', self.hide_on_delete)
        self._newmatch_dialog.connect('delete-event', self.hide_on_delete)
        self._properties_dialog.connect('delete-event', self.hide_on_delete)

        # Let's start everything

        self.load_settings()
        self.start_new_match()

    # Utility methods

    def _connect_signals(self, cobject):
        """Automatically connects the signals of an object"""

        for name in GObject.signal_list_names(cobject):
            attr = 'on_%s' % name.replace('-', '_')
            method = getattr(self, attr)
            cobject.connect(name, method)

    def _add_css_provider(self, path):
        """Adds a new class provider for the screen"""

        provider = Gtk.CssProvider()
        provider.load_from_path(path)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def load_settings(self):
        """Loads application settings"""

        # Remember and restore sound mute

        mute_action = self._builder.get_object('mute_toggleaction')

        self._settings.bind(
            'mute-sound', mute_action, 'active',
            Gio.SettingsBindFlags.DEFAULT
        )

        # Disable sound menu if SDL is not available

        if self._mixer.is_disabled():
            mitem = self._builder.get_object('mute_menuitem')
            mitem.set_sensitive(False)

        # Retrieve last used computer strength

        value = self._settings.get_int('strength')
        self._update_strength_menu(value)

    def start_new_engine(self):
        """Initializes a new engine process"""

        try:
            engine = Engine(self.get_engine_command())
            engine.connect('failure', self.on_engine_failure)
        except BaseException:
            title = _('Computer player is disabled')
            message = _('Could not start the engine')
            self.show_error_message(title, message)

        return engine or Human()

    def get_engine_command(self):
        """Finds a command to execute the engine"""

        if 'command' in self._options:
            command = self._options['command'].split()
            return (shutil.which(command[0]),)

        path = os.path.abspath(GTKView.__ENGINE_PATH)
        command = (shutil.which('java'), '-jar', path)

        return command

    def _update_strength_menu(self, value):
        """Updates the active strength menu item"""

        if value == Strength.EASY.ordinal:
            item = self._builder.get_object('easy_strength_radiomenuitem')
            item.activate()
        elif value == Strength.MEDIUM.ordinal:
            item = self._builder.get_object('medium_strength_radiomenuitem')
            item.activate()
        elif value == Strength.HARD.ordinal:
            item = self._builder.get_object('hard_strength_radiomenuitem')
            item.activate()
        elif value == Strength.EXPERT.ordinal:
            item = self._builder.get_object('expert_strength_radiomenuitem')
            item.activate()

    def hide_on_delete(self, widget, event):
        """Hides a window and prevents it from being destroyed"""

        widget.hide()

        return True

    def user_can_move(self):
        """Returns true if the user is allowed to move"""

        return not (
            self._board_lock.is_set() or
            self._game_loop.is_engine_searching() or
            self._match.has_ended()
        )

    def get_current_player(self):
        """Returns the player to move"""

        if self._match.has_ended():
            return None

        if self._match.get_turn() == Oware.SOUTH:
            return self._south

        return self._north

    def show_tips(self):
        """Shows help messages at startup"""

        if not self._settings.get_boolean('show-tips'):
            return

        self.show_message(
            _("How to play oware"),
            _("You can find the <a href=\"%s\" title=\"Oware abapa rules\">"
              "rules of the game</a> on our website. Have fun playing!")
            % Constants.RULES_URL, Constants.HELP_ICON
        )

        self._settings.set_boolean('show-tips', False)

    def get_window(self):
        """Return the main window for this view"""

        return self._main_window

    # Event handlers

    def on_main_window_delete(self, widget, event):
        """Confirm to save changes if any"""

        if self._match_changed == False:
            return False

        dialog = self.new_unsaved_confirmation_dialog(
            _("Do you want to save the match before closing?"),
            _("The current match has unsaved changes. Your changes will "
              "be lost if you don't save them."),
            _("Close without saving")
        )

        dialog.connect('response', self.on_main_window_delete_response)
        dialog.show()

        return True

    def on_main_window_delete_response(self, dialog, response):
        """Main window delete-event response handler"""

        dialog.destroy()

        if response == Gtk.ResponseType.ACCEPT:
            self._main_window.destroy()
        elif response == Gtk.ResponseType.REJECT:
            dialog = self.new_save_dialog()

            if self._filename is not None:
                dialog.set_filename(self._filename)

            dialog.connect('response', self.on_save_and_quit_response)
            dialog.show()

    def on_save_and_quit_response(self, dialog, response):
        """Main window save and quit dialog response handler"""

        if response == Gtk.ResponseType.ACCEPT:
            self.save_match(dialog.get_filename())

            if self._match_changed == False:
                dialog.destroy()
                self._main_window.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def on_main_window_destroy(self, widget):
        """Quits this interface"""

        self._settings.sync()
        self._mixer.stop_mixer()
        self._north.quit()
        self._south.quit()

    def on_main_window_key_press_event(self, widget, event):
        """Interprets key presses"""

        # Modifier keys are not allowed

        modifiers = Gtk.accelerator_get_default_mod_mask()

        if event.state & modifiers:
            return

        # Forward and rewind actions

        if event.keyval == Gdk.KEY_End:
            action = self._builder.get_object("redo_all_action")
            action.activate()
            return

        if event.keyval == Gdk.KEY_Home:
            action = self._builder.get_object("undo_all_action")
            action.activate()
            return

        # Interpret the move

        if not self.user_can_move():
            return

        move_keys = (
            (Gdk.KEY_A, Gdk.KEY_a),
            (Gdk.KEY_B, Gdk.KEY_b),
            (Gdk.KEY_C, Gdk.KEY_c),
            (Gdk.KEY_D, Gdk.KEY_d),
            (Gdk.KEY_E, Gdk.KEY_e),
            (Gdk.KEY_F, Gdk.KEY_f)
        )

        turn = self._match.get_turn()

        for move in range(len(move_keys)):
            if event.keyval in move_keys[move]:
                house = move + (turn == -1 and 6 or 0)
                if self._match.is_legal_move(house):
                    self.on_move_received(self._game_loop, house)
                break

    def on_house_button_press_event(self, widget, house):
        """Catches mouse press events on a house"""

        if self.user_can_move():
            if self._match.is_legal_move(house):
                self.on_move_received(self._game_loop, house)

    def on_house_enter_notify_event(self, widget, house):
        """Catches mouse enter notifications on a house"""

        if not self.user_can_move():
            return

        window = self._main_window.get_window()

        if self._match.is_legal_move(house):
            window.set_cursor(self._hand_cursor)
            widget.set_active(house)
            widget.queue_draw()
        else:
            window.set_cursor(None)
            widget.set_active(None)

    def on_house_leave_notify_event(self, widget, house):
        """Catches mouse leave notifications on a house"""

        window = self._main_window.get_window()
        window.set_cursor(None)
        widget.set_active(None)
        widget.queue_draw()

    def on_canvas_leave_notify_event(self, widget, event):
        """Emited when the mouse leaves the drawin area"""

        window = self._main_window.get_window()
        window.set_cursor(None)
        widget.set_active(None)

    def on_new_activate(self, widget):
        """On new game activate"""

        if self._match_changed == False:
            self._newmatch_dialog.show()
            return

        dialog = self.new_unsaved_confirmation_dialog(
            _("Do you want to save the current match?"),
            _("The current match has unsaved changes. Your changes will "
              "be lost if you don't save them."),
            _("Discard unsaved changes")
        )

        dialog.connect('response', self.on_new_activate_response)
        dialog.show()

    def on_new_activate_response(self, dialog, response):
        """New match action response handler"""

        dialog.destroy()

        if response == Gtk.ResponseType.REJECT:
            dialog = self.new_save_dialog()

            if self._filename is not None:
                dialog.set_filename(self._filename)

            dialog.connect('response', self.on_save_and_new_response)
            dialog.show()
        elif response != Gtk.ResponseType.CANCEL:
            self._newmatch_dialog.show()

    def on_save_and_new_response(self, dialog, response):
        """New match response handler"""

        if response == Gtk.ResponseType.ACCEPT:
            self.save_match(dialog.get_filename())

            if self._match_changed == False:
                dialog.destroy()
                self._newmatch_dialog.show()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def on_newmatch_dialog_response(self, dialog, response):
        """Handles the new match dialog responses"""

        if response == Gtk.ResponseType.OK:
            self._game_loop.abort_request()
            self._animator.stop_move()
            self._mixer.on_game_start()

            player = self.get_current_player()

            self.start_new_match()
            self.set_active_player(player)
            self.refresh_view()

        self._newmatch_dialog.hide()

    def on_open_activate(self, widget):
        """Open a match file dialog"""

        if self._match_changed == False:
            dialog = self.new_open_dialog()
            dialog.connect('response', self.on_open_dialog_response)
            dialog.show()
        else:
            dialog = self.new_unsaved_confirmation_dialog(
                _("Do you want to save the current match?"),
                _("The current match has unsaved changes. Your changes will "
                  "be lost if you don't save them."),
                _("Discard unsaved changes")
            )

            dialog.connect('response', self.on_open_activate_response)
            dialog.show()

    def on_open_activate_response(self, dialog, response):
        """Open match action response handler"""

        dialog.destroy()

        if response == Gtk.ResponseType.REJECT:
            dialog = self.new_save_dialog()

            if self._filename is not None:
                dialog.set_filename(self._filename)

            dialog.connect('response', self.on_save_and_open_response)
            dialog.show()
        elif response != Gtk.ResponseType.CANCEL:
            dialog = self.new_open_dialog()
            dialog.connect('response', self.on_open_dialog_response)
            dialog.show()

    def on_open_dialog_response(self, dialog, response):
        """Handles open dialogs responses"""

        if response == Gtk.ResponseType.ACCEPT:
            self._game_loop.abort_request()
            self._animator.stop_move()
            self.open_match(dialog.get_filename())
            self.set_active_player(self._human)
            self.refresh_view()

        dialog.destroy()

    def on_save_and_open_response(self, dialog, response):
        """Open match response handler"""

        if response == Gtk.ResponseType.ACCEPT:
            self.save_match(dialog.get_filename())

            if self._match_changed == False:
                dialog.destroy()
                dialog = self.new_open_dialog()
                dialog.connect('response', self.on_open_dialog_response)
                dialog.show()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def on_save_activate(self, widget):
        """Save a match file dialog"""

        if widget.get_name() == 'save_action':
            if self._filename is not None:
                self.save_match(self._filename)
                return

        dialog = self.new_save_dialog()

        if widget.get_name() == 'saveas_action':
            if self._filename is not None:
                dialog.set_filename(self._filename)

        dialog.connect('response', self.on_save_dialog_response)
        dialog.show()

    def on_save_dialog_response(self, dialog, response):
        """Handles save dialogs responses"""

        if response == Gtk.ResponseType.ACCEPT:
            self.save_match(dialog.get_filename())

        if response == Gtk.ResponseType.CANCEL \
        or self._match_changed == False:
            dialog.destroy()

    def on_open_recent_item_activated(self, widget):
        """Open a recently used file"""

        if self._match_changed == False:
            self.open_recent_match()
            return

        dialog = self.new_unsaved_confirmation_dialog(
            _("Do you want to save the current match?"),
            _("The current match has unsaved changes. Your changes will "
              "be lost if you don't save them."),
            _("Discard unsaved changes")
        )

        dialog.connect('response', self.on_open_recent_response)
        dialog.show()

    def on_open_recent_response(self, dialog, response):
        """Open recent match action response handler"""

        dialog.destroy()

        if response == Gtk.ResponseType.REJECT:
            dialog = self.new_save_dialog()

            if self._filename is not None:
                dialog.set_filename(self._filename)

            dialog.connect('response', self.on_save_and_open_recent)
            dialog.show()
        elif response != Gtk.ResponseType.CANCEL:
            self.open_recent_match()

    def on_save_and_open_recent(self, dialog, response):
        """Open match response handler"""

        if response == Gtk.ResponseType.ACCEPT:
            self.save_match(dialog.get_filename())

            if self._match_changed == False:
                dialog.destroy()
                self.open_recent_match()
        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def open_recent_match(self):
        """Open the last chosen recent match file"""

        widget = self._builder.get_object('open_recent_action')
        uri = widget.get_current_uri()
        path = GLib.filename_from_uri(uri)[0]

        self._game_loop.abort_request()
        self._animator.stop_move()
        self.open_match(path)
        self.set_active_player(self._human)
        self.refresh_view()

    def on_file_changed(self, path):
        """File path changed event"""

        # Update current file path and status

        self._filename = path
        self._match_changed = False
        self._report_label.set_text('')

        if path is None:
            name = _("Unsaved match")
            title = '%s - %s' % (Constants.APP_NAME, name)
            self._main_window.set_title(title)
            return

        # Set window properties

        name = os.path.basename(path)
        title = '%s - %s' % (Constants.APP_NAME, name)
        self._main_window.set_title(title)

        # Add the path to recent files

        uri = GLib.filename_to_uri(path, None)
        manager = Gtk.RecentManager.get_default()
        manager.add_item(uri)

    def on_rotate_activate(self, widget):
        """Rotates the current canvas board"""

        # If the window is not visible, just rotate the canvas

        if not self._main_window.is_visible() \
        and self._canvas.get_rotation() == 0.0:
            self._canvas.rotate(math.pi)
            return

        # Animate a board roation

        window = self._main_window.get_window()
        window.set_cursor(None)
        self._rotate_action.set_sensitive(False)
        self._animator.rotate_board()

    def on_mute_activate(self, widget):
        """Enables and disables sound effects"""

        self._mixer.toggle_mute()

    def on_quit_activate(self, widget):
        """Quits this interface"""

        event = Gdk.Event.new(Gdk.EventType.DELETE)

        if not self._main_window.emit('delete-event', event):
            self._main_window.destroy()

    def on_home_activate(self, widget):
        """Start home page"""

        webbrowser.open(Constants.HOME_URL, autoraise=True)

    def on_support_activate(self, widget):
        """Start help and support forum"""

        webbrowser.open(Constants.HELP_URL, autoraise=True)

    def on_rules_activate(self, widget):
        """Show game rules"""

        webbrowser.open(Constants.RULES_URL, autoraise=True)

    def on_properties_activate(self, widget):
        """Show a match tags edition dialog"""

        protected_tags = ('FEN', 'Result', 'Variant')

        store = self._builder.get_object('properties_liststore')
        view = self._builder.get_object('properties_treeview')
        tags = self._match.get_tags()

        store.clear()

        for tag, value in tags:
            if tag not in protected_tags:
                titer = store.append((_(tag), value))

        view.set_cursor(0)
        view.grab_focus()

        self._properties_dialog.show()

    def on_properties_dialog_response(self, widget, response):
        """Handles the properties dialog responses"""

        if response == Gtk.ResponseType.ACCEPT:
            protected_tags = ('FEN', 'Result', 'Variant')

            store = self._builder.get_object('properties_liststore')
            tags = self._match.get_tags()

            path = 0

            for tag, value in tags:
                if tag in protected_tags:
                    continue

                siter = store.get_iter(path)
                new_value = store.get_value(siter, 1)
                path += 1

                if new_value == value:
                    continue

                self._match.set_tag(tag, new_value)
                self._match_changed = True

            self.refresh_infobar()

        self._properties_dialog.hide()

    def on_properties_treeview_row_activated(self, widget, path, column):
        """Starts property edition on activating a row"""

        column = self._builder.get_object('value_treeviewcolumn')
        cell = self._builder.get_object('value_cellrenderertext')
        column.focus_cell(cell)
        widget.set_cursor(path, column, True)

    def on_property_edited(self, widget, path, new_text):
        """Called after editing a match property"""

        store = self._builder.get_object('properties_liststore')
        siter = store.get_iter(path)
        store.set_value(siter, 1, new_text.strip())

    def on_about_activate(self, widget):
        """Shows the about dialog"""

        self._about_dialog.show()

    def on_about_dialog_response(self, widget, response):
        """Handles the about dialog response"""

        self._about_dialog.hide()

    def on_move_now_activate(self, widget):
        """Asks the engine to perform a move"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self.set_active_player(self._engine)

    def on_stop_activate(self, widget):
        """Asks the engine to stop thinking"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self._board_lock.clear()
        self.refresh_view()

    def on_undo_activate(self, widget):
        """Undoes the last move"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self._match.undo_last_move()
        self._board_lock.clear()
        self.refresh_view()

    def on_redo_activate(self, widget):
        """Redoes the last move"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self._match.redo_last_move()
        self._board_lock.clear()
        self.refresh_view()

    def on_undo_all_activate(self, widget):
        """Undoes all the performed moves"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self._match.undo_all_moves()
        self._board_lock.clear()
        self.refresh_view()

    def on_redo_all_activate(self, widget):
        """Redoes all the undone moves"""

        self._game_loop.abort_request()
        self._animator.stop_move()
        self._match.redo_all_moves()
        self._board_lock.clear()
        self.refresh_view()

    def on_side_menuitem_toggled(self, widget):
        """Emitted when the user sets the engine player"""

        if widget.get_active():
            name = widget.get_name()

            if isinstance(self._south, Engine):
                if isinstance(self._north, Engine):
                    self._north.quit()

            if name == 'south-side-menuitem':
                self._south = self._engine
                self._north = self._human
            elif name == 'north-side-menuitem':
                self._south = self._human
                self._north = self._engine
            elif name == 'neither-side-menuitem':
                self._south = self._human
                self._north = self._human
            elif name == 'both-side-menuitem':
                self._south = self._engine
                self._north = self.start_new_engine()

    def on_strength_menuitem_toggled(self, widget):
        """Emitted when the user sets the engine strength"""

        if widget.get_active():
            name = widget.get_name()

            if name == 'easy-menuitem':
                self._strength = Strength.EASY
            elif name == 'medium-menuitem':
                self._strength = Strength.MEDIUM
            elif name == 'hard-menuitem':
                self._strength = Strength.HARD
            elif name == 'expert-menuitem':
                self._strength = Strength.EXPERT

            ordinal = self._strength.ordinal
            self._settings.set_int('strength', ordinal)

    def on_newgame_button_clicked(self, widget):
        """Emitted on a new game button activation"""

        name = widget.get_name()

        if name == 'newgame-south-button':
            item = self._builder.get_object('north_side_radiomenuitem')
            item.set_active(True)
        elif name == 'newgame-north-button':
            item = self._builder.get_object('south_side_radiomenuitem')
            item.set_active(True)
        elif name == 'newgame-edit-button':
            item = self._builder.get_object('neither_side_radiomenuitem')
            item.set_active(True)
        elif name == 'newgame-watch-button':
            item = self._builder.get_object('both_side_radiomenuitem')
            item.set_active(True)

        self._newmatch_dialog.response(Gtk.ResponseType.OK)

    def on_rotate_animation_finished(self, animator):
        """Called after a board rotation animation"""

        self._rotate_action.set_sensitive(True)

        if self.user_can_move():
            self._canvas.update_hovered()
            self.refresh_active_house()

    def on_move_received(self, game_loop, move):
        """Adds a move to the match and animates it"""

        window = self._main_window.get_window()

        try:
            if window is not None:
                window.set_cursor(None)
                self._board_lock.set()
                self._animator.make_move(self._match, move)
                self._match.add_move(move)
                self._match_changed = True
        except BaseException:
            self._board_lock.clear()
            self.show_error_message(
                _("Error"),
                _("The received move is not valid")
            )

        self.refresh_actions()

    def on_info_received(self, game_loop, comment):
        """Shows a player message below the board"""

        self._report_label.set_markup(comment)

    def on_engine_failure(self, engine, reason):
        """Handles unexpected engine termination errors"""

        if engine == self._engine:
            self._engine = Human()

        if engine == self._south:
            self._south = self._human

        if engine == self._north:
            self._north = self._human

        title = _('Computer player is disabled')
        GLib.idle_add(self.show_error_message, title, _(reason))

    def on_move_animation_finished(self, animator):
        """Called after a move animation"""

        player = self.get_current_player()
        self.set_active_player(player)

    def set_active_player(self, player):
        """Sets a new player to move on the current match"""

        if isinstance(player, Engine):
            player.set_playing_strength(self._strength)

        self._game_loop.request_move(player, self._match)
        self._board_lock.clear()
        self.refresh_state()

    # Update view methods

    def refresh_actions(self):
        """Set actions properties"""

        can_undo = self._match.can_undo()
        can_redo = self._match.can_redo()

        self._undo_group.set_sensitive(can_undo)
        self._redo_group.set_sensitive(can_redo)

        if self._match.has_ended():
            self._move_action.set_sensitive(False)
            self._stop_action.set_sensitive(False)
            self._spinner.stop()
        elif self._board_lock.is_set():
            self._move_action.set_sensitive(False)
            self._stop_action.set_sensitive(False)
            self._spinner.stop()
        elif self._game_loop.is_engine_searching():
            self._move_action.set_sensitive(False)
            self._stop_action.set_sensitive(True)
            self._spinner.start()
        else:
            self._move_action.set_sensitive(True)
            self._stop_action.set_sensitive(False)
            self._spinner.stop()

        if self._board_lock.is_set():
            if isinstance(self.get_current_player(), Engine):
                self._stop_action.set_sensitive(True)

    def refresh_active_house(self):
        """Highlights the currently hovered house"""

        window = self._main_window.get_window()
        window.set_cursor(None)
        self._canvas.set_active(None)

        if self.user_can_move():
            house = self._canvas.get_hovered()

            if self._match.is_legal_move(house):
                window.set_cursor(self._hand_cursor)
                self._canvas.set_active(house)

    def refresh_highlight(self):
        """Highlights the last performed move"""

        try:
            move = self._match.get_previous_move()
            self._canvas.set_highlight(move)
        except IndexError:
            self._canvas.set_highlight(None)

    def refresh_infobar(self):
        """Sets information bar properties"""

        def _is_empty(value):
            return value == '?' or not value

        # If it's the start position show match information

        if self._match.can_undo() == False:
            title = ''
            message = ''

            event = self._match.get_tag('Event')
            south = self._match.get_tag('South')
            north = self._match.get_tag('North')
            result = self._match.get_tag('Result')
            description = self._match.get_tag('Description')

            if self._filename is not None:
                if not _is_empty(event):
                    title = '%s' % event

            if not _is_empty(description):
                message = description
            elif not _is_empty(south) and not _is_empty(north):
                message = '%s - %s' % (south, north)

            if not _is_empty(result) and result != '*':
                message = '%s (%s)' % (message, result)

            if title or message:
                icon = Constants.FOLDER_ICON if self._filename else Constants.CREATE_ICON
                self.show_message(title or _("Match"), message, icon)
            elif self._infobar.is_visible():
                self._infobar.set_visible(False)

        # If the game ended, show a result message

        elif self._match.has_ended():
            winner = self._match.get_winner()

            if Oware.SOUTH == winner:
                title = _("South has won")
                description = _("The player gathered more than 24 seeds")
            elif Oware.NORTH == winner:
                title = _("North has won")
                description = _("The player gathered more than 24 seeds")
            elif Oware.DRAW == winner:
                title = _("This match was drawn")
                description = _("Players gathered an equal number of seeds")

            self.show_message(title, description)

        # If the match has comments, show them

        elif self._match.get_comment() is not None:
            comment = GLib.markup_escape_text(self._match.get_comment())
            self.show_message(None, comment, Constants.COMMENT_ICON)

        # Otherwise, hide the infobar

        else:
            self._infobar.set_visible(False)

    def refresh_state(self):
        """Refresh actions and board state"""

        if self._main_window.is_visible():
            self.refresh_actions()
            self.refresh_infobar()

            if self.user_can_move():
                self._canvas.update_hovered()
                self.refresh_active_house()

    def refresh_view(self):
        """Updates this interface"""

        # Refresh this window properties

        self.refresh_highlight()
        self.refresh_active_house()
        self.refresh_actions()
        self.refresh_infobar()

        # Redraw the canvas

        board = self._match.get_board()
        self._canvas.set_board(board)
        self._canvas.queue_draw()

    def show_message(self, title, message, icon=Constants.INFORMATION_ICON):
        """Shows a message to the user"""

        label = self._builder.get_object('infobar-label')
        image = self._builder.get_object('infobar-image')

        if not title:
            markup = '%s' % message
        elif not message:
            markup = '<b>%s</b>' % title
        else:
            markup = '<b>%s</b>: %s' % (title, message)

        label.set_markup(markup)
        image.set_from_file(Utils.resource_path(icon))

        self._infobar.set_message_type(Gtk.MessageType.OTHER)
        self._infobar.set_visible(True)

    def show_error_message(self, title, message, icon=Constants.ERROR_ICON):
        """Shows an error message to the user"""

        self.show_message(title, message, icon)

    def new_confirmation_dialog(self, title, message, text, discard):
        """Creates a new confirmation dialog"""

        dialog = Gtk.MessageDialog(
            parent=self._main_window,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
        )

        self._window_group.add_window(dialog)

        dialog.add_button(discard, Gtk.ResponseType.ACCEPT)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.REJECT)

        dialog.set_property('title', title)
        dialog.set_property('text', message)
        dialog.set_property('secondary-text', text)

        msgarea = dialog.get_message_area()

        for child in msgarea.get_children():
            if isinstance(child, Gtk.Label):
                child.set_property("max-width-chars", 48)

        return dialog

    def new_unsaved_confirmation_dialog(self, message, text, discard):
        """Creates a new unsaved-match confirmation dialog"""

        dialog = self.new_confirmation_dialog(
            _("Match with unsaved changes"),
            message, text, discard
        )

        return dialog

    def new_open_dialog(self):
        """Create a new open match file dialog"""

        dialog = Gtk.FileChooserDialog(
            title=_("Open an oware match"),
            parent=self._main_window,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT
            )
        )

        self._window_group.add_window(dialog)

        oware_filter = Gtk.FileFilter()
        oware_filter.set_name(_("Oware match files"))
        oware_filter.add_mime_type('text/x-oware-ogn')
        oware_filter.add_pattern('*.ogn')

        files_filter = Gtk.FileFilter()
        files_filter.set_name(_("Any files"))
        files_filter.add_pattern('*')

        dialog.add_filter(oware_filter)
        dialog.add_filter(files_filter)
        dialog.set_modal(True)

        return dialog

    def new_save_dialog(self):
        """Create a new save match file dialog"""

        dialog = Gtk.FileChooserDialog(
            title=_("Save current match"),
            parent=self._main_window,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT
            )
        )

        self._window_group.add_window(dialog)

        oware_filter = Gtk.FileFilter()
        oware_filter.set_name(_("Oware match files"))
        oware_filter.add_mime_type('text/x-oware-ogn')
        oware_filter.add_pattern('*.ogn')

        dialog.add_filter(oware_filter)
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(_("untitled.ogn"))
        dialog.set_modal(True)

        return dialog

    def open_match(self, path):
        """Open a match file and sets it as current"""

        try:
            self._match.load(path)
            self.on_file_changed(path)
            item = self._builder.get_object('neither_side_radiomenuitem')
            item.set_active(True)
            self._match.undo_all_moves()
        except Exception as e:
            self.show_error_message(
                _("Error opening match"),
                _("Match file cannot be opened")
            )

        self._board_lock.clear()

    def save_match(self, path):
        """Saves the current match to a file"""

        try:
            self._match.save(path)
            self.on_file_changed(path)
            self.refresh_infobar()
        except Exception as e:
            self.show_error_message(
                _("Error saving match"),
                _("Cannot save current match")
            )

    def start_new_match(self):
        """Starts a new match"""

        # Start a new match

        self._match.new_match()
        self._match.set_tag('Event', _("Untitled"))
        self._match.set_tag('Date', time.strftime('%Y.%m.%d'))
        self._match.set_tag('South', self._south.get_player_name())
        self._match.set_tag('North', self._north.get_player_name())

        # Rotate the board if needed

        south_is_human = isinstance(self._south, Human)
        north_is_human = isinstance(self._north, Human)

        if north_is_human and not south_is_human:
            if self._canvas.get_rotation() != math.pi:
                self._rotate_action.activate()
        elif south_is_human and not north_is_human:
            if self._canvas.get_rotation() != 0.0:
                self._rotate_action.activate()
        else:
            if self._canvas.get_rotation() != 0.0:
                self._rotate_action.activate()

        # Notify this view of a file change

        self.on_file_changed(None)
        self.refresh_infobar()
