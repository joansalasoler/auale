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
from gi.repository import GObject


class Mosaic(Clutter.Canvas):
    """A canvas that draws a reflected image"""

    __gtype_name__ = 'Mosaic'

    def __init__(self):
        super(Mosaic, self).__init__()

        self._path = None
        self._image = None
        self.connect('draw', self.on_draw_request)

    def get_path(self):
        """Get the path for this mosaic image"""

        return self._path

    def set_path(self, path):
        """Set the path for this mosaic image"""

        self.__path = path
        self._image = GdkPixbuf.Pixbuf.new_from_resource(path)
        self.allocate_image()

    def on_draw_request(self, canvas, context, width, height):
        """Draws the tile on the canvas"""

        if isinstance(self._image, GdkPixbuf.Pixbuf):
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

    path = GObject.Property(get_path, set_path, str)
