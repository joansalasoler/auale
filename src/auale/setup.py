#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Aualé oware graphic user interface.
Copyright (C) 2014 Joan Sala Soler <contact@joansala.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import site

try:
    import py2exe
except:
    pass

from distutils.core import setup
from distutils import dir_util

# Add gnome to the path

sys.path.append(
    os.path.join(site.getsitepackages()[1], "gnome"))

# Setup configuration

setup(
    name             = 'auale',
    version          = '1.0.0',
    author           = 'Joan Sala Soler',
    author_email     = 'contact@joansala.com',
    url              = 'http://www.joansala.com/auale/',
    license          = 'GPL2',
    description      = 'Graphic user interface for oware',
    long_description = """Aualé is a graphic user interface for the oware abapa
        board game. Allows the users to analyse and record their own matches
        or play against a strong computer player.""",
    
    packages = [
        '.',
        'game',
        'gui',
        'uci',
        'res',
        'sdl2',
    ],
    
    package_data = {
        'res' : [
            'engine/*',
            'glade/*',
            'image/*',
            'other/*',
            'sound/*',
            'messages/*/*/*'
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

# Copy resource and gtk files

if 'py2exe' in sys.argv and 'win' in sys.platform:
    dir_util.copy_tree('./res', './dist/res')
    dir_util.copy_tree('../../bin/win32/', './dist/')
    os.rename('./dist/__main__.exe', './dist/auale.exe')

