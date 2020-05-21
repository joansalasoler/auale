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

from threading import Lock
from gi.repository import GLib
from gi.repository import GObject
from uci import Engine
from .cache import PonderCache


class GameLoop(GObject.GObject):
    """Represents the game loop"""

    __move_delay = 1.6

    __gtype_name__ = 'GameLoop'

    __gsignals__ = {
        'move-received': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE, (
                GObject.TYPE_INT,
            )
        ),

        'info-received': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE, (
                GObject.TYPE_STRING,
            )
        )
    }

    def __init__(self):
        GObject.GObject.__init__(self)

        self._active_player = None
        self._current_player = None
        self._previous_player = None
        self._request_lock = Lock()
        self._ponder_cache = PonderCache(256)

    def request_move(self, player, match):
        """Requests a player to make a move"""

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

    def abort_move(self):
        """Aborts any ongoing move requests"""

        with self._request_lock:
            self._active_player = None
            self._switch_to_waiting(self._current_player)
            self._switch_to_waiting(self._previous_player)

    def _is_entering_player(self, player):
        """Checks if its a new player entering the match"""

        return player != self._current_player and \
               player != self._previous_player

    def _is_substitute_player(self, player):
        """Checks if the player substitutes a previous one"""

        return player != self._previous_player and \
               self._previous_player != self._current_player

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

                    match = player.get_current_match()
                    game = match.get_game()
                    move = game.to_move(values['move'])

                    GLib.idle_add(self.emit, 'move-received', move)

                    if values['ponder'] is not None:
                        value = game.to_move(values['ponder'])
                        self._ponder_cache.store(match, move, value)

    def _on_info_received(self, player, values):
        """Handles the reception of an engine report"""

        pass # TODO: Not implemented yet
