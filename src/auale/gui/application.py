#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014 Joan Sala Soler <contact@joansala.com>
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

from gui import App, GTKView
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk


class GTKApplication(Gtk.Application):
    
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
        self.connect("window-added", self.on_window_added)
        self.connect("handle-local-options", self.on_handle_options)
    
    
    def on_startup(self, application):
        """Emitted on application startup"""
        
        self._settings = Gio.Settings(App.ID)
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
    
    
    def on_window_added(self, application, window):
        """Emitted on window addition"""
        
        # Restore the last closed window size
        
        width = self._settings.get_int('window-width')
        height = self._settings.get_int('window-height')
        
        if (width, height) >= window.get_size_request():
            window.set_default_size(width, height)
        
        # Restore the last maximization state
        
        if self._settings.get_boolean('window-maximize'):
            window.maximize()
    
    
    def on_window_change(self, window, event):
        """Emitted on a window delete or configure event"""
        
        # WA: Save the state only on resize events
        
        if window._size == (event.width, event.height): return
        window._size = (event.width, event.height)
        
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
    
    
    def show_view(self, view):
        """Adds a view to the application and shows it"""
        
        window = view.get_window()
        window.connect('configure-event', self.on_window_change)
        window._size = (-1, -1)
        
        self.add_window(window)
        
        window.show_all()
        view.refresh_view()

