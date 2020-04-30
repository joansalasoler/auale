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

import re

from game import Match


class UCIClient():
    """
    Universal Chess Interface Protocol Client. This class provides methods to
    interact with an external engine process throught the UCI protocol.
    """

    __STOPPED_STATE = 0
    __WAITING_STATE = 1
    __THINKING_STATE = 2
    __PONDERING_STATE = 3

    __PATTERN = '^[ \\t]*(\\S+)(?:[ \\t]+(.*))?$'

    def __init__(self, game, service):
        """Initializes a new client object"""

        self._game = game
        self._input = service.stdout
        self._output = service.stdin

        self._match = Match(game)
        self._board = self._match.get_board()
        self._pattern = re.compile(UCIClient.__PATTERN)

        self._name = "Unknown"
        self._author = "Unknown"
        self._best_move = game.NULL_MOVE
        self._ponder_move = game.NULL_MOVE
        self._infinite = False
        self._debug = False
        self._ready = True
        self._uciok = True
        self._state = UCIClient.__WAITING_STATE

    def get_board(self):
        """Returns the current board position"""

        return self._match.get_board()

    def get_start_board(self):
        """Returns the current game start position"""

        return self._board

    def get_best_move(self):
        """Returns the last received best move"""

        return self._best_move

    def get_ponder_move(self):
        """Returns the last received ponder move"""

        return self._ponder_move

    def get_name(self):
        """Returns the current engine name"""

        return self._name

    def get_author(self):
        """Returns the current engine author"""

        return self._author

    def is_debug_on(self):
        """Returns the current engine debug mode"""

        return self._debug

    def has_time_limit(self):
        """True if the engine is not thinking in infinite mode"""

        return (self._infinite == False)

    def is_thinking(self):
        """True if the engine is in a thinking state"""

        return (self._state == UCIClient.__THINKING_STATE)

    def is_pondering(self):
        """True if the engine is in a pondering state"""

        return (self._state == UCIClient.__PONDERING_STATE)

    def is_running(self):
        """True if the engine process is running"""

        return (self._state != UCIClient.__STOPPED_STATE)

    def is_ready(self):
        """True if the engine is ready to receive new commands"""

        if self._state == UCIClient.__STOPPED_STATE:
            return False

        return self._ready

    def is_uci_ready(self):
        """True if the engine is ready to accept UCI commands"""

        if self._state == UCIClient.__STOPPED_STATE:
            return False

        return self._uciok

    def _parse_uci(self, params):
        """Parses a 'uci' command"""

        self._uciok = False

    def _parse_debug(self, params):
        """Parses a 'debug' command"""

        switch = True
        value = True

        if params is not None:
            for token in params.split():
                if 'on' == token:
                    switch = False
                    value = True
                elif 'off' == token:
                    switch = False
                    value = False

        if switch == True:
            self._debug = not self._debug
        else:
            self._debug = value

    def _parse_isready(self, params):
        """Parses an 'isready' command"""

        self._ready = False

    def _parse_setoption(self, params):
        """Not implemented"""
        pass

    def _parse_register(self, params):
        """Not implemented"""
        pass

    def _parse_ucinewgame(self, params):
        """Parses an 'ucinewgame' command"""

        if self._state != UCIClient.__WAITING_STATE:
            raise Exception("The engine is not waiting for commands")

    def _parse_position(self, params):
        """Parses a 'position' command"""

        position = None
        notation = None
        moves = None

        board = None
        turn = self._game.SOUTH

        # This command requieres at least one parameter

        if params is None:
            raise ValueError("No parameters were provided")

        # Parse the provided parameters

        tokens = params.split()

        while len(tokens) > 0:
            token = tokens.pop(0)

            if 'startpos' == token:
                position = 'startpos'
            elif 'fen' == token:
                if len(tokens) > 0:
                    position = tokens.pop(0)
            elif 'moves' == token:
                if len(tokens) > 0:
                    notation = tokens.pop(0)

        # Obtain the board for the received position

        if position is None:
            raise ValueError("No position was provided")

        if 'startpos' == position:
            board = self._game.get_initial_board()
            turn = self._game.SOUTH
        else:
            (board, turn) = self._game.to_position(position)

        # Obtain the moves for the received notation

        if notation is not None:
            moves = self._game.to_moves(notation)

        # Change the game state if moves are legal

        match = Match(self._game)
        match.set_position(board, turn)

        if moves is not None:
            for move in moves:
                match.add_move(move)

        self._board = board
        self._match = match

    def _parse_go(self, params):
        """Parses a 'go' command"""

        infinite = False
        ponder = False

        # Ensure the engine is in a consistent state

        if self._state != UCIClient.__WAITING_STATE:
            raise Exception("The engine is already thinking")

        # Parse the provided parameters

        if params is not None:
            for token in params.split():
                if 'infinite' == token:
                    infinite = True
                elif 'ponder' == token:
                    ponder = True
                    infinite = True

        # Change the engine state accordingly

        self._state = (ponder == True) \
            and UCIClient.__PONDERING_STATE \
            or UCIClient.__THINKING_STATE
        self._infinite = infinite

    def _parse_stop(self, params):
        """Parses an 'stop' command"""

        if self._state != UCIClient.__THINKING_STATE \
        and self._state != UCIClient.__PONDERING_STATE:
            raise Exception("The engine is not thinking")

        self._infinite = False

    def _parse_ponderhit(self, params):
        """Parses a 'quit' command"""

        if self._state != UCIClient.__PONDERING_STATE:
            raise Exception("The engine is not pondering")

        self._state = UCIClient.__THINKING_STATE

    def _parse_quit(self, params):
        """Parses a 'quit' command"""

        self._state = UCIClient.__STOPPED_STATE

    def _parse_id(self, params):
        """Parses an 'id' command"""

        if params is None:
            raise ValueError("No parameters were provided")

        stop = 'name|value$'
        tokens = params.split()

        while len(tokens) > 0:
            token = tokens.pop(0)

            if 'name' == token:
                string = self._string(tokens, stop)
                self._name = string
            elif 'author' == token:
                string = self._string(tokens, stop)
                self._author = string

    def _parse_uciok(self, params):
        """Parses an 'uciok' command"""

        self._uciok = True

    def _parse_readyok(self, params):
        """Parses an 'readyok' command"""

        self._ready = True

    def _parse_bestmove(self, params):
        """Parses a 'bestmove' command"""

        best_move = None
        ponder_move = None

        # Change the state, even if moves are not valid

        self._state = UCIClient.__WAITING_STATE
        self._infinite = False

        # This method requieres at least a parameter

        if params is None:
            raise ValueError("No parameters were provided")

        # Parse the provided parameters

        tokens = params.split()

        if len(tokens) > 0:
            best_move = tokens.pop(0)

        while len(tokens) > 0:
            token = tokens.pop(0)
            if 'ponder' == token and len(tokens) > 0:
                ponder_move = tokens.pop(0)

        # Check if a null move was received

        if '0000' == best_move:
            self._best_move = self._game.NULL_MOVE
            self._ponder_move = self._game.NULL_MOVE
            return

        # Validate the provided move notations

        if best_move is None or len(best_move) != 1:
            raise Exception("Not a valid move notation")

        if ponder_move is not None and len(ponder_move) != 1:
            raise Exception("Not a valid move notation")

        # Validate the received moves legality

        ponder = self._game.NULL_MOVE
        best = self._game.to_move(best_move)

        board = self._match.get_board()
        turn = self._match.get_turn()

        if best not in self._game.xlegal_moves(board, turn):
            raise Exception("Best move is not legal")

        if ponder_move is not None:
            board = self._game.compute_board(board, best)
            ponder = self._game.to_move(ponder_move)

            if ponder not in self._game.xlegal_moves(board, -turn):
                raise Exception("Ponder move is not legal")

        # Save the received moves

        self._best_move = best
        self._ponder_move = ponder

    def _parse_copyprotection(self, params):
        """Not implemented"""
        pass

    def _parse_registration(self, params):
        """Not implemented"""
        pass

    def _parse_info(self, params):
        """Not implemented"""
        pass

    def _parse_option(self, params):
        """Not implemented"""
        pass

    def _string(self, tokens, stop):
        """
        Builds a string from a list of tokens, consuming tokens from the list
        until the stop pattern is found or all tokens are consumed
        """

        string = ''
        words = []

        while len(tokens) > 0:
            if re.match(stop, tokens[0]) is not None:
                break
            token = tokens.pop(0)
            words.append(token)

        if len(words) > 0:
            string = ' '.join(words)

        return string

    def _evaluate_input(self, message):
        """Evaluates an engine-to-client command"""

        # Parse the input message

        match = self._pattern.match(message)

        if match is None:
            raise ValueError("Syntax error: %s" % message)

        # Parse the received command

        command = match.group(1)
        params = match.group(2)

        if 'id' == command:
            self._parse_id(params)
        elif 'uciok' == command:
            self._parse_uciok(params)
        elif 'readyok' == command:
            self._parse_readyok(params)
        elif 'bestmove' == command:
            self._parse_bestmove(params)
        elif 'copyprotection' == command:
            self._parse_copyprotection(params)
        elif 'registration' == command:
            self._parse_registration(params)
        elif 'info' == command:
            self._parse_info(params)
        elif 'option' == command:
            self._parse_option(params)
        else:
            raise ValueError(
                "Unknown engine command: %s" % command)

    def _evaluate_output(self, message):
        """Evaluates a client-to-engine command"""

        # Ensure that the engine is running

        if self._state == UCIClient.__STOPPED_STATE:
            raise Exception("The engine is not running")

        # Parse the output message

        match = self._pattern.match(message)

        if match is None:
            raise ValueError("Syntax error: %s" % message)

        # Parse the received command

        command = match.group(1)
        params = match.group(2)

        if 'uci' == command:
            self._parse_uci(params)
        elif 'debug' == command:
            self._parse_debug(params)
        elif 'isready' == command:
            self._parse_isready(params)
        elif 'setoption' == command:
            self._parse_setoption(params)
        elif 'register' == command:
            self._parse_register(params)
        elif 'ucinewgame' == command:
            self._parse_ucinewgame(params)
        elif 'position' == command:
            self._parse_position(params)
        elif 'go' == command:
            self._parse_go(params)
        elif 'stop' == command:
            self._parse_stop(params)
        elif 'ponderhit' == command:
            self._parsePonderHit(params)
        elif 'quit' == command:
            self._parse_quit(params)
        else:
            raise ValueError(
                "Unknown client command: %s" % command)

    def send(self, message):
        """Evaluates and sends a single client-to-engine command"""

        self._evaluate_output(message)
        self._output.write('%s\n' % message)
        self._output.flush()

        if self._debug:
            print("> %s" % message)

    def receive(self):
        """Receives and evaluates the next engine-to-client command"""

        if self._input.closed:
            raise Exception("Engine is not responding")

        message = self._input.readline()

        if message is None or message == '':
            raise Exception("Engine is not responding")

        message = message.strip()

        if message != '':
            self._evaluate_input(message)

        if self._debug:
            print("< %s" % message)

        return message
