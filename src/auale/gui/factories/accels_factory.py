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


class AccelsFactory(object):
    """Connect accelerators to an application"""

    def __init__(self, descriptors):
        """Creates a new factory for a configuration"""

        self._descriptors = descriptors

    def connect(self, target):
        """Connects the set of configured options to a target"""

        for descriptor in self._descriptors:
            target.set_accels_for_action(*descriptor)
