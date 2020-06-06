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
from collections import namedtuple
from enum import Enum

Params = namedtuple('Params', (
    'nick',   # Unique identifier
    'angle',  # Human's view angle in radians
    'south',  # If south is an engine
    'north',  # If north is an engine
))


class Side(Enum):
    """Engine's playing side"""

    BOTH = Params('both', 0.0, True, True)
    NEITHER = Params('neither', 0.0, False, False)
    NORTH = Params('north', 0.0, False, True)
    SOUTH = Params('south', math.pi, True, False)

    @property
    def is_south(self):
        return self.value.south

    @property
    def is_north(self):
        return self.value.north

    @property
    def view_angle(self):
        return self.value.angle

    @property
    def nick(self):
        return self.value.nick

    @property
    def ordinal(self) -> int:
        return list(self).index(self)

    @staticmethod
    def is_nick(nick: str, value: Enum) -> bool:
        return value.nick == nick.lower()

    @staticmethod
    def value_of(nick: str) -> Enum:
        return next(e for e in Side if Side.is_nick(nick, e))
