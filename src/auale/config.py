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

from gui.factories import AccelsFactory
from gui.factories import ActionFactory
from gui.factories import OptionFactory

# =============================================================================
# Main actions of the application
# =============================================================================

ACTION_DESCRIPTORS = (
    ('app', (
        ('simple',          ('debug', 'b')),
        ('simple',          ('new',)),
        ('simple',          ('open', 's',)),
        ('simple',          ('quit',)),
        ('state',           ('engine', '"[default]"', 's')),
    )),
    ('win', (
        ('simple',          ('about',)),
        ('simple',          ('close',)),
        ('simple',          ('move',)),
        ('simple',          ('new',)),
        ('simple',          ('open', 's',)),
        ('simple',          ('redo-all',)),
        ('simple',          ('redo',)),
        ('simple',          ('rules',)),
        ('simple',          ('save-as',)),
        ('simple',          ('save', 's',)),
        ('simple',          ('scoresheet',)),
        ('simple',          ('stop',)),
        ('simple',          ('undo-all',)),
        ('simple',          ('undo',)),
        ('setting',         ('engine',)),
        ('setting',         ('mute',)),
        ('setting',         ('strength',)),
        ('state',           ('immersive', 'false',)),
        ('state',           ('rotate', 'false',)),
        ('state',           ('side', '"south"', 's')),
    ))
)

# =============================================================================
# Main command line options of the application
# =============================================================================

OPTION_DESCRIPTORS = (
    ('debug',               ('Enable the debug mode',)),
    ('version',             ('Show program\'s version number and exit',)),
    ('engine',              ('Set the engine to use', 'command', '&s')),
)

# =============================================================================
# Keyboard shortcuts configuration
# =============================================================================

ACCELS_DESCRIPTORS = (
    ('win.save-as',         ('<Primary><Shift>S',)),
    ('win.new',             ('<Primary>N',)),
    ('win.open',            ('<Primary>O',)),
    ('win.rotate',          ('<Primary>R',)),
    ('win.save',            ('<Primary>S',)),
    ('win.redo-all',        ('End',)),
    ('win.rules',           ('F1',)),
    ('win.immersive',       ('F11',)),
    ('win.undo-all',        ('Home',)),
    ('win.redo',            ('Page_Down',)),
    ('win.undo',            ('Page_Up',)),
)

# =============================================================================
# Configuration factory instances
# =============================================================================

options = OptionFactory(OPTION_DESCRIPTORS)
actions = ActionFactory(ACTION_DESCRIPTORS)
accelerators = AccelsFactory(ACCELS_DESCRIPTORS)
