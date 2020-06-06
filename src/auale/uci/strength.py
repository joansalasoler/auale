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
    'nick',     # Unique identifier
    'factor',   # Strength factor
    'depth',    # Maximum search depth
    'timeout',  # Maximum search time
    'ponder',   # If pondering is allowed
))


class Strength(Enum):
    """Engine playing strength levels"""

    EASY = Params('easy', 0.0, 4, 600, False)
    MEDIUM = Params('medium', 0.3, 8, 1200, False)
    HARD = Params('hard', 0.5, 16, 2400, True)
    EXPERT = Params('expert', 1.0, None, 3600, True)

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
    def strength_factor(self):
        return self.value.factor

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
        return next(e for e in Strength if Strength.is_nick(nick, e))
