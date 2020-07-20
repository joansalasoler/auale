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
from gi.repository import GObject


class Actor(Clutter.Actor):
    """Base for all the actors"""

    __gtype_name__ = 'Actor'
    __object_properties = ('house',)

    def __init__(self):
        super(Actor, self).__init__()

        self._house = None
        self.set_pivot_point(0.5, 0.5)

    def get_house(self):
        """Get the related house actor"""

        return self._house

    def set_house(self, house):
        """Set the related house actor"""

        self._house = house

    def set_x_center(self, x: float):
        """Set the x-axis coordinate relative to the actor's center"""

        self.set_x(x - (self.get_width() / 2.0))

    def set_y_center(self, y: float):
        """Set the y-axis coordinate relative to the actor's center"""

        self.set_y(y - (self.get_height() / 2.0))

    house = GObject.Property(get_house, set_house, type=Clutter.Actor)
    x_center = GObject.Property(setter=set_x_center, type=float)
    y_center = GObject.Property(setter=set_y_center, type=float)
