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

import os, sys
import util

from gui import App, GTKView
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk


class GTKApplication(Gtk.Application):
    """
    This GTK application parses command line arguments and creates new
    views on request.
    """
    
    def __init__(self):
        """Starts the application"""
        
        super(GTKApplication, self).__init__(
            application_id = App.ID,
            flags = Gio.ApplicationFlags.HANDLES_OPEN
        )
        
        # Add a 'version' option to the command line
        
        option = GLib.OptionEntry()
        option.long_name = 'version'
        option.short_name = ord('v')
        option.description = _("Show program's version number and exit")
        
        self.add_main_option_entries((option,))
        
        # Connect all the application signals
        
        self.connect("startup", self.on_startup)
        self.connect("shutdown", self.on_shutdown)
        self.connect("activate", self.on_activate)
        self.connect("open", self.on_open)
        self.connect("handle-local-options", self.on_handle_options)
    
    
    def on_startup(self, application):
        """Emitted on application startup"""
        
        self._settings = util.get_gio_settings(App.ID)
        self._settings.delay()
        
        
    def on_shutdown(self, application):
        """Emitted on application shutdown"""
        
        self._settings.apply()
        self._settings.sync()
        
        
    def on_activate(self, application):
        """Emitted to activate the application"""
        
        view = GTKView()
        application.show_view(view)
        view.show_tips()
    
    
    def on_open(self, application, files, n, hint):
        """Emitted to open one ore more files"""
        
        for path in (f.get_path() for f in files):
            view = GTKView()
            view.open_match(path)
            application.show_view(view)
    
    
    def on_handle_options(self, application, options):
        """Emitted to parse local command line options"""
        
        if options.contains('version'):
            print('%s %s' % (App.NAME, App.VERSION))
            sys.exit(0);
        
        return -1
    
    
    def on_window_delete(self, window, event):
        """Emitted on a window delete or configure event"""
        
        # Save the window size and maximization state
        
        maximized = Gdk.WindowState.MAXIMIZED
        state = window.get_window().get_state()
        
        if (maximized == state & maximized):
            self._settings.set_boolean('window-maximize', True)
        else:
            (width, height) = window.get_size()
            self._settings.set_int('window-width', width)
            self._settings.set_int('window-height', height)
            self._settings.set_boolean('window-maximize', False)
    
    
    def set_window_size(self, window):
        """Sets a window width and height"""
        
        # Copy the current or last maximization state
        
        active = self.get_active_window()
        maximize = self._settings.get_boolean('window-maximize')
        
        if active is not None:
            maximized = Gdk.WindowState.MAXIMIZED
            state = active.get_window().get_state()
            maximize = (maximized == state & maximized)
        
        # Copy the active or last closed window size
        
        if maximize or not active:
            width = self._settings.get_int('window-width')
            height = self._settings.get_int('window-height')
        else:
            (width, height) = active.get_size()
        
        # Set the window size and maximization state
        
        if (width, height) >= window.get_size_request():
            window.set_default_size(width, height)
        
        if maximize:
            window.maximize()
    
    
    def show_view(self, view):
        """Adds a view to the application and shows it"""
        
        window = view.get_window()
        window.connect('delete-event', self.on_window_delete)
        
        self.set_window_size(window)
        self.add_window(window)
        
        window.show_all()
        view.refresh_view()

