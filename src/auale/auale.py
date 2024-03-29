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
import sys
import signal
import logging
import gui

from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from config import accelerators
from config import actions
from config import controls
from config import options

from gui.mixer import SoundMixer
from gui.windows import AualeWindow


class Auale(Gtk.Application):
    """Main application"""

    __gtype_name__ = 'Auale'

    __VERSION = '2.2.0'
    __DISPLAY_NAME = 'Aualé'
    __ID = 'com.joansala.auale'
    __FLAGS = Gio.ApplicationFlags.HANDLES_OPEN
    __MULTINSTANCE = False

    def __init__(self):
        super(Auale, self).__init__(application_id=self.__ID, flags=self.__FLAGS)

        self._settings = None
        self._immersive = False

        GLib.set_application_name(self.__DISPLAY_NAME)
        GLib.setenv('PULSE_PROP_application.name', self.__DISPLAY_NAME, True)
        GLib.setenv('PULSE_PROP_application.icon_name', 'auale', True)
        GLib.setenv('PULSE_PROP_media.role', 'game', True)

        signal.signal(signal.SIGINT, self.on_application_termination)
        signal.signal(signal.SIGTERM, self.on_application_termination)

        self.connect("activate", self.on_application_activate)
        self.connect("handle-local-options", self.on_handle_local_options)
        self.connect("open", self.on_application_open)
        self.connect("shutdown", self.on_application_shutdown)
        self.connect("startup", self.on_application_startup)

        self.connect_application_commands()
        self.register()

    def get_local_settings(self):
        """Gets this application's local settings instance"""

        if not isinstance(self._settings, Gio.Settings):
            self._settings = Gio.Settings(self.__ID)

        return self._settings

    def get_engine_command(self):
        """Get the string value of the current engine state"""

        action = self.lookup_action('engine')
        state = action.get_state()

        return state.get_string()

    def get_immersive_mode(self):
        """Get if the immersive mode was requested"""

        return self._immersive

    def reset_engine_command(self):
        """Resets the current engine command state"""

        settings = self.get_local_settings()
        state = settings.get_user_value('engine')
        action = self.lookup_action('engine')
        action.set_state(state)

    def reset_immersive_mode(self):
        """Resets the fullscreen mode state"""

        self._immersive = False

    def setup_application_theme(self):
        """Registers this application's CSS provider"""

        Gio.ThemedIcon.new('auale')

        provider = Gtk.CssProvider()
        screen = Gdk.Screen.get_default()
        base_path = self.get_resource_base_path()
        priority = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION

        Gtk.StyleContext.add_provider_for_screen(screen, provider, priority)
        provider.load_from_resource(f'{ base_path }/gtk/application.css')

    def show_application_window(self, uri=None):
        """Adds or presents an application window"""

        has_active_window = self.get_active_window()
        allow_new_windows = self.__MULTINSTANCE

        if allow_new_windows or not has_active_window:
            window = self.add_application_window(uri)
            return window.show_all()

        self.present_application_window(uri)

    def add_application_window(self, uri=None):
        """Adds a new application window"""

        SoundMixer.init()
        window = AualeWindow(self)

        command = self.get_engine_command()
        immersive = self.get_immersive_mode()
        settings = Gio.Settings(self.__ID)
        settings.delay()

        window.set_application(self)
        window.set_local_settings(settings)

        self.connect_window_actions(window)
        self.connect_window_signals(window)

        window.set_engine_command(command)
        window.set_immersive_mode(immersive)

        if isinstance(uri, str) and uri:
            window.set_match_from_uri(uri)

        return window

    def present_application_window(self, uri=None):
        """Update and present the current application window"""

        window = self.get_active_window()
        command = self.get_engine_command()
        immersive = self.get_immersive_mode()

        if isinstance(uri, str) and uri:
            window.set_match_from_uri(uri)

        window.set_engine_command(command)
        window.set_immersive_mode(immersive)
        window.present()

        return window

    def connect_application_commands(self):
        """Registers the command line options"""

        options.connect(self)

    def connect_application_actions(self):
        """Setups the actions for the application"""

        actions.connect(self, 'app')
        accelerators.connect(self)
        controls.connect(self)

    def connect_window_actions(self, window):
        """Setups the actions for a window"""

        actions.connect(window, 'win')

    def connect_window_signals(self, window):
        """Connects the required window signals"""

        window.connect('delete-event', self.on_window_delete_event)
        window.connect('realize', self.on_window_realize)

    def save_window_geometry(self, window):
        """Updates the settings with a window geometry"""

        settings = self.get_local_settings()
        maximize = window.is_maximized()
        width, height = window.get_size()

        if not maximize:
            settings.set_int('width', width)
            settings.set_int('height', height)

        settings.set_boolean('maximize', maximize)

    def restore_window_geometry(self, window):
        """Sets a window geometry according to stored settings"""

        settings = self.get_local_settings()

        width = settings.get_int('width')
        height = settings.get_int('height')
        maximize = settings.get_boolean('maximize')

        window.set_default_size(width, height)
        window.maximize() if maximize else window.unmaximize()

    def save_window_settings(self, window):
        """Stores the local settings of a window"""

        settings = window.get_local_settings()
        settings.apply()
        settings.sync()

    def print_version_number(self):
        """Show program's version number and exit"""

        version = self.__VERSION
        name = self.__DISPLAY_NAME
        sys.stdout.write(f'{ name } { version }\n')

    def on_application_startup(self, app):
        """Handles the application initialization"""

        self.setup_application_theme()
        self.connect_application_actions()

    def on_application_shutdown(self, application):
        """Handles the application shutdown"""

        SoundMixer.quit()
        settings = self.get_local_settings()
        settings.sync()

    def on_application_activate(self, application):
        """Activates the application"""

        self.activate_action('new')
        self.reset_engine_command()
        self.reset_immersive_mode()

    def on_application_open(self, application, files, length, hint):
        """Opens the given files"""

        for file in files:
            uri = GLib.Variant.new_string(file.get_uri())
            self.activate_action('open', uri)

        self.reset_engine_command()
        self.reset_immersive_mode()

    def on_application_termination(self, sinal, frame):
        """Handles system interruption signals"""

        for window in self.get_windows():
            window.destroy()

        self.activate_action('quit')
        sys.exit(os.EX_OK)

    def on_window_realize(self, window):
        """Handles the realize event of a window"""

        self.restore_window_geometry(window)

    def on_window_delete_event(self, window, event):
        """Handles the deletion event of a window"""

        self.save_window_geometry(window)
        self.save_window_settings(window)

    def on_handle_local_options(self, application, options):
        """Handles command line options"""

        if options.contains('version'):
            self.print_version_number()
            return os.EX_OK

        for name in self.list_actions():
            if options.contains(name):
                value = options.lookup_value(name)
                self.activate_action(name, value)

        return -1

    def on_debug_action_activate(self, action, value):
        """Enables the debug mode"""

        logging.basicConfig(stream=sys.stdout)
        logging.getLogger().setLevel(logging.DEBUG)

    def on_quit_action_activate(self, action, value):
        """Exits the application"""

        self.quit()

    def on_new_action_activate(self, action, value):
        """Opens a new application window"""

        self.show_application_window()

    def on_open_action_activate(self, action, value):
        """Opens a file in a new application window"""

        uri = value.get_string()
        self.show_application_window(uri)

    def on_fullscreen_action_activate(self, action, value):
        """Sets the immersive mode for new windows"""

        self._immersive = True

    def on_engine_action_change_state(self, action, value):
        """Sets the engine command for the current session"""

        action.set_state(value)
