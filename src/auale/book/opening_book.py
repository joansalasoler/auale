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

import math
import random
import struct

from game import Match
from game import Oware
from uci import Strength

from .constants import COEFFICIENTS


class OpeningBook(object):
    """Opening book implementation"""

    __MARGIN = 42

    def __init__(self, path):
        self._scores = []
        self._header = dict()
        self._min_score = self.__MARGIN
        self._load_opening_book(path)

    def set_strength(self, strength):
        """Sets the playing strength of the book"""

        margin = self.__MARGIN
        factor = 1 - strength.strength_factor
        self._min_score = margin + (.25 * margin * factor) ** 2

    def pick_best_move(self, match):
        """Choose a best move from the book"""

        moves = self.find_best_moves(match)
        choice = random.choice(moves) if moves else None

        return choice

    def find_best_moves(self, match):
        """Obtain the best moves from the book"""

        moves = list()
        game = match.get_game()
        turn = match.get_turn()
        scores = self._get_move_scores(match)

        max_score = max(scores) if scores else -math.inf
        min_score = max(max_score - self._min_score, -self._min_score)
        offset = 0 if turn == game.SOUTH else 6

        for move, score in enumerate(scores, offset):
            if score >= min_score or score >= max_score:
                moves.append(move)

        return moves

    def _get_move_scores(self, match):
        """Scores for the given match position"""

        code = self._compute_hash_code(match)
        scores = self._scores.get(code, [])

        return scores

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
