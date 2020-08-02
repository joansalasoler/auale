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

import logging

from threading import Lock
from gi.repository import GLib
from gi.repository import GObject
from game import Match
from uci import Engine
from .ponder_cache import PonderCache


class GameLoop(GObject.GObject):
    """Represents the game loop"""

    __gtype_name__ = 'GameLoop'
    __move_delay = 1.6

    def __init__(self):
        GObject.GObject.__init__(self)

        self._active_player = None
        self._current_player = None
        self._previous_player = None
        self._request_lock = Lock()
        self._ponder_cache = PonderCache(256)
        self._logger = logging.getLogger('game-loop')

    @GObject.Signal
    def move_received(self, player: object, move: int):
        """Emitted when the active player makes a move"""

    @GObject.Signal
    def info_received(self, player: object, values: object):
        """Emitted when a player wants to send a search report"""

    def request_move(self, player, match):
        """Requests a player to make a move"""

        if not isinstance(match, Match) or match.has_ended():
            return self.abort_move()

        self._logger.debug('Received a move request')

        with self._request_lock:
            self._active_player = None

            if self._is_entering_player(player):
                self._connect_player(player)

            if self._is_substitute_player(player):
                self._switch_to_waiting(self._previous_player)
                self._disconnect_player(self._previous_player)

            self._previous_player = self._current_player
            self._current_player = player

            if self._current_player != self._previous_player:
                self._switch_to_waiting(self._previous_player)
                self._switch_to_pondering(self._previous_player, match)

            self._switch_to_waiting(self._current_player)
            self._switch_to_thinking(self._current_player, match)

        self._logger.debug('Move requested for player')

    def abort_move(self):
        """Aborts any ongoing move requests"""

        self._logger.debug('Received a move abortion request')

        with self._request_lock:
            self._active_player = None
            self._switch_to_waiting(self._current_player)
            self._switch_to_waiting(self._previous_player)

        self._logger.debug('Current move request was aborted')

    def _is_entering_player(self, player):
        """Checks if its a new player entering the match"""

        is_current = (player == self._current_player)
        is_previous = (player == self._previous_player)

        return not is_current and not is_previous

    def _is_substitute_player(self, player):
        """Checks if the player substitutes a previous one"""

        is_previous = (player == self._previous_player)
        is_same = (self._previous_player == self._current_player)

        return not is_previous and not is_same

    def _connect_player(self, player):
        """Connects a player to the signal handlers"""

        if isinstance(player, Engine):
            player.connect('move-received', self._on_move_received)
            player.connect('info-received', self._on_info_received)

    def _disconnect_player(self, player):
        """Disconnects a player from the signal handlers"""

        if isinstance(player, Engine):
            player.disconnect_by_func(self._on_info_received)
            player.disconnect_by_func(self._on_move_received)

    def _switch_to_waiting(self, player):
        """Switches a player state to waiting for a command"""

        if isinstance(player, Engine):
            player.stop_thinking()

    def _switch_to_thinking(self, player, match):
        """Switches a player state to searching for a move"""

        if isinstance(player, Engine):
            self._active_player = player
            player.start_new_match(match)
            player.start_thinking(match)

    def _switch_to_pondering(self, player, match):
        """Switches a player state to pondering a position"""

        if isinstance(player, Engine):
            strength = player.get_playing_strength()

            if strength.allows_pondering:
                move = self._ponder_cache.fetch(match)
                player.start_new_match(match)
                player.start_pondering(match, move)

    def _on_move_received(self, player, values):
        """Handles the reception of an engine move"""

        if not self._request_lock.locked():
            with self._request_lock:
                if player == self._active_player:
                    self._active_player = None
                    self._emit_player_move(player, values)

            self._logger.debug('Move received from engine')

    def _on_info_received(self, player, values):
        """Handles the reception of an engine report"""

        self._emit_player_report(player, values)
        self._logger.debug('Information received from engine')

    def _emit_player_move(self, player, values):
        """Emits a move received from the given player"""

        match = player.get_current_match()
        game = match.get_game()
        move = game.to_move(values['move'])

        if values['ponder'] is not None:
            value = game.to_move(values['ponder'])
            self._ponder_cache.store(match, move, value)

        GLib.idle_add(self.move_received.emit, player, move)

    def _emit_player_report(self, player, values):
        """Emits a report received from the given player"""

        GLib.idle_add(self.info_received.emit, player, values)
