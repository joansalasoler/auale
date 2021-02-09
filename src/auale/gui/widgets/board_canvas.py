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
from config import theme

from ..actors import House
from ..values import RipeningStage
from ..values import Rotation
from .board_animator import BoardAnimator


class BoardCanvas(GtkClutter.Embed):
    """A widget that displays an oware board"""

    __gtype_name__ = 'BoardCanvas'

    _display = Gdk.Display.get_default()
    _pointer_cursor = Gdk.Cursor.new_from_name(_display, 'pointer')
    _hidden_cursor = Gdk.Cursor.new_from_name(_display, 'none')

    def __init__(self):
        super(BoardCanvas, self).__init__()

        self._script = theme.create_canvas_script()
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
    def canvas_updated(self, match: object):
        """Emitted after the match is updated"""

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
        root = self.get_object('root')

        bind_root = Clutter.BindConstraint()
        bind_root.set_coordinate(Clutter.BindCoordinate.ALL)
        bind_root.set_source(stage)

        root.add_constraint(bind_root)
        stage.set_no_clear_hint(True)
        stage.add_child(root)

    def connect_canvas_signals(self):
        """Connects the required signals"""

        stage = self.get_stage()
        stage.connect('allocation-changed', self.on_allocation_changed)

        for house in self.get_children('houses'):
            house.connect('house-activated', self.on_house_activated)
            house.connect('key-focus-in', self.on_house_key_focus_in)
            house.connect('key-focus-out', self.on_house_key_focus_out)
            house.connect('notify::hovered', self.on_house_hover_changed)

    def is_animation_playing(self):
        """Check if an animation is currently playing"""

        return self._animator.is_playing()

    def get_animator(self):
        """Obtain the board animator"""

        return self._animator

    def get_object(self, name):
        """Obtains a board object given its name"""

        return self._script.get_object(name)

    def get_children(self, name):
        """Obtains the children of a board actor"""

        return self.get_object(name).get_children()

    def get_reactive(self):
        """Checks if this canvas can respond to events"""

        return self._is_reactive and self.is_sensitive()

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

    def get_hovered_house(self):
        """House that is currently hovered"""

        houses = self.get_children('houses')
        house = next((h for h in houses if h.get_hovered()), None)

        return house

    def get_focused_house(self):
        """House that has the key focus or none"""

        stage = self.get_stage()
        focus = stage.get_key_focus()
        is_house = isinstance(focus, House)

        return focus if is_house else None

    def get_cursor_visible(self):
        """Check if the cursor is visible"""

        window = self.get_window()
        cursor = window.get_cursor()
        is_visible = cursor != self._hidden_cursor

        return is_visible

    def set_cursor_visible(self, is_visible):
        """Sets the visibility of the cursor"""

        self.show_cursor() if is_visible else self.hide_cursor()

    def set_reactive(self, is_reactive):
        """If the canvas actors will receive events"""

        self._is_reactive = is_reactive

        for house in self.get_children('houses'):
            move = house.get_move()
            is_legal = move in self._moves
            value = is_reactive and is_legal
            house.set_property('reactive', value)

    def set_rotation(self, rotation):
        """Sets the board rotation angle"""

        if rotation != self._rotation:
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
        self.canvas_updated.emit(match)

    def show_activables(self, match):
        """Highlight the houses that can be activated"""

        for house in self.get_children('houses'):
            is_valid = match.is_valid_move(house.get_move())
            house.set_property('activable', is_valid)

    def animate_move(self, match):
        """Animates the last move from a match"""

        self._animator.stop_animation()
        self._animator.animate_move(match)
        self.set_reactive(False)

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
        is_active = house.is_move(match.get_move())
        state = self.get_ripening_stage(move, seeds, match)
        canvas = self.get_seed_canvas(seeds)

        house.set_content(canvas)
        house.set_property('activated', is_active)
        house.set_property('activable', True)
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

        if len(self._activables):
            length = len(self._activables)
            index = self._activables.index(current)
            direction = self._rotation.direction
            next_index = (index + direction) % length
            house = self._activables[next_index]
            house.grab_key_focus()

    def focus_previous_house(self):
        """Set key focus on the previous activable house"""

        current = self.get_focused_house()

        if current not in self._activables:
            return self.focus_last_house()

        if len(self._activables):
            length = len(self._activables)
            index = self._activables.index(current)
            direction = -self._rotation.direction
            previous_index = (index + direction) % length
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

    def hide_cursor(self):
        """Sets the cursor visibility as hidden"""

        window = self.get_window()
        window.set_cursor(self._hidden_cursor)

    def show_cursor(self):
        """Sets the cursor visibility as visible"""

        hovered_house = self.get_hovered_house()
        cursor = self._pointer_cursor if hovered_house else None
        window = self.get_window()
        window.set_cursor(cursor)

    def on_allocation_changed(self, stage, box, flags):
        """Scale the scene when the stage is resized"""

        stage_width = box.get_width()
        stage_height = box.get_height()

        for child in self.get_children('root'):
            width, height = child.get_size()
            scale = min(stage_width / width, stage_height / height)
            child.set_scale(scale, scale)

    def on_house_activated(self, house):
        """Bubble house activation signals"""

        self.house_activated.emit(house)

    def on_house_hover_changed(self, house, params):
        """Show a hand cursor whenever a house is hovered"""

        if self.get_cursor_visible():
            self.show_cursor()

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

        stage = self.get_stage()

        if isinstance(stage, Clutter.Stage):
            stage.set_key_focus(house)
            self.grab_focus()
