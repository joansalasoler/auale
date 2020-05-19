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
import re
import sys

from threading import Event
from threading import Thread
from gi.repository import GObject

from .rules import parser


class Client(Thread, GObject.GObject):
    """UCI protocol client implementation."""

    __response_timeout = 8.0

    __gtype_name__ = 'UCIClient'

    __response_signal = (
        GObject.SignalFlags.RUN_FIRST,
        GObject.TYPE_NONE, (
          GObject.TYPE_PYOBJECT,
        )
    )

    __timeout_signal = (
        GObject.SignalFlags.RUN_FIRST,
        GObject.TYPE_NONE, (
          GObject.TYPE_STRING,
        )
    )

    __failure_signal = (
        GObject.SignalFlags.RUN_LAST,
        GObject.TYPE_NONE, (
          GObject.TYPE_STRING,
        )
    )

    __termination_signal = (
        GObject.SignalFlags.RUN_LAST,
        GObject.TYPE_NONE, ()
    )

    __gsignals__ = {
        'id-received': __response_signal,
        'info-received': __response_signal,
        'option-received': __response_signal,
        'bestmove-received': __response_signal,
        'response-timeout': __timeout_signal,
        'termination': __termination_signal,
        'failure': __failure_signal
    }

    def __init__(self, filein, fileout):
        GObject.GObject.__init__(self)
        Thread.__init__(self)

        self._fileout = fileout
        self._filein = filein

        self._logger = logging.getLogger('uci')
        self._is_waiting = Event()
        self._is_terminated = Event()
        self._is_running = Event()
        self._is_ready = Event()

        self._match = None
        self._search_depth = 10
        self._search_timeout = 1000

    def is_searching(self):
        """Checks if the engine is thinking or pondering"""

        running = self._is_running.is_set()
        waiting = self._is_waiting.is_set()

        return running and not waiting

    def get_current_match(self):
        """Last match the engine was asked to search on"""

        return self._match

    def set_search_depth(self, depth):
        """Sets how many plies the player may search"""

        self._search_depth = depth

    def set_search_timeout(self, milliseconds):
        """Sets how many milliseconds a search may take"""

        self._search_timeout = milliseconds

    def start(self):
        """Starts the client in UCI mode"""

        super().start()

        if not self._is_running.is_set():
            self._is_running.clear()
            self._send_command('uci')
            self._wait_for('uci', self._is_running)

        if not self._is_running.is_set():
            self.emit('failure', 'Engine is not responding')

    def start_new_match(self, match=None):
        """Notify the player a new match will start"""

        if self._is_waiting.is_set():
            if match != self._match or not self._match:
                self._send_command('ucinewgame')
                self._synchronize()

    def start_thinking(self, match):
        """Asks the player to start thinking on the given match"""

        if self._is_waiting.is_set():
            self._match = match
            self._is_waiting.clear()
            search_args = self._get_search_arguments()
            position_args = self._get_position_arguments(match)
            self._send_command(f'position { position_args }')
            self._send_command(f'go { search_args }')

    def start_pondering(self, match):
        """Asks the player to start pondering on the given match"""

        if self._is_waiting.is_set():
            self._match = match
            self._is_waiting.clear()
            position_args = self._get_position_arguments(match)
            self._send_command(f'position { position_args }')
            self._send_command('go ponder')

    def stop_thinking(self):
        """Asks the player to stop thinking"""

        if not self._is_waiting.is_set():
            self._send_command('stop')
            self._wait_for('stop', self._is_waiting)

    def quit(self):
        """Asks the player to quit"""

        if not self._is_terminated.is_set():
            self._send_command('quit')
            self._wait_for('quit', self._is_terminated)

    def _eval_uciok(self, params):
        """Evaluates a uciok response"""

        if not self._is_running.is_set():
            self._is_running.set()
            self._is_waiting.set()

    def _eval_readyok(self, params):
        """Evaluates a readyok response"""

        if not self._is_ready.is_set():
            self._is_ready.set()

    def _eval_info(self, params):
        """Evaluates a info response"""

        if self._is_running.is_set():
            self.emit('info-received', params)

    def _eval_id(self, params):
        """Evaluates an id response"""

        if not self._is_running.is_set():
            self.emit('id-received', params)

    def _eval_option(self, params):
        """Evaluates an option response"""

        if not self._is_running.is_set():
            self.emit('option-received', params)

    def _eval_bestmove(self, params):
        """Evaluates a bestmove response"""

        if not self._is_waiting.is_set():
            self.emit('bestmove-received', params)
            self._is_waiting.set()

    def _get_search_arguments(self):
        """Builds the arguments for the go command"""

        options = []

        if self._search_depth is not None:
            options.append('depth')
            options.append(self._search_depth)

        if self._search_timeout is not None:
            options.append('movetime')
            options.append(self._search_timeout)

        if not options:
            options.append('infinite')

        return self._to_string(options)

    def _get_position_arguments(self, match):
        """Builds the arguments for the position command"""

        options = []

        index = match.get_capture_index()
        board = self._get_board_argument(match, index)

        options.append(board)

        if index < match.get_current_index():
            moves = self._get_moves_argument(match, index)
            options.append(moves)

        return self._to_string(options)

    def _get_board_argument(self, match, index):
        """Obtains a board notation for the given match index"""

        options = 'startpos'
        position = match.get_positions()[index]
        game = match.get_game()

        if position[0] != game.get_initial_board():
            options = game.to_board_notation(*position)
            options = f'fen { options }'

        return options

    def _get_moves_argument(self, match, index):
        """Obtains a moves notation for the given match index"""

        options = None
        length = 1 + match.get_current_index()
        moves = match.get_moves()[index:length]

        if moves:
            game = match.get_game()
            options = game.to_moves_notation(moves)
            options = f'moves { options }'

        return options

    def _to_string(self, options):
        """Converts an iterable into a string"""

        parts = (o for o in options if o is not None)
        string = ' '.join((str(o) for o in parts))

        return string

    def _synchronize(self):
        """Synchronize player responses"""

        self._is_ready.clear()
        self._send_command('isready')
        self._wait_for('isready', self._is_ready)

    def _wait_for(self, order, event):
        """Waits for an event to be set"""

        if not self._is_terminated.is_set():
            if not event.wait(self.__response_timeout):
                self._logger.warning('Response timeout')
                self.emit('response-timeout', order)

    def _eval_response(self, response):
        """Evaluates a received response"""

        try:
            params = parser.parse(response)
            method_name = f'_eval_{ params["order"] }'
            callback = getattr(self, method_name)
            callback(params)
        except BaseException as e:
            self._logger.warning('Unknown UCI response')

    def _read_response(self):
        """Reads a response from the input file"""

        try:
            response = self._filein.readline().strip()
            self._logger.debug(f'< { response }')
        except BrokenPipeError:
            self.emit('failure', 'Broken pipe')

        return response

    def _send_command(self, command):
        """Writes a command to the output file"""

        try:
            self._logger.debug(f'> { command }')
            self._fileout.write(f'{ command }\n')
            self._fileout.flush()
        except BrokenPipeError:
            self.emit('failure', 'Broken pipe')

    def run(self):
        """Evaluates responses while the input file is open"""

        try:
            while response := self._read_response():
                self._eval_response(response)
        finally:
            self._is_running.clear()
            self._is_terminated.set()
            self.emit('termination')
