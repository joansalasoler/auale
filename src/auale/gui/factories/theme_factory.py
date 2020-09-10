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
from ..mixer import SoundContext


class ThemeFactory(object):
    """Creates the canvas and sound contexts"""

    def __init__(self, descriptors):
        self._descriptors = descriptors

    def create_canvas_script(self):
        """Creates a new Clutter script for the board canvas"""

        script = Clutter.Script()

        for kind, path in self._descriptors:
            if kind == 'canvas':
                script.load_from_resource(path)

        return script

    def create_sound_context(self):
        """Creates a new sound context for the application"""

        context = SoundContext()

        for kind, path in self._descriptors:
            if kind == 'sounds':
                context.load_from_resource(path)

        return context
