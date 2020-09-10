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

from collections import namedtuple
from enum import Enum

Params = namedtuple('Params', (
    'factor',   # Strength factor
    'depth',    # Maximum search depth
    'timeout',  # Maximum search time
    'ponder',   # If pondering is allowed
    'book',     # If the opening book is enabled
))


class Strength(Enum):
    """Engine playing strength levels"""

    EASY = Params(0.0, 2, 600, False, False)
    MEDIUM = Params(0.3, 6, 1200, False, True)
    HARD = Params(0.5, 16, 2400, True, True)
    EXPERT = Params(1.0, None, 3600, True, True)

    @property
    def search_depth(self):
        return self.value.depth

    @property
    def search_timeout(self):
        return self.value.timeout

    @property
    def allows_pondering(self):
        return self.value.ponder

    @property
    def allows_book_search(self):
        return self.value.book

    @property
    def strength_factor(self):
        return self.value.factor

    @property
    def ordinal(self) -> int:
        return list(self).index(self)

    @property
    def nick(self):
        return self.name.lower()

    @staticmethod
    def value_of(nick: str) -> Enum:
        return Strength[nick.upper()]
