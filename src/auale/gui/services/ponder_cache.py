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

from collections import OrderedDict


class PonderCache(OrderedDict):
    """A cache to store ponder moves"""

    def __init__(self, size):
        self._size = size

    def fetch(self, match):
        """Obtains a value for the given match"""

        move = match.get_move()
        index = match.get_current_index()
        positions = match.get_positions()
        hashcode = hash((move, positions[:index]))

        return self.get(hashcode, None)

    def store(self, match, move, value):
        """Stores a value for the given match and move"""

        if len(self) >= self._size:
            self.popitem()

        positions = match.get_positions()
        hashcode = hash((move, positions))
        self[hashcode] = value

    @property
    def size(self):
        """Requested size of this dictionary"""

        return self._size
