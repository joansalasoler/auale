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

from .actor import Actor


class Active(Actor):
    """Active indicator of a house"""

    __gtype_name__ = 'Active'

    def __init__(self):
        super(Active, self).__init__()
        self.connect('notify::house', self.on_house_changed)

    def on_house_changed(self, actor, param):
        """Emitted when the related house changes"""

        house = self.get_house()
        house.bind_property('activated', self, 'visible')
