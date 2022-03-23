#!/usr/bin/python3
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
import site

from distutils.core import setup
from distutils import dir_util

# Distutils configuration

PACKAGE_CONFIG = dict(
    name='auale',
    version='2.2.0+develop',
    url='https://auale.joansala.com/',
    author='Joan Sala Soler',
    author_email='contact@joansala.com',
    license='GPL3+',
    description='Aualé — The Game of Mancala',
    long_description="""Oware is a strategy board game of the Mancala family.""",
    packages=[
        'auale',
        'auale.uci',
        'auale.book',
        'auale.game',
        'auale.sdl2',
        'auale.gui',
        'auale.i18n',
        'auale.gamepad',
        'auale.serialize',
        'auale.sdl2.test',
        'auale.sdl2.ext',
        'auale.gui.widgets',
        'auale.gui.dialogs',
        'auale.gui.services',
        'auale.gui.filters',
        'auale.gui.animation',
        'auale.gui.mixer',
        'auale.gui.actors',
        'auale.gui.values',
        'auale.gui.factories',
        'auale.gui.windows'
    ],

    package_data={
        'auale': [
            'data/engine/*',
            'data/locale/*/*/*',
            'data/auale.gresource',
            'game/oware.pkl',
        ],
    },
)

# Py2exe configuration

if 'win' in sys.platform:
    import py2exe

    PACKAGE_CONFIG.update({
        'windows': [{
            'script': '__main__.py',
            'icon_resources': [(1, './resources/images/auale.ico')]
        }],

        'options': {
            'py2exe': {
                'packages': ['gi'],
                'includes': ['gi'],
            }
        },
    })

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
    dir_util.copy_tree('../../bin/win32/', './dist/')
    os.rename('./dist/__main__.exe', './dist/auale.exe')
