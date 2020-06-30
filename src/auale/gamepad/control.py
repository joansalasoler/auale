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
from .control_type import ControlType

Params = namedtuple('Params', (
    'code',      # Event code
    'type',      # Event type
    'direction'  # Direction value
))


class Control(Enum):
    """Gamepad controls"""

    ABS_DOWN = Params(0x01, ControlType.ABSOLUTE_AXIS, 1.0)
    ABS_LEFT = Params(0x00, ControlType.ABSOLUTE_AXIS, -1.0)
    ABS_RIGHT = Params(0x00, ControlType.ABSOLUTE_AXIS, 1.0)
    ABS_UP = Params(0x01, ControlType.ABSOLUTE_AXIS, -1.0)
    DPAD_DOWN = Params(0x221, ControlType.BUTTON, None)
    DPAD_LEFT = Params(0x222, ControlType.BUTTON, None)
    DPAD_RIGHT = Params(0x223, ControlType.BUTTON, None)
    DPAD_UP = Params(0x220, ControlType.BUTTON, None)
    EAST = Params(0x131, ControlType.BUTTON, None)
    HAT_DOWN = Params(0x11, ControlType.HAT_AXIS, 1.0)
    HAT_LEFT = Params(0x10, ControlType.HAT_AXIS, -1.0)
    HAT_RIGHT = Params(0x10, ControlType.HAT_AXIS, 1.0)
    HAT_UP = Params(0x11, ControlType.HAT_AXIS, -1.0)
    SOUTH = Params(0x130, ControlType.BUTTON, None)
    TRIGGER_LEFT = Params(0x136, ControlType.BUTTON, None)
    TRIGGER_RIGHT = Params(0x137, ControlType.BUTTON, None)

    @property
    def code(self):
        return self.value.code

    @property
    def type(self):
        return self.value.type

    @property
    def direction(self):
        return self.value.direction

    @property
    def nick(self):
        return self.name.lower()

    @property
    def ordinal(self) -> int:
        return list(self).index(self)

    @staticmethod
    def value_of(nick: str) -> Enum:
        return Control[nick.upper()]

    @staticmethod
    def for_code(code: int) -> list:
        return [e for e in Control if code == e.code]
