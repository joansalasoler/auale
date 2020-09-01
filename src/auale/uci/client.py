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
import math
import re
import sys

from threading import Event
from threading import Thread
from gi.repository import GObject

from .rules import parser


class Client(GObject.GObject, Thread):
    """UCI protocol client implementation."""

    __gtype_name__ = 'Client'
    __response_timeout = 8.0

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
        self._ponder_move = None

    @GObject.Signal
    def id_received(self, params: object):
        """Emitted when a player identified itself"""

    @GObject.Signal
    def info_received(self, params: object):
        """Emitted when a player report is received"""

    @GObject.Signal
    def option_received(self, params: object):
        """Emitted when a configuration option is received"""

    @GObject.Signal
    def move_received(self, params: object):
        """Emitted when a best move report is received"""

    @GObject.Signal
    def response_timeout(self, order: str):
        """Emitted when waiting for a response times out"""

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST)
    def failure(self, reason: str):
        """Emitted on client failures"""

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST)
    def termination(self):
        """Emitted when the client is stopped"""

    def is_searching(self):
        """Checks if the engine is thinking or pondering"""

        running = self._is_running.is_set()
        waiting = self._is_waiting.is_set()

        return running and not waiting

    def get_current_match(self):
        """Last match the engine was asked to search on"""

        return self._match

    def get_move_number(self):
        """Move number of the match we are searching on"""

        index = 1 + self._match.get_current_index()
        number = math.ceil(index / 2)

        return number

    def get_ponder_move(self):
        """Notation of the move the player was pondering on"""

        move = self._ponder_move
        game = self._match.get_game()
        notation = move and game.to_move_notation(move)

        return notation

    def set_search_depth(self, depth):
        """Sets how many plies the player may search"""

        self._search_depth = depth

    def set_search_timeout(self, milliseconds):
        """Sets how many milliseconds a search may take"""

        self._search_timeout = milliseconds

    def set_option(self, name, value=None):
        """Sends a configuration parameter to the engine"""

        param = '' if value is None else f' value { value }'
        command = f'setoption name { name }{ param }'
        self._send_command(command)

    def start(self):
        """Starts the client in UCI mode"""

        super().start()

        if not self._is_running.is_set():
            self._is_running.clear()
            self._send_command('uci')
            self._wait_for('uci', self._is_running)

        if not self._is_running.is_set():
            self.failure.emit('Engine is not responding')

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
            self._ponder_move = None
            search_args = self._get_search_arguments()
            position_args = self._get_position_arguments(match)
            self._send_command(f'position { position_args }')
            self._send_command(f'go { search_args }')

    def start_pondering(self, match, move=None):
        """Asks the player to start pondering on the given match"""

        if self._is_waiting.is_set():
            self._match = match
            self._is_waiting.clear()
            self._ponder_move = move
            position_args = self._get_position_arguments(match, move)
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
            params['number'] = self.get_move_number()
            params['ponder'] = self.get_ponder_move()
            self.info_received.emit(params)

    def _eval_id(self, params):
        """Evaluates an id response"""

        if not self._is_running.is_set():
            self.id_received.emit(params)

    def _eval_option(self, params):
        """Evaluates an option response"""

        if not self._is_running.is_set():
            self.option_received.emit(params)

    def _eval_bestmove(self, params):
        """Evaluates a bestmove response"""

        if not self._is_waiting.is_set():
            self.move_received.emit(params)
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

    def _get_board_argument(self, match, index):
        """Obtains a board notation for the given match index"""

        options = 'startpos'
        position = match.get_positions()[index]
        game = match.get_game()

        if position[0] != game.get_initial_board():
            options = game.to_board_notation(*position)
            options = f'fen { options }'

        return options

    def _get_position_arguments(self, match, move=None):
        """Builds the arguments for the position command"""

        options = []

        index = match.get_capture_index()
        board = self._get_board_argument(match, index)
        moves = self._get_moves_argument(match, index, move)

        options.append(board)
        options.append(moves)

        return self._to_string(options)

    def _get_moves_argument(self, match, index, move=None):
        """Obtains a moves notation for the given match index"""

        options = None

        length = match.get_current_index()
        moves = match.get_moves()[index:length]

        if isinstance(move, int):
            moves = moves + (move,)

        if moves and len(moves) > 0:
            game = match.get_game()
            notation = game.to_moves_notation(moves)
            options = f'moves { notation }'

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
                self.response_timeout.emit(order)

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
            self._logger.debug(f'{ self } < { response }')
        except BrokenPipeError:
            if not self._is_terminated.is_set():
                self.failure.emit('Broken pipe')

        return response

    def _send_command(self, command):
        """Writes a command to the output file"""

        try:
            self._logger.debug(f'{ self } > { command }')
            self._fileout.write(f'{ command }\n')
            self._fileout.flush()
        except BrokenPipeError:
            if not self._is_terminated.is_set():
                self.failure.emit('Broken pipe')

    def run(self):
        """Evaluates responses while the input file is open"""

        try:
            while response := self._read_response():
                self._eval_response(response)
        finally:
            self._is_running.clear()
            self._is_terminated.set()
            self.termination.emit()
