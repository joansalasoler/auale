#!/usr/bin/env python
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

import gi
import os
import sys
import i18n

# =============================================================================
# Configuration of the interface.
# -----------------------------------------------------------------------------
# This module sets the environment for the application and ensures that the
# required libraries are loaded for the current platform.
# =============================================================================

__FILE_PATH = os.path.dirname(__file__)
__BASE_PATH = os.path.abspath(os.path.join(__FILE_PATH, os.pardir))
__RESOURCE_PATH = os.path.join(__BASE_PATH, 'data/auale.gresource')
__LOCALE_PATH = os.path.join(__BASE_PATH, 'data/locale/')
__TEXT_DOMAIN = 'auale'

# Sets the required GTK library versions globally.

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Rsvg', '2.0')
gi.require_version('Clutter', '1.0')
gi.require_version('GtkClutter', '1.0')
gi.require_version('Manette', '0.2')

# Reister the application resources on the global namespace so they
# can be used wiht the @Gtk.Template decorator. Notice though that
# this module needs to be imported before using them.

from gi.repository import Gio

resource = Gio.Resource.load(__RESOURCE_PATH)
Gio.resources_register(resource)

# On the Windows platform we provide the SDL library as a DLL on the
# data folder. Set the environment to ensure that it can be found.

if 'win' in sys.platform:
    sdl_path = os.path.join(__BASE_PATH, 'data/lib/sdl')
    os.environ['PYSDL2_DLL_PATH'] = sdl_path

# Initialize Gtk and Clutter before the text domain is set

from gi.repository import Gtk
from gi.repository import GtkClutter
from gi.repository import Manette

GtkClutter.init(sys.argv)

# Ensure the required environment variables are set, so the locale
# library can find the correct translations and set the text domain.
# Notice that Gtk must be imported before the textdomain is set.

if os.path.isdir(__LOCALE_PATH):
    os.environ['LOCPATH'] = __LOCALE_PATH

if 'LANG' not in os.environ or not os.environ['LANG']:
    lang, enc = i18n.module.getdefaultlocale()
    os.environ['LANG'] = lang

if 'LOCPATH' not in os.environ or not os.environ['LOCPATH']:
    __LOCALE_PATH = f'{ sys.base_prefix }/share/locale'
    os.environ['LOCPATH'] = __LOCALE_PATH

i18n.module.bind_textdomain_codeset(__TEXT_DOMAIN, 'utf-8')
i18n.module.bindtextdomain(__TEXT_DOMAIN, __LOCALE_PATH)
i18n.module.textdomain(__TEXT_DOMAIN)
