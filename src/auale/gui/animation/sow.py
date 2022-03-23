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


class Sow(Clutter.TransitionGroup):
    """Add a number of seeds to a house"""

    __gtype_name__ = 'Sow'

    def __init__(self, house):
        super(Sow, self).__init__()

        self._house = house
        self._content = None
        self._state = None
        self._name = str(id(self))

        scalex = Clutter.PropertyTransition()
        scalex.set_progress_mode(Clutter.AnimationMode.EASE_OUT_ELASTIC)
        scalex.set_property_name('scale-x')
        scalex.set_from(0.4)
        scalex.set_to(1.0)

        scaley = Clutter.PropertyTransition()
        scaley.set_progress_mode(Clutter.AnimationMode.EASE_OUT_ELASTIC)
        scaley.set_property_name('scale-y')
        scaley.set_from(0.4)
        scaley.set_to(1.0)

        self.connect('started', self.on_transition_started)
        self.add_transition(scalex)
        self.add_transition(scaley)
        self.set_duration(1000)

        self._scalex = scalex

    def get_house(self):
        """House actor for this transition"""

        return self._house

    def set_content(self, content):
        """Sets the content of the animated actor"""

        self._content = content

    def set_state(self, state):
        """Sets the rippening state of the animated actor"""

        self._state = state

    def attach(self):
        """Start this transition on an actor"""

        self._house.add_transition(self._name, self)

    def detach(self):
        """Remove this transition from its attached actor"""

        self._house.remove_transition(self._name)
        self._house.set_scale(1.0, 1.0)

    def on_transition_started(self, transition):
        """Fired when the transition starts animating"""

        self._house.set_content(self._content)
        self._house.set_property('state', self._state)
