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

import random
import struct

from game import Match
from game import Oware
from .constants import COEFFICIENTS


class OpeningBook(object):
    """Opening book implementation"""

    def __init__(self, path):
        self._header = None
        self._scores = None
        self._load_opening_book(path)

    def pick_best_move(self, match, error=10):
        """Choose a best move from the book"""

        moves = self.find_best_moves(match, error)
        choice = random.choice(moves) if moves else None

        return choice

    def find_best_moves(self, match, error=10):
        """Obtain the best moves from the book"""

        moves = list()
        code = self._compute_hash_code(match)

        if code not in self._scores:
            return moves

        game = match.get_game()
        turn = match.get_turn()

        scores = self._scores[code]
        offset = 0 if turn == game.SOUTH else 6
        min_score = max(scores) - error

        for index, move_score in enumerate(scores):
            if move_score >= min_score:
                moves.append(offset + index)

        return moves

    def _load_opening_book(self, path):
        """Loads an opening book from a file"""

        with open(path, 'r+b') as file:
            self._header = self._read_header(file)
            self._scores = self._read_scores(file)

    def _read_header(self, file):
        """Reads the header fields from an open file"""

        header = dict()
        signature = file.readline()

        while field := file.readline():
            if field == b'\x00\n': break
            values = field.decode('utf-8').split(':', 1)
            header.setdefault(*values)

        return header

    def _read_scores(self, file):
        """Reads position scores from an open file"""

        scores = dict()

        while entry := file.read(20):
            code, *values = struct.unpack('>q6h', entry)
            scores.setdefault(code, values)

        return scores

    def _compute_hash_code(self, match):
        """Hash code for the current match position"""

        game = match.get_game()
        turn = match.get_turn()
        board = match.get_board()

        code = 0x80000000000 if turn == game.SOUTH else 0x00
        seeds = board[13]

        for house in range(12, -1, -1):
            if seeds >= 48: break
            code += COEFFICIENTS[seeds][house]
            seeds += board[house]

        return code
