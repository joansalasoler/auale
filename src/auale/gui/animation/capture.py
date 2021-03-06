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

from gi.repository import Clutter


class Capture(Clutter.PropertyTransition):
    """Capture the seeds on a house"""

    __gtype_name__ = 'Capture'

    def __init__(self, house):
        super(Capture, self).__init__()

        self._house = house
        self._name = str(id(self))

        self.set_property_name('opacity')
        self.set_progress_mode(Clutter.AnimationMode.EASE_IN_QUAD)
        self.set_duration(100)
        self.set_from(255)
        self.set_to(0)

    def get_house(self):
        """House actor for this transition"""

        return self._house

    def attach(self):
        """Start this transition on an actor"""

        self._house.add_transition(self._name, self)

    def detach(self):
        """Remove this transition from its attached actor"""

        self._house.remove_transition(self._name)
        self._house.set_content(None)
        self._house.set_opacity(255)
