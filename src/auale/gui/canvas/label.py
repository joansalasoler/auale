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
from gi.repository import cairo as Cairo
from gi.repository import PangoCairo
from gi.repository import Pango


class Label(Clutter.Canvas):
    """Draws a canvas containing some text"""

    __gtype_name__ = 'Label'

    def __init__(self):
        super(Label, self).__init__()

        self._text = ''
        self._font = Pango.font_description_from_string('Ubuntu Bold 14')
        self._stroke_color = (0.30, 0.30, 0.30, 1.0)
        self._shadow_color = (0.20, 0.20, 0.20, 1.0)
        self._text_color = (0.96, 0.96, 0.96, 1.0)
        self.connect('draw', self.on_draw_request)

    def set_color(self, red, green, blue, alpha=1.0):
        """Color for the label's text"""

        self.text_color = (red, green, blue, alpha)
        self.invalidate()

    def set_text(self, text):
        """Text to display"""

        self._text = text
        self.invalidate()

    def set_size(self, size):
        """Font size in fractional points"""

        self._font.set_absolute_size(size)
        self.invalidate()

    def on_draw_request(self, canvas, context, width, height):
        """Draws the loaded glyph on the canvas"""

        line_width = 0.125 * self._font.get_size() / Pango.SCALE
        layout = PangoCairo.create_layout(context)
        layout.set_ellipsize(Pango.EllipsizeMode.END)
        layout.set_font_description(self._font)
        layout.set_height(height * Pango.SCALE)
        layout.set_width(width * Pango.SCALE)
        layout.set_text(self._text, -1)

        self._setup_context(context)
        self._clear_context(context)

        context.save()
        context.translate(0.0, 2.0)
        PangoCairo.layout_path(context, layout)
        context.set_source_rgba(*self._shadow_color)
        context.fill()
        context.restore()

        PangoCairo.layout_path(context, layout)
        context.set_source_rgba(*self._stroke_color)
        context.set_line_width(line_width)
        context.stroke_preserve()
        context.set_source_rgba(*self._text_color)
        context.fill()

    def _clear_context(self, context):
        """Clears a drawing context"""

        context.save()
        context.set_operator(Cairo.Operator.CLEAR)
        context.paint()
        context.restore()

    def _setup_context(self, context):
        """Configure the drawing context"""

        context.set_antialias(Cairo.Antialias.BEST)
