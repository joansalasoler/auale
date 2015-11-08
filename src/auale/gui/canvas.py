# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014-2015 Joan Sala Soler <contact@joansala.com>
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

import os
import math
import warnings
import util
import cairo as pycairo

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import cairo
from gi.repository import GdkPixbuf
from gi.repository import Rsvg


class Board(Gtk.DrawingArea):
    """This GTK widget represents an Oware board"""
    
    __gtype_name__ = 'Board'
    
    __gproperties__ = {
        
        'board': (
            GObject.TYPE_PYOBJECT,
            "Board",
            "A list defining an Oware position",
            GObject.PARAM_READWRITE
        ),
        
        'background-image': (
            GObject.TYPE_STRING,
            "Background image",
            "Background image as a PNG file path",
            "",
            GObject.PARAM_READWRITE
        )
    }
        
    __gsignals__ = {
        
        'house-enter-notify-event': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE,
            (GObject.TYPE_INT,)
        ),
        
        'house-leave-notify-event': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE,
            (GObject.TYPE_INT,)
        ),
        
        'house-button-press-event': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE,
            (GObject.TYPE_INT,)
        )
    }
    
    __LABELS_PATH = util.resource_path('./res/image/labels.svg')
    __NUMBERS_PATH = util.resource_path('./res/image/numbers.svg')
    __BACKGROUND_PATH = util.resource_path('./res/image/background.png')
    
    
    def __init__(self):
        """Initalize this canva object"""
        
        super(Board, self).__init__()
        
        self._NOTATION = 'ABCDEFabcdef'
        
        self._HOUSE_POSITIONS = (
            (-275.0,  55.0), (-165.0,  55.0), ( -55.0,  55.0),
            (  55.0,  55.0), ( 165.0,  55.0), ( 275.0,  55.0),
            ( 275.0, -55.0), ( 165.0, -55.0), (  55.0, -55.0),
            ( -55.0, -55.0), (-165.0, -55.0), (-275.0, -55.0)
        )
        
        self._COLOR = {
            'HOUSE':           (0.96, 0.96, 0.96),
            'HOUSE_ACTIVE':    (1.0, 1.0, 0.55),
            'HOUSE_HIGHLIGHT': (0.88, 0.95, 1.0),
            'HOUSE_STROKE':    (0.2, 0.2, 0.2),
            'SEED':            (0.55, 0.75, 0.0),
            'SEED_STROKE':     (0.10, 0.5, 0.2)
        }
        
        self._context = None
        self._board = (0,) * 14
        self._hovered_house = -1
        self._active_house = -1
        self._highlighted_house = -1
        self._wallpaper = None
        self._background_path = ''
        self._angle = 0.0
        
        # Initialize graphic components
        
        try:
            self._labels = Rsvg.Handle().new_from_file(self.__LABELS_PATH)
            self._numbers = Rsvg.Handle().new_from_file(self.__NUMBERS_PATH)
            self._wallpaper = GdkPixbuf.Pixbuf.new_from_file(self.__BACKGROUND_PATH)
            self._background_path = self.__BACKGROUND_PATH
        except:
            self._labels = None
            self._numbers = None
            self._wallpaper = None
        
        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK | \
            Gdk.EventMask.BUTTON_PRESS_MASK | \
            Gdk.EventMask.ENTER_NOTIFY_MASK | \
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        
        self.connect('draw', self.do_draw_event)
        self.set_property('can-focus', True)
        
        
    def do_get_property(self, prop):
        """Gets a property value"""
        
        if prop.name == 'board':
            return self._board
        elif prop.name == 'background-image':
            return self._background_path
        
        
    def do_set_property(self, prop, value):
        """Sets a property value"""
        
        if prop.name == 'board':
            if type(value) != tuple:
                raise TypeError('board must be a tuple')
            
            if len(value) != 14 or sum(value) > 48:
                raise ValueError('not a valid board tuple')
            
            self._hovered_house = -1
            self._board = value
        elif prop.name == 'background-image':
            try:
                self._wallpaper = GdkPixbuf.Pixbuf.new_from_file(value)
                self._background_path = value
            except:
                warnings.warn('cannot load background image')
        
        
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
        
        surface = pycairo.SVGSurface(path, width, height)
        context = pycairo.Context(surface)
        
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
                self.emit('house-leave-notify-event', self._hovered_house)
            if hovered_house != -1:
                self.emit('house-enter-notify-event', hovered_house)
            self._hovered_house = hovered_house
    
    
    def do_button_press_event(self, event):
        """Button press events"""
        
        if self._hovered_house != -1:
            self.emit('house-button-press-event', self._hovered_house)
        
        
    def do_enter_notify_event(self, event):
        """Recomputes hit detection"""
        
        self.do_motion_notify_event(event)
        
        
    def do_leave_notify_event(self, event):
        """Unselect any selected house"""
        
        if self._hovered_house != -1:
            self.emit('house-leave-notify-event', self._hovered_house)
            self._hovered_house = -1
        
        
    def draw_home(self, context, x, y):
        """Draws a home"""
        
        context.new_sub_path()
        context.arc(x, y - 55, 50.0, math.pi, 0.0)
        context.line_to(x + 50, y + 55)
        context.arc(x, y + 55, 50.0, 0.0, math.pi)
        context.line_to(x - 50, y - 55)
        context.set_source_rgb(*self._COLOR['HOUSE'])
        context.fill_preserve()
        context.set_source_rgb(*self._COLOR['HOUSE_STROKE'])
        context.set_line_width(2.0)
        context.stroke()
    
    
    def draw_house(self, context, x, y, active = False, highlight = False):
        """Draws a house"""
        
        context.new_sub_path()
        context.arc(x, y, 50., 0., 2 * math.pi)
        context.set_source_rgb(
            *self._COLOR[
                active and 'HOUSE_ACTIVE' or (
                highlight and 'HOUSE_HIGHLIGHT' or 'HOUSE')]
        )
        context.fill_preserve()
        context.set_source_rgb(*self._COLOR['HOUSE_STROKE'])
        context.set_line_width(2.0)
        context.stroke()
        
        
    def draw_seed(self, context, x, y, radius):
        """Draws a single seed"""
        
        context.new_sub_path()
        context.arc(x, y, radius, 0.0, 2.0 * math.pi)
        context.set_source_rgb(*self._COLOR['SEED'])
        context.fill_preserve()
        context.set_source_rgb(*self._COLOR['SEED_STROKE'])
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
        radius = (seeds > 1 and 6.0 + 3.0 * seeds  or 0.0)
        
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
        
        context.translate(x, y)
        context.rotate(-self._angle)
        
        turn = char.islower() and 'n' or 's'
        label = '#%s%s' % (char.lower(), turn)
        self._labels.render_cairo_sub(context, label)
        
        context.rotate(self._angle)
        context.translate(-x, -y)
        
        
    def draw_number(self, context, x, y, number):
        """Draws a seed number"""
        
        if self._numbers is None:
            return
        
        context.translate(x, y)
        context.rotate(-self._angle)
        
        self._numbers.render_cairo_sub(context, '#%d' % number)
        
        context.rotate(self._angle)
        context.translate(-x, -y)
        
        
    def draw_background(self, width, height, context):
        """Draws a tiled background"""
        
        context.rectangle(0, 0, width, height)
        
        try:
            Gdk.cairo_set_source_pixbuf(context, self._wallpaper, 0, 0)
            pattern = context.get_source()
            pattern.set_extend(2)
        except:
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
        
        
    def rotate(self, angle):
        """Rotates the canvas the specified number of radians"""
        
        self._angle += angle
        self._hovered_house = -1
        
        
    def get_rotation(self):
        """Returns this canvas rotation angle in radians"""
        
        return self._angle
        
    def set_board(self, board):
        """Sets the board property of this object"""
        
        self.set_property('board', board)
        
        
    def set_active(self, house):
        """Sets the active house"""
        
        self._active_house = house
    
    
    def set_highlight(self, house):
        """Sets the highligted house"""
        
        self._highlighted_house = house
    
    
    def get_hovered(self):
        """Returns the current hovered house index"""
        
        return self._hovered_house
    
    
    def update_hovered(self):
        """Updates the hovered house"""
        
        event = Gdk.EventMotion()
        window = self.get_window()
        (w, event.x, event.y, m) = window.get_pointer()
        
        self._hovered_house = -1
        self.do_motion_notify_event(event)
    
    
    def get_active(self):
        """Returns the current active house index"""
        
        return self._active_house
        
        
    def get_highlight(self):
        """Returns the active house"""
        
        return self._highlighted_house

