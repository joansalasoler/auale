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

import os
import pickle
import re


class Oware(object):
    """Oware Abapa game logic"""

    SOUTH = 1
    NORTH = -1
    DRAW = 0

    __base = os.path.dirname(__file__)
    __path = os.path.join(__base, 'oware.pkl')
    __file = open(__path, 'rb')

    _RULESET = "Oware Abapa"
    _EMPTY_ROW = (0, 0, 0, 0, 0, 0)
    _EMPTY_ROWL = [0, 0, 0, 0, 0, 0]
    _SEED_DRILL = pickle.load(__file)
    _HARVESTER = pickle.load(__file)
    _REAPER = pickle.load(__file)

    __file.close()

    @staticmethod
    def get_ruleset_name():
        """Ruleset name for this game"""

        return Oware._RULESET

    @staticmethod
    def get_initial_board():
        """Start board of the game as a tuple of integers"""

        return (4,) * 12 + (0, 0)

    @staticmethod
    def get_final_board(board):
        """
        Endgame position for the given board

        If the game ended because a player captured more than 24 seeds
        or each player captured 24 seeds, the final position is equal to
        the provided position. Otherwise, if the game ended because of a
        move repetition or a lack of legal moves, each player gathers the
        remaining seeds on their side of the board.
        """

        if board[12] > 24 or board[13] > 24:
            return board

        if board[12] == board[13] == 24:
            return board

        south = sum(board[0:6], board[12])
        north = sum(board[6:12], board[13])

        return (0,) * 12 + (south, north)

    @staticmethod
    def get_winner(board, turn):
        """
        Checks if a player has won the match and returns Oware.SOUTH,
        Oware.NORTH or Oware.DRAW according to the winner. If the match
        is ongoing this method returns Oware.DRAW.
        """

        if board[12] > 24:
            return Oware.SOUTH
        elif board[13] > 24:
            return Oware.NORTH

        if not Oware.has_legal_moves(board, turn):
            cboard = Oware.get_final_board(board)
            if cboard[12] > cboard[13]:
                return Oware.SOUTH
            elif cboard[12] < cboard[13]:
                return Oware.NORTH
            else:
                return Oware.DRAW

        return Oware.DRAW

    @staticmethod
    def get_sowings(board, move):
        """Get the sowed houses in their sower order"""

        return Oware._SEED_DRILL[move][:board[move]]

    @staticmethod
    def is_capture(board, move):
        """Checks if a move may perform at capture"""

        if board[move] in Oware._REAPER[move]:
            (last, positions) = Oware._REAPER[move][board[move]]

            if board[last] > 2:
                return False

            if (board[last] == 0) ^ (board[move] < 12) \
                    or (11 < board[move] < 23 and board[last] == 1):
                if move < 6:
                    if board[6:12] in positions:
                        return False
                else:
                    if board[0:6] in positions:
                        return False
                return True

        return False

    @staticmethod
    def is_endgame(board, turn):
        """Checks if the position is an endgame position"""

        if board[12] > 24 or board[13] > 24:
            return True

        if Oware.has_legal_moves(board, turn):
            return False

        return True

    @staticmethod
    def has_legal_moves(board, turn):
        """Checks if a player has at least one legal move"""

        if turn == Oware.SOUTH:
            if board[0:6] != Oware._EMPTY_ROW:
                if board[6:12] != Oware._EMPTY_ROW:
                    return True

                for house in (5, 4, 3, 2, 1, 0):
                    if 0 < board[house] > 5 - house:
                        return True
        else:
            if board[6:12] != Oware._EMPTY_ROW:
                if board[0:6] != Oware._EMPTY_ROW:
                    return True

                for house in (11, 10, 9, 8, 7, 6):
                    if 0 < board[house] > 11 - house:
                        return True

        return False

    @staticmethod
    def make_move(board, move):
        """
        Makes a move on the board an returns the result. Grand Slam moves
        are legal but the player to move does not capture any seeds.
        """

        new_board = list(board)
        new_board[move] = 0

        # Sow

        for house in Oware._SEED_DRILL[move][:board[move]]:
            new_board[house] += 1

        # Gather

        if 4 > new_board[house] > 1:
            if move < 6 and house > 5:
                board_copy = new_board[:]
                for house in Oware._HARVESTER[house]:
                    if not 4 > board_copy[house] > 1:
                        break
                    board_copy[12] += board_copy[house]
                    board_copy[house] = 0
                if board_copy[6:12] != Oware._EMPTY_ROWL:
                    return tuple(board_copy)
            elif move > 5 and house < 6:
                board_copy = new_board[:]
                for house in Oware._HARVESTER[house]:
                    if not 4 > board_copy[house] > 1:
                        break
                    board_copy[13] += board_copy[house]
                    board_copy[house] = 0
                if board_copy[0:6] != Oware._EMPTY_ROWL:
                    return tuple(board_copy)

        return tuple(new_board)

    @staticmethod
    def get_legal_moves(board, turn):
        """
        Legal moves that a player can perform on a board. Illegal moves are
        those which don't reach the opponent's side when it's empty."""

        south = Oware.get_legal_moves_south
        north = Oware.get_legal_moves_north
        is_south = turn == Oware.SOUTH

        yield from south(board) if is_south else north(board)

    @staticmethod
    def get_legal_moves_south(board):
        """Get legal moves for south"""

        for move in (5, 4, 3, 2, 1, 0):
            if 0 < board[move] > 5 - move \
            and Oware.is_capture(board, move):
                yield move

        if board[6:12] != Oware._EMPTY_ROW:
            for move in (0, 1, 2, 3, 4, 5):
                if 0 < board[move] < 3 \
                and not Oware.is_capture(board, move):
                    yield move

            for move in (0, 1, 2, 3, 4, 5):
                if board[move] > 2 \
                and not Oware.is_capture(board, move):
                    yield move
        else:
            for move in (0, 1, 2, 3, 4, 5):
                if 0 < board[move] > 5 - move \
                and not Oware.is_capture(board, move):
                    yield move

    @staticmethod
    def get_legal_moves_north(board):
        """Get legal moves for north"""

        for move in (11, 10, 9, 8, 7, 6):
            if 0 < board[move] > 11 - move \
            and Oware.is_capture(board, move):
                yield move

        if board[0:6] != Oware._EMPTY_ROW:
            for move in (6, 7, 8, 9, 10, 11):
                if 0 < board[move] < 3 \
                and not Oware.is_capture(board, move):
                    yield move

            for move in (6, 7, 8, 9, 10, 11):
                if board[move] > 2 \
                and not Oware.is_capture(board, move):
                    yield move
        else:
            for move in (6, 7, 8, 9, 10, 11):
                if 0 < board[move] > 11 - move \
                and not Oware.is_capture(board, move):
                    yield move

    @staticmethod
    def to_board_notation(board, turn):
        """Converts a board tuple to its notation"""

        notation = []

        for house in board:
            notation.append(str(house))

        notation.append(turn == Oware.SOUTH and 'S' or 'N')

        return '-'.join(notation)

    @staticmethod
    def to_move_notation(move):
        """Converts a move identifier to its notation"""

        if isinstance(move, int):
            if 0 <= move <= 5:
                return chr(65 + move)
            elif 6 <= move <= 11:
                return chr(91 + move)

        raise ValueError("Not a valid move identifier")

    @staticmethod
    def to_moves_notation(moves):
        """Converts a move tuple to its notation"""

        notation = []

        for move in moves:
            n = Oware.to_move_notation(move)
            notation.append(n)

        return ''.join(notation)

    @staticmethod
    def to_move(notation):
        """Converts a notation to a move identifier"""

        if isinstance(notation, str) and len(notation) == 1:
            if 65 <= ord(notation) <= 70:
                return ord(notation) - 65
            elif 97 <= ord(notation) <= 102:
                return ord(notation) - 91

        raise ValueError("Not a valid move notation")

    @staticmethod
    def to_moves(notation):
        """Converts a moves notation to a move identifiers tuple"""

        pattern = '([A-F]([a-f][A-F])*[a-f]?)|([a-f]([A-F][a-f])*[A-F]?)$'

        if re.match(pattern, notation) is None:
            raise ValueError("Moves notation is not valid")

        return tuple(Oware.to_move(n) for n in notation)

    @staticmethod
    def to_position(notation):
        """Converts a position notation to a board tuple and turn"""

        pattern = '((?:[1-4]?[0-9]-){14})(S|N)$'
        match = re.match(pattern, notation)

        if match is None:
            raise ValueError("Position notation is not valid")

        turn = Oware.SOUTH
        board = []

        if 'N' == match.group(2):
            turn = Oware.NORTH

        houses = match.group(1).split('-')
        houses.pop()

        for seeds in houses:
            board.append(int(seeds))

        return (tuple(board), turn)
