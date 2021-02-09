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

from gi.repository import GObject
from ..animation import Capture
from ..animation import Energize
from ..animation import Pick
from ..animation import Ripe
from ..animation import Sow


class BoardAnimator(GObject.GObject):
    """Animates moves on the board canvas"""

    __gtype_name__ = 'BoardAnimator'
    __STEP_DELAY = 250

    def __init__(self, canvas):
        GObject.GObject.__init__(self)

        self._canvas = canvas
        self._is_playing = False
        self._transitions = set()

    @GObject.Signal
    def capture_animation(self, transition: object):
        """Emitted when a capture animation starts"""

    @GObject.Signal
    def harvest_animation(self, transition: object):
        """Emitted when a harvest animation starts"""

    @GObject.Signal
    def pick_animation(self, transition: object):
        """Emitted when a pick animation starts"""

    @GObject.Signal
    def ripe_animation(self, transition: object):
        """Emitted when a ripening animation starts"""

    @GObject.Signal
    def sow_animation(self, transition: object):
        """Emitted when a sow animation starts"""

    def is_playing(self):
        """Check if the animation is playing"""

        return self._is_playing

    def animate_move(self, match):
        """Animate the move that lead to the current match position"""

        self._is_playing = True
        self._push_move_transitions(match)
        self._start_transitions()

    def stop_animation(self):
        """Stop the current animation if it is playing"""

        self._clear_transitions()
        self._is_playing = False

    def _start_transitions(self):
        """Starts the attached transitions"""

        for transition in self._transitions:
            transition.attach()

    def _clear_transitions(self):
        """Stops and detaches any pending transitions"""

        while self._transitions:
            transition = self._transitions.pop()
            transition.detach()
            transition.stop()

    def _remove_transition(self, transition):
        """Discard a completed transition"""

        transition.detach()
        self._transitions.discard(transition)

        return self._transitions

    def _push_transition(self, transition, match):
        """Attach a house transition for the given match"""

        self._transitions.add(transition)
        callback = self._on_transition_completed
        transition.connect('completed', callback, match)

        return self._transitions

    def _push_move_transitions(self, match):
        """Add animation for the last move on a match"""

        steps = self._push_pick_transitions(0, match)
        steps = self._push_sow_transitions(steps, match)
        steps = self._push_ripe_transitions(steps, match)
        steps = self._push_capture_transitions(steps, match)
        steps = self._push_harvest_transitions(steps, match)

    def _push_pick_transitions(self, steps, match):
        """Add animations to pick the house seeds"""

        for house in self._canvas.get_children('houses'):
            is_move = match.get_move() == house.get_move()
            transition = Pick(house) if is_move else Energize(house)
            transition.connect('started', self.pick_animation.emit)
            self._push_transition(transition, match)

        return steps + 1

    def _push_sow_transitions(self, steps, match):
        """Add animations to sow the picked seeds"""

        move = match.get_move()
        sowings = match.get_sowings()
        board = list(match.get_board(-2))

        for step, move in enumerate(sowings, steps):
            board[move] += 1
            seeds = board[move]
            content = self._canvas.get_seed_canvas(seeds)
            house = self._canvas.get_object(f'house-{ move }')
            state = self._canvas.get_ripening_stage(move, seeds, match)

            transition = Sow(house)
            transition.set_state(state)
            transition.set_content(content)
            transition.set_delay(step * self.__STEP_DELAY)
            transition.connect('started', self.sow_animation.emit)
            self._push_transition(transition, match)

        return steps + len(sowings)

    def _push_capture_transitions(self, steps, match):
        """Add animations to capture the house seeds"""

        move = match.get_move()
        sowings = match.get_sowings()
        current = match.get_board()
        previous = match.get_board(-2)

        previous = [s + sowings.count(i) for i, s in enumerate(previous)]
        moves = [i for i in range(11, -1, -1) if current[i] == 0]
        houses = [i for i in moves if i != move and previous[i] != 0]

        for step, move in enumerate(houses, steps):
            house = self._canvas.get_object(f'house-{ move }')

            transition = Capture(house)
            transition.set_delay(step * self.__STEP_DELAY)
            transition.connect('started', self.capture_animation.emit)
            self._push_transition(transition, match)

        return steps + len(houses)

    def _push_harvest_transitions(self, steps, match):
        """Add animations to harvest seeds onto the player's homes"""

        current = match.get_board()
        previous = match.get_board(-2)
        houses = [i for i in (12, 13) if current[i] != previous[i]]
        delay = (steps + .5) * self.__STEP_DELAY

        for move in houses:
            seeds = match.get_seeds(move)
            content = self._canvas.get_seed_canvas(seeds)
            house = self._canvas.get_object(f'house-{ move }')

            transition = Sow(house)
            transition.set_delay(delay)
            transition.set_content(content)
            transition.connect('started', self.harvest_animation.emit)
            self._push_transition(transition, match)

        return steps + .5

    def _push_ripe_transitions(self, steps, match):
        """Add animations to show the ripening state"""

        move = match.get_move()
        delay = steps * self.__STEP_DELAY

        for house in self._canvas.get_children('houses'):
            move = house.get_move()
            seeds = match.get_seeds(move)
            state = self._canvas.get_ripening_stage(move, seeds, match)

            transition = Ripe(house)
            transition.set_state(state)
            transition.set_delay(delay)
            transition.connect('started', self.ripe_animation.emit)
            self._push_transition(transition, match)

        return steps

    def _on_transition_completed(self, transition, match):
        """Fired when a transition for a match is completed"""

        if not self._remove_transition(transition):
            self._is_playing = False
            self._canvas.show_match(match)
            self._canvas.animation_completed.emit()
