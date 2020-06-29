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
    """A canvas that draws a glyph from the scene"""

    __gtype_name__ = 'Glyph'
    __path = '/com/joansala/auale/canvas/scene.svg'
    __handle = None

    def __init__(self):
        super(Glyph, self).__init__()

        self._fragment = None
        self._surface = None

        self.connect('draw', self.on_draw_request)

    def get_svg_handle(self):
        """Obtain the Rsvg handle to use for drawing"""

        return self.__handle or self.__create_svg_handle()

    def get_image_surface(self):
        """Obtain the current Cairo image surface"""

        return self._surface or self.__create_image_surface()

    def set_fragment(self, fragment):
        """Sets the fragment to render from the .svg"""

        if self._fragment != fragment:
            self._fragment = fragment
            self.invalidate()

    def on_draw_request(self, canvas, context, width, height):
        """Draws the loaded glyph on the canvas"""

        if isinstance(self._fragment, str):
            surface = self.get_image_surface()
            context.set_source_surface(surface)
            context.paint()

    def __create_image_surface(self):
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

    @classmethod
    def __create_svg_handle(self):
        """Creates a new .svg handle for the scene"""

        flags = Gio.ResourceLookupFlags.NONE
        data = Gio.resources_lookup_data(self.__path, flags)
        self.__handle = Rsvg.Handle.new_from_data(data.get_data())

        return self.__handle

    fragment = GObject.Property(setter=set_fragment, type=str)
