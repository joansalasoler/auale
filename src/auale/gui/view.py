#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014-2015 Joan Sala Soler <contact@joansala.com>
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

import os, math, time, sys
import threading
import webbrowser
import util

from game import *
from gui import *
from uci import UCIPlayer
from gi.repository import Gio, GLib, Gdk, Gtk, GObject


class GTKView(object):
    """Represents an oware window"""
    
    __GLADE_PATH = util.resource_path('./res/glade/auale.ui')
    __CSS_PATH = util.resource_path('./res/glade/auale.css')
    __ENGINE_PATH = util.resource_path('./res/engine/Aalina.jar')
    
    
    def __init__(self):
        """Builds this interface and runs it"""
        
        # Game state attributes
        
        self._locked = threading.Event()
        self._engine = None
        self._south = None
        self._north = None
        self._filename = None
        self._match_changed = False
        self._strength = UCIPlayer.Strength.EASY
        
        # Interface objects
        
        self._match = Match(Oware)
        self._loop = GameLoop()
        self._canvas = Board()
        self._mixer = Mixer()
        self._animator = Animator(self._canvas, self._mixer)
        self._builder = Gtk.Builder()
        self._settings = util.get_gio_settings(App.ID)
        
        # Initialize this Gtk interface
        
        self._add_css_provider(GTKView.__CSS_PATH)
        self._builder.set_translation_domain(App.DOMAIN)
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
        
        # Pack the objects together
        
        overlay = Gtk.Overlay()
        overlay.add(self._canvas)
        overlay.add_overlay(self._infobar)
        
        vbox = self._builder.get_object('window_vbox')
        vbox.add(overlay)
        vbox.reorder_child(overlay, 2)
        
        self._canvas.grab_focus()
        self._canvas.set_board(self._match.get_board())
        
        self._window_group.add_window(self._main_window)
        self._window_group.add_window(self._about_dialog)
        self._window_group.add_window(self._newmatch_dialog)
        self._window_group.add_window(self._properties_dialog)
        
        # Connect event signals for custom objects
        
        self._connect_signals(self._animator)
        self._connect_signals(self._loop)
        self._connect_signals(self._canvas)
        
        self._canvas.connect('leave-notify-event',
            self.on_canvas_leave_notify_event)
        
        self._about_dialog.connect('delete-event', self.hide_on_delete)
        self._newmatch_dialog.connect('delete-event', self.hide_on_delete)
        self._properties_dialog.connect('delete-event', self.hide_on_delete)
        
        # Let's start everything
        
        self._load_settings()
        self._start_engine()
        self._loop.start()
        self.start_match()
    
    
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
    
    
    def _load_settings(self):
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
        
        strength = self._settings.get_int('strength')
        self._update_strength_menu(strength)
    
    
    def _start_engine(self):
        """Initializes the engine process"""
        
        try:
            path = None
            
            if 'linux' in sys.platform:
                path = util.which('aalina')
            
            if path is None:
                command = [
                    util.which('java'), '-jar',
                    os.path.abspath(GTKView.__ENGINE_PATH)
                ]
            else:
                command = [path]
            
            self._engine = UCIPlayer(command, Oware)
            self._north = self._engine
        except Exception as e:
            message = self._get_exception_message(e)
            
            self.show_error_dialog(
                _('Could not start the engine'),
                _('Computer player is disabled'),
                '%s: %s' % (
                    _('Could not start the engine'),
                    _(message)
                )
            )
    
    
    def _update_strength_menu(self, strength):
        """Updates the active strength menu item"""
        
        if UCIPlayer.Strength.EASY == strength:
            item = self._builder.get_object('easy_strength_radiomenuitem')
            item.activate()
        elif UCIPlayer.Strength.MEDIUM == strength:
            item = self._builder.get_object('medium_strength_radiomenuitem')
            item.activate()
        elif UCIPlayer.Strength.HARD == strength:
            item = self._builder.get_object('hard_strength_radiomenuitem')
            item.activate()
        elif UCIPlayer.Strength.EXPERT == strength:
            item = self._builder.get_object('expert_strength_radiomenuitem')
            item.activate()
    
    
    def hide_on_delete(self, widget, event):
        """Hides a window and prevents it from being destroyed"""
        
        widget.hide()
        
        return True
    
    def user_can_move(self):
        """Returns true if the user is allowed to move"""
        
        return not (
            self._locked.is_set() or \
            self._loop.is_thinking() or \
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
        
        self.show_info_bar(
            _("How to play oware"),
            _("You can find the <a href=\"%s\" title=\"Oware abapa rules\">"
              "rules of the game</a> on our website. Have fun playing!")
            % App.RULES_URL, 'help'
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
        
        self._loop.stop()
        
        if self._engine is not None:
            self._engine.quit()
        
        self._settings.sync()
        self._mixer.stop_mixer()
    
    
    def on_main_window_key_press_event(self, widget, event):
        """Interprets key presses"""
        
        # Modifier keys are not allowed
        
        modifiers = Gtk.accelerator_get_default_mod_mask();
        
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
                    self.on_move_received(self._loop, house)
                break
    
    
    def on_house_button_press_event(self, widget, house):
        """Catches mouse press events on a house"""
        
        if self.user_can_move():
            if self._match.is_legal_move(house):
                self.on_move_received(self._loop, house)
    
    
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
            self._loop.abort()
            self._animator.stop_move()
            
            self.start_match()
            self.reset_engine()
            self.refresh_view()
            
            self._mixer.on_game_start()
            
            player = self.get_current_player()
            
            if player is None:
                self._locked.clear()
            self._loop.request_move(player)
        
        self._newmatch_dialog.hide()
    
    
    def on_open_activate(self, widget):
        """Open a match file dialog"""
        
        if self._match_changed == False:
            return
        
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
            self._loop.abort()
            self._animator.stop_move()
            self.open_match(dialog.get_filename())
            self.reset_engine()
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
        
        self._loop.abort()
        self._animator.stop_move()
        self.open_match(path)
        self.reset_engine()
        self.refresh_view()
    
    
    def on_file_changed(self, path):
        """File path changed event"""
        
        # Update current file path and status
        
        self._filename = path
        self._match_changed = False
        
        if path is None:
            name = _("Unsaved match")
            title = '%s - %s' % (App.NAME, name)
            self._main_window.set_title(title)
            return
        
        # Set window properties
        
        name = os.path.basename(path)
        title = '%s - %s' % (App.NAME, name)
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
        
        webbrowser.open(App.HOME_URL, autoraise = True)
    
    
    def on_support_activate(self, widget):
        """Start help and support forum"""
        
        webbrowser.open(App.HELP_URL, autoraise = True)
        
        
    def on_rules_activate(self, widget):
        """Show game rules"""
        
        webbrowser.open(App.RULES_URL, autoraise = True)
    
    
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
        
        self._loop.abort()
        self._animator.stop_move()
        
        self._engine.set_strength(self._strength)
        self._engine.set_position(self._match)
        self._loop.request_move(self._engine)
        
        self.refresh_view()
    
    
    def on_stop_activate(self, widget):
        """Asks the engine to stop thinking"""
        
        self._loop.abort()
        self._animator.stop_move()
        self.refresh_view()
        self._locked.clear()
    
    
    def on_undo_activate(self, widget):
        """Undoes the last move"""
        
        self._loop.abort()
        self._animator.stop_move()
        self._match.undo_last_move()
        self.refresh_view()
        self._locked.clear()
    
    
    def on_redo_activate(self, widget):
        """Redoes the last move"""
        
        self._loop.abort()
        self._animator.stop_move()
        self._match.redo_last_move()
        self.refresh_view()
        self._locked.clear()
    
    
    def on_undo_all_activate(self, widget):
        """Undoes all the performed moves"""
        
        self._loop.abort()
        self._animator.stop_move()
        self._match.undo_all_moves()
        self.refresh_view()
        self._locked.clear()
    
    
    def on_redo_all_activate(self, widget):
        """Redoes all the undone moves"""
        
        self._loop.abort()
        self._animator.stop_move()
        self._match.redo_all_moves()
        self.refresh_view()
        self._locked.clear()
    
    
    def on_side_menuitem_toggled(self, widget):
        """Emitted when the user sets the engine player"""
        
        if not widget.get_active(): return
        name = widget.get_name()
        
        if name == 'south-side-menuitem':
            self._south = self._engine
            self._north = None
        elif name == 'north-side-menuitem':
            self._south = None
            self._north = self._engine
        elif name == 'both-side-menuitem':
            self._south = self._engine
            self._north = self._engine
        elif name == 'neither-side-menuitem':
            self._south = None
            self._north = None
    
    
    def on_strength_menuitem_toggled(self, widget):
        """Emitted when the user sets the engine strength"""
        
        if not widget.get_active(): return
        name = widget.get_name()
        
        if name == 'easy-menuitem':
            self._strength = UCIPlayer.Strength.EASY
        elif name == 'medium-menuitem':
            self._strength = UCIPlayer.Strength.MEDIUM
        elif name == 'hard-menuitem':
            self._strength = UCIPlayer.Strength.HARD
        elif name == 'expert-menuitem':
            self._strength = UCIPlayer.Strength.EXPERT
        
        self._settings.set_int('strength', self._strength)
    
    
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
    
    
    def on_move_received(self, loop, move):
        """Adds a move to the match and animates it"""
        
        window = self._main_window.get_window()
        window.set_cursor(None)
        
        try:
            self._locked.set()
            self._animator.make_move(self._match, move)
            self._match.add_move(move)
            self._match_changed = True
        except:
            self._locked.clear()
            self.show_error_bar(
                _("Error"),
                _("The received move is not valid")
            )
        
        self.refresh_actions()
    
    
    def on_move_animation_finished(self, animator):
        """Called after a move animation"""
        
        player = self.get_current_player()
        
        self._engine.set_strength(self._strength)
        self._engine.set_position(self._match)
        self._loop.request_move(player)
    
    
    def on_state_changed(self, loop):
        """Emited when the game loop state changes"""
        
        self._locked.clear()
        self.refresh_state()
    
    
    # Update view methods
    
    def refresh_actions(self):
        """Set actions properties"""
        
        can_undo = self._match.can_undo()
        can_redo = self._match.can_redo()
        self._undo_group.set_sensitive(can_undo)
        self._redo_group.set_sensitive(can_redo)
        
        if self._locked.is_set():
            self._move_action.set_sensitive(False)
            self._stop_action.set_sensitive(False)
            self._spinner.stop()
        elif self._loop.is_thinking():
            self._move_action.set_sensitive(False)
            self._stop_action.set_sensitive(True)
            self._spinner.start()
        else:
            self._move_action.set_sensitive(True)
            self._stop_action.set_sensitive(False)
            self._spinner.stop()
        
        if self._match.has_ended():
            self._move_action.set_sensitive(False)
        
        
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
        
        if self._filename is not None and self._match.can_undo() == False:
            title = ''
            message = ''
            
            event = self._match.get_tag('Event')
            south = self._match.get_tag('South')
            north = self._match.get_tag('North')
            result = self._match.get_tag('Result')
            description = self._match.get_tag('Description')
            
            if not _is_empty(event):
                title = '%s' % event
            
            if not _is_empty(description):
                message = description
            elif not _is_empty(south) and not _is_empty(north):
                message = '%s - %s' % (south, north)
            
            if not _is_empty(result) and result != '*':
                message = '%s (%s)' % (message, result)
            
            if title or message:
                if not title: title = _("Match")
                self.show_info_bar(title, message, 'document-open')
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
            
            self.show_info_bar(title, description)
        
        # If the match has comments, show them
        
        elif self._match.get_comment() != None:
            comment = GLib.markup_escape_text(self._match.get_comment())
            self.show_info_bar(None, comment, 'edit-find')
        
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
    
    
    # Message and confirmation dialogs
    
    def show_info_bar(self, title, message, icon = 'dialog-information'):
        """Shows an infobar information to the user"""
        
        label = self._builder.get_object('infobar-label')
        image = self._builder.get_object('infobar-image')
        
        if not title:
            markup = '%s' % message
        elif not message:
            markup = '<b>%s</b>' % title
        else:
            markup = '<b>%s</b>: %s' % (title, message)
        
        label.set_markup(markup)
        image.set_from_icon_name(icon, Gtk.IconSize.MENU)
        
        self._infobar.set_message_type(Gtk.MessageType.INFO)
        self._infobar.set_visible(True)
    
    
    def show_error_bar(self, title, message, icon = 'dialog-error'):
        """Shows an infobar error to the user"""
        
        label = self._builder.get_object('infobar-label')
        image = self._builder.get_object('infobar-image')
        
        label.set_markup('<b>%s</b>: %s' % (title, message))
        image.set_from_icon_name(icon, Gtk.IconSize.MENU)
        
        self._infobar.set_message_type(Gtk.MessageType.ERROR)
        self._infobar.set_visible(True)
    
    
    def show_info_dialog(self, title, message, text = None):
        """Shows an information message to the user"""
        
        dialog = self.new_message_dialog(
            Gtk.MessageType.INFO, title, message, text)
        
        dialog.connect('response', self.on_message_dialog_response)
        dialog.show()
    
    
    def show_error_dialog(self, title, message, text = None):
        """Shows an error message to the user"""
        
        dialog = self.new_message_dialog(
            Gtk.MessageType.ERROR, title, message, text)
        
        dialog.connect('response', self.on_message_dialog_response)
        dialog.show()
    
    
    def on_message_dialog_response(self, dialog, response):
        """Default handler for message dialogs"""
        
        dialog.destroy()
    
    
    def new_message_dialog(self, type, title, message, text = None):
        """Creates a new message dialog"""
        
        dialog = Gtk.MessageDialog(
            parent = self._main_window,
            flags = Gtk.DialogFlags.MODAL,
            buttons = Gtk.ButtonsType.OK
        )
        
        self._window_group.add_window(dialog)
        
        dialog.set_property('message-type', type)
        dialog.set_property('title', title)
        dialog.set_property('text', message)
        
        msgarea = dialog.get_message_area()
        
        for child in msgarea.get_children():
            if isinstance(child, Gtk.Label):
                child.set_property("max-width-chars", 48)
        
        if text is not None:
            dialog.set_property('secondary-text', text)
        
        return dialog
    
    
    def new_confirmation_dialog(self, title, message, text, discard):
        """Creates a new confirmation dialog"""
        
        dialog = Gtk.MessageDialog(
            parent = self._main_window,
            flags = Gtk.DialogFlags.MODAL,
            message_type = Gtk.MessageType.QUESTION,
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
            title = _("Open an oware match"),
            parent = self._main_window,
            action = Gtk.FileChooserAction.OPEN,
            buttons = (
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
            title = _("Save current match"),
            parent = self._main_window,
            action = Gtk.FileChooserAction.SAVE,
            buttons = (
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
    
    
    # Match manipulation methods
    
    def _get_exception_message(self, exception):
        """Extracts an error message from an exception"""
        
        message = None
        
        if hasattr(exception, 'message'):
            if exception.message is not None \
            and exception.message != '':
                message = exception.message
        
        if hasattr(exception, 'strerror'):
            if exception.strerror is not None \
            and exception.strerror != '':
                message = exception.strerror
        
        if message is None:
            message = str(exception)
        
        return message
    
    
    def open_match(self, path):
        """Open a match file and sets it as current"""
        
        try:
            self._match.load(path)
            self.on_file_changed(path)
            item = self._builder.get_object('neither_side_radiomenuitem')
            item.set_active(True)
            self._match.undo_all_moves()
        except Exception as e:
            message = self._get_exception_message(e)
            
            self.show_error_dialog(
                _("Error opening match"),
                _("Match file cannot be opened"),
                '%s «%s»: %s' % (
                    _("Unable to open file"),
                    path, _(message)
                )
            )
        
        self._locked.clear()
    
    
    def save_match(self, path):
        """Saves the current match to a file"""
        
        try:
            self._match.save(path)
            self.on_file_changed(path)
            self.refresh_infobar()
        except Exception as e:
            message = self._get_exception_message(e)
            
            self.show_error_dialog(
                _("Error saving match"),
                _("Cannot save current match"),
                _(message)
            )
    
    
    def start_match(self):
        """Starts a new match"""
        
        # Start a new match
        
        self._match.new_match()
        
        # Fill the match with default tags
        
        user = GLib.get_real_name()
        date = time.strftime('%Y.%m.%d')
        event = _("Untitled")
        
        self._match.set_tag('Event', event)
        self._match.set_tag('Date', date)
        self._match.set_tag('South', user)
        self._match.set_tag('North', user)
        
        if self._south is not None:
            name = self._south.get_name()
            self._match.set_tag('South', name)
        
        if self._north is not None:
            name = self._north.get_name()
            self._match.set_tag('North', name)
        
        # Rotate the board if needed
        
        if self._north is None and self._south is not None:
            if self._canvas.get_rotation() != math.pi:
                self._rotate_action.activate()
        elif self._south is None and self._north is not None:
            if self._canvas.get_rotation() != 0.0:
                self._rotate_action.activate()
        else:
            if self._canvas.get_rotation() != 0.0:
                self._rotate_action.activate()
        
        # Notify this view of a file change
        
        self.on_file_changed(None)
    
    
    def reset_engine(self):
        """Aborts any engine computations and setups a new game"""
        
        self._engine.abort_computation()
        self._engine.new_match()
        self._engine.set_strength(self._strength)
        self._engine.set_position(self._match)

