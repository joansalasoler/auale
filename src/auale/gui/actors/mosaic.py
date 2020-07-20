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

from cairo import EXTEND_REFLECT
from gi.repository import Clutter
from gi.repository import Gdk
from gi.repository import GdkPixbuf


class Mosaic(Clutter.Canvas):
    """A canvas that draws a reflected image"""

    __gtype_name__ = 'Mosaic'
    __path = '/com/joansala/auale/canvas/mosaic.png'

    def __init__(self):
        super(Mosaic, self).__init__()

        self._image = GdkPixbuf.Pixbuf.new_from_resource(self.__path)
        self.connect('draw', self.on_draw_request)

    def on_draw_request(self, canvas, context, width, height):
        """Draws the tile on the canvas"""

        Gdk.cairo_set_source_pixbuf(context, self._image, 0, 0)
        context.get_source().set_extend(EXTEND_REFLECT)
        context.rectangle(0, 0, width, height)
        context.fill()

    def allocate_image(self):
        """Resize the canvas to fit the mosaic"""

        width = 2 * self._image.get_width()
        height = 2 * self._image.get_height()

        if not self.set_size(width, height):
            self.invalidate()
