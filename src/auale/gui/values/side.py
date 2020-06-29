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

from enum import Enum
from collections import namedtuple
from .rotation import Rotation

Params = namedtuple('Params', (
    'angle',  # Board rotation
    'south',  # If south is an engine
    'north',  # If north is an engine
))


class Side(Enum):
    """Engine's playing side"""

    BOTH = Params(Rotation.BASE, True, True)
    NEITHER = Params(Rotation.BASE, False, False)
    NORTH = Params(Rotation.BASE, False, True)
    SOUTH = Params(Rotation.ROTATED, True, False)

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
    def ordinal(self) -> int:
        return list(self).index(self)

    @property
    def nick(self):
        return self.name.lower()

    @staticmethod
    def value_of(nick: str) -> Enum:
        return Side[nick.upper()]
