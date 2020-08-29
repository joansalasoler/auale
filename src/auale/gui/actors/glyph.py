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

import cairo

from gi.repository import Clutter
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Rsvg


class Glyph(Clutter.Canvas):
    """A canvas that draws a glyph from an .svg file"""

    __gtype_name__ = 'Glyph'
    __cache = dict()

    def __init__(self):
        super(Glyph, self).__init__()

        self._path = None
        self._handle = None
        self._surface = None
        self._fragment = None

        self.connect('draw', self.on_draw_request)

    def get_path(self):
        """Get the path for this mosaic image"""

        return self._path

    def get_fragment(self):
        """Gets the fragment to render from the .svg"""

        return self._fragment

    def set_path(self, path):
        """Set the path for this mosaic image"""

        self._path = path
        self._handle = None
        self._surface = None
        self.invalidate()

    def set_fragment(self, fragment):
        """Sets the fragment to render from the .svg"""

        self._fragment = fragment
        self.invalidate()

    def get_svg_handle(self):
        """Obtain the Rsvg handle to use for drawing"""

        return self._handle or self._create_svg_handle()

    def get_image_surface(self):
        """Obtain the current Cairo image surface"""

        return self._surface or self._create_image_surface()

    def on_draw_request(self, canvas, context, width, height):
        """Draws the loaded glyph on the canvas"""

        if self._path and self._fragment:
            surface = self.get_image_surface()
            context.set_source_surface(surface)
            context.paint()

    def _create_image_surface(self):
        """Creates a surface for the current .svg fragment"""

        handle = self.get_svg_handle()
        view_size = handle.get_dimensions()
        width = int(self.get_property('width'))
        height = int(self.get_property('height'))
        x = (width / 2.0) - (view_size.width / 2.0)
        y = (height / 2.0) - (view_size.height / 2.0)

        surface = cairo.ImageSurface(cairo.Format.ARGB32, width, height)
        context = cairo.Context(surface)
        context.translate(x, y)
        handle.render_cairo_sub(context, self._fragment)

        return surface

    def _create_svg_handle(self):
        """Creates a new .svg handle for the scene"""

        if self._path in self.__cache:
            return self.__cache[self._path]

        flags = Gio.ResourceLookupFlags.NONE
        data = Gio.resources_lookup_data(self._path, flags)
        self._handle = Rsvg.Handle.new_from_data(data.get_data())
        self.__cache[self._path] = self._handle

        return self._handle

    fragment = GObject.Property(setter=set_fragment, type=str)
    path = GObject.Property(get_path, set_path, str)
