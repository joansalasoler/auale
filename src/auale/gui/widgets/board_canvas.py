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
from gi.repository import Gdk
from gi.repository import GLib
from gi.repository import GObject
from gi.repository import GtkClutter

from ..actors import House
from ..actors import Mosaic
from ..values import RipeningStage
from ..values import Rotation
from .board_animator import BoardAnimator


class BoardCanvas(GtkClutter.Embed):
    """A widget that displays an oware board"""

    __gtype_name__ = 'BoardCanvas'
    __scene_path = '/com/joansala/auale/canvas/board.json'
    __states_path = '/com/joansala/auale/canvas/states.json'

    _display = Gdk.Display.get_default()
    _pointer = Gdk.Cursor.new_from_name(_display, 'pointer')

    def __init__(self):
        super(BoardCanvas, self).__init__()

        self._script = Clutter.Script()
        self._script.load_from_resource(self.__scene_path)
        self._script.load_from_resource(self.__states_path)
        self._animator = BoardAnimator(self)
        self._rotation = Rotation.BASE
        self._is_reactive = True
        self._activables = []
        self._sowings = [[], ] * 12
        self._moves = []

        self.setup_canvas_stage()
        self.connect_canvas_signals()
        self.set_support_multidevice(True)

    @GObject.Signal
    def animation_completed(self):
        """Emitted when a move animation is completed"""

    @GObject.Signal
    def house_activated(self, house: object):
        """Emitted when a house is activated"""

        self.activate_house(house)

    @GObject.Signal
    def house_focused(self, house: object):
        """Emitted when a house is focused"""

        GLib.idle_add(self._refresh_house_focus, house)

    @GObject.Signal
    def board_rotated(self, rotation: object):
        """Emitted when the board is rotated"""

    def setup_canvas_stage(self):
        """Configures this canvas's stage"""

        stage = self.get_stage()
        scene = self.get_object('scene')
        overlay = self.get_object('overlay')

        mosaic = Mosaic()
        mosaic.allocate_image()

        align_scene = Clutter.AlignConstraint()
        align_scene.set_align_axis(Clutter.AlignAxis.BOTH)
        align_scene.set_source(stage)
        align_scene.set_factor(0.5)
        scene.add_constraint(align_scene)

        align_overlay = Clutter.AlignConstraint()
        align_overlay.set_align_axis(Clutter.AlignAxis.X_AXIS)
        align_overlay.set_source(stage)
        align_overlay.set_factor(0.5)
        overlay.add_constraint(align_overlay)

        stage.set_content(mosaic)
        stage.set_content_repeat(Clutter.ContentRepeat.BOTH)
        stage.set_no_clear_hint(True)
        stage.add_child(scene)
        stage.add_child(overlay)

    def connect_canvas_signals(self):
        """Connects the required signals"""

        stage = self.get_stage()
        stage.connect('allocation-changed', self.on_allocation_changed)

        for house in self.get_children('houses'):
            house.connect('house-activated', self.house_activated.emit)
            house.connect('key-focus-in', self.on_house_key_focus_in)
            house.connect('key-focus-out', self.on_house_key_focus_out)
            house.connect('notify::hovered', self.on_house_hover_changed)

    def get_object(self, name):
        """Obtains a board object given its name"""

        return self._script.get_object(name)

    def get_children(self, name):
        """Obtains the children of a board actor"""

        return self.get_object(name).get_children()

    def get_reactive(self):
        """Checks if this canvas can respond to events"""

        return self._is_reactive and self.is_sensitive()

    def set_reactive(self, is_reactive):
        """If the canvas actors will receive events"""

        self._is_reactive = is_reactive

        for house in self.get_children('houses'):
            house.set_property('reactive', is_reactive)

    def set_rotation(self, rotation):
        """Sets the board rotation angle"""

        self._rotation = rotation
        scene_state = self.get_object('scene-rotation')
        house_state = self.get_object('house-rotation')
        scene_state.set_state(rotation.nick)
        house_state.set_state(rotation.nick)
        self.board_rotated.emit(rotation)

    def show_match(self, match):
        """Displays a match position on the board"""

        self._moves = match.get_legal_moves()
        self._animator.stop_animation()

        self.set_reactive(True)
        self.update_houses(match)
        self.update_sowings(match)
        self.update_focus(self._moves)

    def animate_move(self, match):
        """Animates the last move from a match"""

        self._animator.stop_animation()
        self._animator.animate_move(match)
        self.set_reactive(False)

    def get_seed_canvas(self, number):
        """Canvas for the given number of seeds"""

        return self.get_object(f'seed-canvas-{ number }')

    def get_sow_canvas(self, number):
        """Hint for the given number of seeds"""

        return self.get_object(f'sow-canvas-{ number }')

    def get_ripening_stage(self, move, seeds, match):
        """Rippening state of a move if it contains the given seeds"""

        is_capture = match.is_capture_move(move)
        house_state = RipeningStage.GREEN

        for state in RipeningStage:
            if seeds >= state.minimum_seeds:
                if is_capture == state.needs_capture:
                    house_state = state

        return house_state

    def get_focused_house(self):
        """House that has the key focus or none"""

        stage = self.get_stage()
        focus = stage.get_key_focus()
        is_house = isinstance(focus, House)

        return focus if is_house else None

    def activate_house(self, house):
        """Activates the given house"""

        houses = self.get_children('houses')

        if not house.get_activated():
            house.activate()

        for actor in (h for h in houses if h != house):
            actor.set_property('activated', False)

    def update_houses(self, match):
        """Updates the houses from the given match"""

        for house in self.get_children('houses'):
            self.update_house(house, match)

    def update_house(self, house, match):
        """Updates a single house from a match"""

        move = house.get_move()
        seeds = match.get_seeds(move)
        is_valid = match.is_valid_move(move)
        is_legal = match.is_legal_move(move)
        is_active = house.is_move(match.get_move())
        state = self.get_ripening_stage(move, seeds, match)
        canvas = self.get_seed_canvas(seeds)

        house.set_content(canvas)
        house.set_property('reactive', is_legal)
        house.set_property('activated', is_active)
        house.set_property('activable', is_valid)
        house.set_property('state', state)

    def update_hints(self, move):
        """Updates the hints for a legal move"""

        sowings = self._sowings[move]
        counts = [sowings.count(i) for i in range(12)]
        last_move = sowings[-1]

        for hint in self.get_children('hints'):
            house_move = hint.get_house().get_move()
            seeds = counts[house_move]
            is_last = house_move == last_move
            opacity = 255 if is_last else 127

            canvas = self.get_sow_canvas(seeds)
            hint.set_scale(0.0, 0.0)
            hint.set_opacity(opacity)
            hint.set_content(canvas)

    def update_focus(self, moves):
        """Update the focus queue houses"""

        stage = self.get_stage()
        stage.set_key_focus(None)

        self._activables.clear()

        for house in self.get_children('houses'):
            if house.get_move() in moves:
                self._activables.append(house)

    def update_sowings(self, match):
        """Update the sowing hints from a match"""

        game = match.get_game()
        board = match.get_board()

        for move in self._moves:
            sowings = game.get_sowings(board, move)
            self._sowings[move] = sowings

    def focus_next_house(self):
        """Set key focus on the next activable house"""

        current = self.get_focused_house()

        if current not in self._activables:
            return self.focus_first_house()

        if count := len(self._activables):
            index = self._activables.index(current)
            direction = self._rotation.direction
            next_index = (index + direction) % count
            house = self._activables[next_index]
            house.grab_key_focus()

    def focus_previous_house(self):
        """Set key focus on the previous activable house"""

        current = self.get_focused_house()

        if current not in self._activables:
            return self.focus_last_house()

        if count := len(self._activables):
            index = self._activables.index(current)
            direction = -self._rotation.direction
            previous_index = (index + direction) % count
            house = self._activables[previous_index]
            house.grab_key_focus()

    def focus_first_house(self):
        """Set key focus on the first activable house"""

        if len(self._activables):
            index = min(0, self._rotation.direction)
            house = self._activables[index]
            house.grab_key_focus()

    def focus_last_house(self):
        """Set key focus on the last activable house"""

        if len(self._activables):
            index = min(0, -self._rotation.direction)
            house = self._activables[index]
            house.grab_key_focus()

    def on_allocation_changed(self, stage, box, flags):
        """Scale the scene when the stage is resized"""

        scene = self.get_object('scene')
        overlay = self.get_object('overlay')
        width, height = scene.get_size()
        scale = min(box.get_width() / width, box.get_height() / height)
        scene.set_scale(scale, scale)
        overlay.set_scale(scale, scale)

    def on_house_hover_changed(self, house, params):
        """Show a hand cursor whenever a house is hovered"""

        is_hovered = house.get_hovered()
        cursor = self._pointer if is_hovered else None
        self.get_window().set_cursor(cursor)

    def on_house_key_focus_in(self, house):
        """Show hints when a house receives the focus"""

        if house.get_reactive() is True:
            self.house_focused.emit(house)
            self.update_hints(house.get_move())
            state = self.get_object('hint-visibility')
            state.set_state('visible')

    def on_house_key_focus_out(self, house):
        """Hide hints when a house loses the focus"""

        state = self.get_object('hint-visibility')
        state.set_state('hidden')

    def show_message(self):
        """Shows the message of the board"""

        state = self.get_object('message-visibility')
        state.set_state('visible')

    def hide_message(self):
        """Hides the message of the board"""

        state = self.get_object('message-visibility')
        state.set_state('hidden')

    def set_message_visible(self, visible):
        """Toggles the visibility of the board's message"""

        self.show_message() if visible else self.hide_message()

    def _refresh_house_focus(self, house):
        """Ensures this widget is focused"""

        if stage := self.get_stage():
            stage.set_key_focus(house)
            self.grab_focus()
