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
    'seeds',   # Minimum number of seeds
    'capture'  # Requires a capture
))


class RipeningStage(Enum):
    """A house ripening stage"""

    GREEN = Params(0, False)
    BREAKER = Params(0, True)
    TURNING = Params(12, False)
    RIPE = Params(12, True)

    @property
    def needs_capture(self):
        return self.value.capture

    @property
    def minimum_seeds(self):
        return self.value.seeds

    @property
    def nick(self):
        return self.name.lower()

    @property
    def ordinal(self) -> int:
        return list(self).index(self)

    @staticmethod
    def value_of(nick: str) -> Enum:
        return RipeningStage[nick.upper()]
