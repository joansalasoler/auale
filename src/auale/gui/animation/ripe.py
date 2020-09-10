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


class Ripe(Clutter.PropertyTransition):
    """Add a number of seeds to a house"""

    __gtype_name__ = 'Ripe'

    def __init__(self, house):
        super(Ripe, self).__init__()

        self._house = house
        self._name = str(id(self))
        self.set_duration(150)
        self.connect('started', self.on_transition_started)

    def get_house(self):
        """House actor for this transition"""

        return self._house

    def set_state(self, state):
        """Sets the rippening state of the animated actor"""

        self._state = state

    def attach(self):
        """Start this transition on an actor"""

        self._house.add_transition(self._name, self)

    def detach(self):
        """Remove this transition from its attached actor"""

        self._house.remove_transition(self._name)

    def on_transition_started(self, transition):
        """Fired when the transition starts animating"""

        self._house.set_property('state', self._state)
