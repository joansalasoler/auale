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

import os
import sys
import site

try:
    import py2exe
except:
    pass

from distutils.core import setup
from distutils import dir_util

# Distutils configuration

PACKAGE_CONFIG = dict(
    name             = 'auale',
    version          = '1.1.0',
    url              = 'http://www.joansala.com/auale/',
    author           = 'Joan Sala Soler',
    author_email     = 'contact@joansala.com',
    license          = 'GPL3+',
    description      = 'Graphic user interface for oware',
    long_description = """Aualé is a graphic user interface for the oware abapa
        board game. Allows the users to analyse and record their own matches
        or play against a strong computer player.""",
    
    packages = [
        '.',
        'game',
        'gui',
        'uci',
        'sdl2',
    ],
    
    package_data = {
        '.' : [
            'res/engine/*',
            'res/glade/*',
            'res/image/*',
            'res/other/*',
            'res/sound/*',
            'res/messages/*/*/*'
        ],
    },
    
    windows = [{
        'script' : '__main__.py',
        'icon_resources' : [(1, './res/image/auale.ico')]
    }],
    
    options = {
        'py2exe' : {
            'packages' : ['gi', 'cairo'],
            'includes' : ['gi', 'cairo'],
        }
    },
)

# Add the 'gnome' package to the path

if 'win' in sys.platform:
    gnome_path = os.path.join(site.getsitepackages()[1], "gnome")
    sys.path.append(gnome_path)

# Do the distutils setup thing

setup(**PACKAGE_CONFIG)

# Copy resource and GTK files to the distribution folder when building
# binaries for Windows. This assumes the required binary libraries and
# configuration files for GTK and SDL are stored on /bin/win32/

if 'py2exe' in sys.argv and 'win' in sys.platform:
    dir_util.copy_tree('./res', './dist/res')
    dir_util.copy_tree('../../bin/win32/', './dist/')
    os.rename('./dist/__main__.exe', './dist/auale.exe')

