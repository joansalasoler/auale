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

import time
import threading

from gi.repository import GLib
from gi.repository import GObject
from uci import UCIPlayer


class GameLoop(threading.Thread, GObject.GObject):
    """Represents the game loop"""

    __gtype_name__ = 'GameLoop'

    __gsignals__ = {

        'state-changed': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE, ()
        ),

        'move-received': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE,
            (GObject.TYPE_INT,)
        )
    }

    MOVE_DELAY = 1.6

    def __init__(self):
        """Initializes this game loop"""

        GObject.GObject.__init__(self)
        threading.Thread.__init__(self)

        self._match = None
        self._player = None
        self._is_running = False
        self._lock = threading.Lock()
        self._switch = threading.Condition(self._lock)
        self._aborted = threading.Event()
        self._computed = threading.Event()
        self._computed.set()

    def is_thinking(self):
        """Tells if the engine is thinking"""

        return not self._computed.is_set()

    def request_move(self, player):
        """Requests a move to the current player"""

        with self._switch:
            self._player = player
            self._switch.notify_all()

    def run(self):
        """Switches turns till this thread is stopped"""

        with self._switch:
            self._is_running = True

            while self._is_running:
                self._switch.wait()
                if self._is_running:
                    self._request_action()

    def abort(self):
        """Aborts any running move computation"""

        self._aborted.set()

        try:
            if self._player is not None:
                while not self._computed.is_set():
                    self._player.stop()
                    self._computed.wait(0.2)
        except BaseException:
            pass  # Not computing

        self._computed.wait()
        self._aborted.clear()

    def stop(self):
        """Stops this game loop thread"""

        self.abort()

        with self._switch:
            self._is_running = False
            self._switch.notify_all()

    def _request_action(self):
        """Request a move to the player"""

        if self._player is None:
            GLib.idle_add(self.emit, 'state-changed')
            return

        try:
            self._computed.clear()
            GLib.idle_add(self.emit, 'state-changed')
            self._compute_move()
            self._computed.set()
        except BaseException:
            self._computed.set()
            GLib.idle_add(self.emit, 'state-changed')

    def _compute_move(self):
        """Requests a move to the player"""

        start_time = time.time()

        # Compute a move and set the player to ponder

        if not self._aborted.is_set():
            move = self._player.retrieve_move()

        if not self._aborted.is_set():
            if self._player.get_strength() > UCIPlayer.Strength.MEDIUM:
                self._player.start_pondering()

        # Wait before emiting a signal

        end_time = time.time()
        delay = end_time - start_time

        if delay < GameLoop.MOVE_DELAY:
            wait_time = GameLoop.MOVE_DELAY - delay
            self._aborted.wait(wait_time)

        # Emit a move-received signal

        if not self._aborted.is_set():
            GLib.idle_add(self.emit, 'move-received', move)
