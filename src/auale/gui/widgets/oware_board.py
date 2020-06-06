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

import math
import cairo
import logging

from gi.repository import Gdk
from gi.repository import GdkPixbuf
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Rsvg


class OwareBoard(Gtk.DrawingArea):
    """This GTK widget represents an Oware board"""

    __gtype_name__ = 'OwareBoard'

    __LABELS_PATH = '/com/joansala/auale/images/labels.svg'
    __NUMBERS_PATH = '/com/joansala/auale/images/numbers.svg'
    __BACKGROUND_PATH = '/com/joansala/auale/images/background.png'

    _NOTATION = 'ABCDEFabcdef'

    _COLORS = {
        'HOUSE': (0.96, 0.96, 0.96),
        'HOUSE_ACTIVE': (1.0, 1.0, 0.55),
        'HOUSE_HIGHLIGHT': (0.75, 0.89, 1.0),
        'HOUSE_STROKE': (0.2, 0.2, 0.2),
        'SEED': (0.47, 0.72, 0.12),
        'SEED_STROKE': (0.10, 0.5, 0.2)
    }

    _HOUSE_POSITIONS = (
        (-275.0, 55.0), (-165.0, 55.0), (-55.0, 55.0),
        (55.0, 55.0), (165.0, 55.0), (275.0, 55.0),
        (275.0, -55.0), (165.0, -55.0), (55.0, -55.0),
        (-55.0, -55.0), (-165.0, -55.0), (-275.0, -55.0)
    )

    def __init__(self):
        super(OwareBoard, self).__init__()

        self._context = None
        self._board = (0,) * 14
        self._hovered_house = -1
        self._active_house = -1
        self._highlighted_house = -1
        self._wallpaper = None
        self._angle = 0.0

        self._labels = self.new_labels_svg_handle()
        self._numbers = self.new_numbers_svg_handle()
        self._wallpaper = self.new_default_wallpaper()

        self.add_events(Gdk.EventMask.ALL_EVENTS_MASK)
        self.connect('draw', self.do_draw_event)
        self.set_property('can-focus', True)

    @GObject.Signal
    def house_enter(self, house: int):
        """Emitted when the pointer enters a house"""

    @GObject.Signal
    def house_leave(self, house: int):
        """Emitted when the pointer leaves a house"""

    @GObject.Signal
    def house_pressed(self, house: int):
        """Emitted when a house is pressed"""

    def get_rotation(self):
        """Returns this canvas rotation angle in radians"""

        return self._angle

    def get_active(self):
        """Returns the current active house index"""

        return self._active_house

    def get_highlight(self):
        """Returns the active house"""

        return self._highlighted_house

    def get_board(self):
        """Obtains the displayed board tuple"""

        return self._board

    def set_active(self, house):
        """Sets the active house"""

        self._active_house = house
        self.queue_draw()

    def set_highlight(self, house):
        """Sets the highligted house"""

        self._highlighted_house = house
        self.queue_draw()

    def set_board(self, board):
        """Sets the displayed board position as a tuple"""

        if not isinstance(board, tuple):
            raise TypeError('Board must be a tuple')

        if len(board) != 14 or sum(board) > 48:
            raise ValueError('Not a valid board tuple')

        self._hovered_house = -1
        self._board = board
        self.queue_draw()

    def set_rotation(self, angle):
        """Sets the canvas rotation in radians"""

        self._angle = angle
        self._hovered_house = -1
        self.queue_draw()

    def new_default_wallpaper(self):
        """Obtains the default wallpaper image"""

        return GdkPixbuf.Pixbuf.new_from_resource(self.__BACKGROUND_PATH)

    def new_labels_svg_handle(self):
        """Obtains a new labels SVG handle"""

        return self.new_svg_from_resource(self.__LABELS_PATH)

    def new_numbers_svg_handle(self):
        """Obtains a new numbers SVG handle"""

        return self.new_svg_from_resource(self.__NUMBERS_PATH)

    def do_draw_event(self, widget, context):
        """Performs all drawing operations"""

        self._context = context

        allocation = widget.get_allocation()
        (width, height) = (allocation.width, allocation.height)

        self.draw_background(width, height, context)
        self.transform_canvas(width, height, context)
        self.draw_board(context)

    def export_svg(self, path, width, height):
        """Exports the current canvas to an SVG file"""

        surface = cairo.SVGSurface(path, width, height)
        context = cairo.Context(surface)

        self.transform_canvas(width, height, context)
        self.draw_board(context)

        surface.flush()
        surface.finish()

    def do_motion_notify_event(self, event):
        """Hit detection"""

        if not self._context:
            return

        # Transform the canvas again

        an = self.get_allocation()
        self._context.identity_matrix()
        self.transform_canvas(an.width, an.height, self._context)

        # Transform mouse coordinates

        matrix = self._context.get_matrix()
        matrix.invert()
        (x, y) = matrix.transform_point(event.x, event.y)

        # House detection

        hovered_house = -1
        for house in range(12):
            (i, j) = self._HOUSE_POSITIONS[house]
            self._context.arc(i, j, 50., 0., 2 * math.pi)

            if self._context.in_fill(x, y):
                hovered_house = house
                self._context.new_path()
                break

            self._context.new_path()

        # Send events

        if hovered_house != self._hovered_house:
            if self._hovered_house != -1:
                self.house_leave.emit(self._hovered_house)
            if hovered_house != -1:
                self.house_enter.emit(hovered_house)
            self._hovered_house = hovered_house

    def do_button_press_event(self, event):
        """Button press events"""

        if self._hovered_house != -1:
            self.house_pressed.emit(self._hovered_house)

    def do_enter_notify_event(self, event):
        """Recomputes hit detection"""

        self.do_motion_notify_event(event)

    def do_leave_notify_event(self, event):
        """Unselect any selected house"""

        if self._hovered_house != -1:
            self.house_leave.emit(self._hovered_house)
            self._hovered_house = -1

    def draw_home(self, context, x, y):
        """Draws a home"""

        context.new_sub_path()
        context.arc(x, y - 55, 50.0, math.pi, 0.0)
        context.line_to(x + 50, y + 55)
        context.arc(x, y + 55, 50.0, 0.0, math.pi)
        context.line_to(x - 50, y - 55)
        context.set_source_rgb(*self._COLORS['HOUSE'])
        context.fill_preserve()
        context.set_source_rgb(*self._COLORS['HOUSE_STROKE'])
        context.set_line_width(2.0)
        context.stroke()

    def draw_house(self, context, x, y, active=False, highlight=False):
        """Draws a house"""

        context.new_sub_path()
        context.arc(x, y, 50., 0., 2 * math.pi)
        context.set_source_rgb(
            *self._COLORS[
                active and 'HOUSE_ACTIVE' or (
                    highlight and 'HOUSE_HIGHLIGHT' or 'HOUSE')]
        )
        context.fill_preserve()
        context.set_source_rgb(*self._COLORS['HOUSE_STROKE'])
        context.set_line_width(2.0)
        context.stroke()

    def draw_seed(self, context, x, y, radius):
        """Draws a single seed"""

        context.new_sub_path()
        context.arc(x, y, radius, 0.0, 2.0 * math.pi)
        context.set_source_rgb(*self._COLORS['SEED'])
        context.fill_preserve()
        context.set_source_rgb(*self._COLORS['SEED_STROKE'])
        context.set_line_width(1.5)
        context.stroke()

    def draw_seeds(self, context, x, y, number):
        """Draws the specified number of seeds"""

        # Zero seeds

        if number < 1:
            return

        # More than six seeds

        seeds = number
        if 10 > seeds > 6:
            # Draw a single seed on the center

            seeds -= 1
            self.draw_seed(context, x, y, 10.0)
        elif seeds > 9:
            # Draw a big numbered seed

            seeds = 9
            self.draw_seed(context, x, y, 19.0)
            self.draw_number(context, x, y, number)

        # Remaining seeds

        angle = 2.0 * math.pi / seeds
        radius = (seeds > 1 and 6.0 + 3.0 * seeds or 0.0)

        for n in range(seeds):
            self.draw_seed(
                context,
                x + radius * math.cos(n * angle),
                y + radius * math.sin(n * angle),
                10.0
            )

    def draw_label(self, context, x, y, char):
        """Draws a notation label"""

        if self._labels is None:
            return

        context.save()
        context.translate(x, y)
        context.rotate(-self._angle)

        turn = char.islower() and 'n' or 's'
        label = '#%s%s' % (char.lower(), turn)
        self._labels.render_cairo_sub(context, label)

        context.restore()

    def draw_number(self, context, x, y, number):
        """Draws a seed number"""

        if self._numbers is None:
            return

        context.save()
        context.translate(x, y)
        context.rotate(-self._angle)

        self._numbers.render_cairo_sub(context, '#%d' % number)

        context.restore()

    def draw_background(self, width, height, context):
        """Draws a tiled background"""

        context.rectangle(0, 0, width, height)

        if self._wallpaper:
            Gdk.cairo_set_source_pixbuf(context, self._wallpaper, 0, 0)
            pattern = context.get_source()
            pattern.set_extend(2)
        else:
            context.set_source_rgb(0.7, 0.5, 0.3)

        context.fill()

    def draw_board(self, context):
        """Draws the current board"""

        # Draw home holes

        self.draw_home(context, 390, 0)
        self.draw_home(context, -390, 0)
        self.draw_seeds(context, 390, 0, self._board[12])
        self.draw_seeds(context, -390, 0, self._board[13])

        # Draw houses and labels

        for house in range(12):
            (x, y) = self._HOUSE_POSITIONS[house]

            self.draw_house(
                context, x, y,
                house == self._active_house,
                house == self._highlighted_house
            )

            self.draw_seeds(context, x, y, self._board[house])

            self.draw_label(
                context, x, y + (house < 6 and 90 or -90),
                self._NOTATION[house]
            )

    def transform_canvas(self, width, height, context):
        """Translates, scales and rotates this canvas"""

        # Move origin to the center

        context.translate(width / 2.0, height / 2.0)

        # Scale to fit the widget area

        scale = min(width / 1000.0, height / 500.0)
        context.scale(scale, scale)

        # Rotate the board

        context.rotate(self._angle)

    def update_hovered(self):
        """Updates the hovered house"""

        event = Gdk.EventMotion()
        window = self.get_window()
        (w, event.x, event.y, m) = window.get_pointer()

        self._hovered_house = -1
        self.do_motion_notify_event(event)

    def new_svg_from_resource(self, resource_path):
        """Creates a new SVG handle from a resource path"""

        try:
            handle = None
            flags = Gio.ResourceLookupFlags.NONE
            data = Gio.resources_lookup_data(resource_path, flags)
            handle = Rsvg.Handle.new_from_data(data.get_data())
        except BaseException as e:
            logging.warn(f'Could not load resource { resource_path }')
            logging.debug(e)

        return handle
