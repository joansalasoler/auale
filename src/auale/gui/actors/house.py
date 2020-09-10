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
from gi.repository import GObject

from .actor import Actor
from ..values import RipeningStage


class House(Actor):
    """An actionable playing house on the board"""

    __gtype_name__ = 'House'

    def __init__(self):
        super(House, self).__init__()

        self._move = None
        self._activable = False
        self._activated = False
        self._hovered = False
        self._pressed = False
        self._state = RipeningStage.GREEN

        self.set_reactive(False)
        self.set_easing_duration(150)
        self.set_easing_mode(Clutter.AnimationMode.LINEAR)

        self.connect('button-press-event', self.on_button_press_event)
        self.connect('button-release-event', self.on_button_release_event)
        self.connect('motion-event', self.on_motion_event)
        self.connect('leave-event', self.on_leave_event)
        self.connect('notify::reactive', self.on_leave_event)

    @GObject.Signal
    def house_activated(self):
        """Emitted when the user activates a house"""

    def get_hovered(self):
        """Get the hovered status of the house"""

        return self._hovered

    def set_hovered(self, hovered):
        """Set the hovered status of the house"""

        self._hovered = hovered

    def get_pressed(self):
        """Get the pressed status of the house"""

        return self._pressed

    def set_pressed(self, pressed):
        """Set the pressed status of the house"""

        self._pressed = pressed

    def get_activated(self):
        """Get the activated status of the house"""

        return self._activated

    def set_activated(self, activated):
        """Set the activated status of the house"""

        self._activated = activated

    def get_activable(self):
        """Whether the house can be activated"""

        return self._activable

    def set_activable(self, activable):
        """Set if the house can be activated"""

        move = self.get_move()
        is_opaque = activable or move > 11

        self._activable = activable
        self.set_opacity(255 if is_opaque else 127)

    def is_move(self, move):
        """Check if a move is linked to the house"""

        return move == self._move

    def get_move(self):
        """Get the move linked to the house"""

        return self._move

    def set_move(self, move):
        """Set the move linked to the house"""

        self._move = move

    def get_state(self):
        """Get the ripening state of the house"""

        return self._state

    def set_state(self, state):
        """Set the ripening state of the house"""

        self._state = state

    def activate(self):
        """Activates this house"""

        self.set_property('activated', True)
        self.house_activated.emit()

    def on_motion_event(self, actor, event):
        """Emitted when the pointer moves over the actor"""

        point = self.transform_stage_point(event.x, event.y)
        hovered = self.is_inside_point(point.x_out, point.y_out)
        has_changed = hovered != self._hovered

        if hovered and not self.has_key_focus():
            self.grab_key_focus()

        if not hovered and self.has_key_focus():
            stage = self.get_stage()
            stage.set_key_focus(None)

        if hovered and has_changed:
            self.set_property('hovered', True)

        if not hovered and has_changed:
            self.set_property('pressed', False)
            self.set_property('hovered', False)

    def on_leave_event(self, actor, event):
        """Emitted when the pointer leaves the actor"""

        if self.has_key_focus():
            parent = self.get_parent()
            parent.grab_key_focus()

        if self._hovered is True:
            self.set_property('pressed', False)
            self.set_property('hovered', False)

    def on_button_press_event(self, actor, event):
        """Emitted when mouse button is pressed on the actor"""

        point = self.transform_stage_point(event.x, event.y)

        if self.is_inside_point(point.x_out, point.y_out):
            if event.button == Clutter.BUTTON_PRIMARY:
                self.set_property('pressed', True)

    def on_button_release_event(self, actor, event):
        """Emitted when mouse button is released on the actor"""

        point = self.transform_stage_point(event.x, event.y)

        if self.is_inside_point(point.x_out, point.y_out):
            if self._pressed and event.button == Clutter.BUTTON_PRIMARY:
                self.activate()

    def is_inside_point(self, x, y):
        """Checks if a point is inside the house"""

        radius = self.get_width() / 2.0
        distance = pow(x - radius, 2) + pow(y - radius, 2)
        is_inside = (distance <= pow(radius, 2))

        return is_inside

    move = GObject.Property(get_move, set_move, int)
    state = GObject.Property(get_state, set_state, object)
    activated = GObject.Property(get_activated, set_activated, bool, False)
    activable = GObject.Property(get_activable, set_activable, bool, False)
    hovered = GObject.Property(get_hovered, set_hovered, bool, False)
    pressed = GObject.Property(get_pressed, set_pressed, bool, False)
