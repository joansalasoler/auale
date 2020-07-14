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

import copy


class Match(object):
    """Represents an oware match"""

    __TAG_ROSTER = (
        "Variant",
        "Event",
        "Site",
        "Date",
        "Round",
        "South",
        "North",
        "Result",
    )

    def __init__(self, game):
        """Object constructor"""

        self._game = game
        self._turn = game.SOUTH
        self._board = []
        self._moves = []
        self._positions = [(None, None)]
        self._comments = [None]
        self._has_ended = False
        self._current_index = 0
        self._tags = {}
        self._new_match()

    def _new_match(self):
        """Starts a new match with the defaul position"""

        turn = self._game.SOUTH
        board = self._game.get_initial_board()
        self.set_position(board, turn)

    def clone(self):
        """Creates a copy of this match"""

        return copy.copy(self)

    def get_game(self):
        """Obtains the game that is being played"""

        return self._game

    def get_length(self):
        """Number of stored moves on the match"""

        return len(self._moves)

    def get_current_index(self):
        """Return the index of the current move"""

        return self._current_index

    def get_capture_index(self):
        """Return the index of the last performed capture"""

        capture_index = 0

        for index in range(self._current_index, 0, -1):
            (next_board, turn) = self._positions[index]
            (prev_board, turn) = self._positions[index - 1]

            if next_board[12:] != prev_board[12:]:
                capture_index = index
                break

        return capture_index

    def get_moves(self):
        """Returns a tuple of performed moves"""

        return tuple(self._moves)

    def get_positions(self):
        """Returns a tuple of played positions"""

        return tuple(self._positions)

    def get_south_store(self):
        """Returns the current south store"""

        board = self._positions[self._current_index][0]

        return board[12]

    def get_north_store(self):
        """Returns the current north store"""

        board = self._positions[self._current_index][0]

        return board[13]

    def get_board(self):
        """Returns a copy of the current board position"""

        return self._board[:]

    def get_turn(self):
        """Returns the current turn"""

        return self._turn

    def get_move(self):
        """Move that lead to the current position or none"""

        index = self._current_index - 1
        move = self._moves[index] if index >= 0 else None

        return move

    def get_winner(self):
        """Returns the winner of the match (1 = South, -1 = North) or
           zero if the match ended in a draw or it hasn't ended yet"""

        if self._has_ended:
            return self._game.get_winner(
                self._board, self._turn)

        return 0

    def get_comment(self):
        """Returns the comment for the current move"""

        if self._current_index == 0:
            return None

        return self._comments[self._current_index]

    def can_undo(self):
        """Return True if a move can be undone"""

        return self._current_index > 0

    def can_redo(self):
        """Return True if a move can be redone"""

        return self._current_index < len(self._moves)

    def has_ended(self):
        """Returns if the match ended on the current position"""

        return self._has_ended

    def get_seeds(self, move):
        """Current number of seeds on the given house"""

        return self._board[move]

    def is_legal_move(self, move):
        """If the move is legal for the moving player"""

        return move in self.get_legal_moves()

    def is_valid_move(self, move):
        """If the move would be legal for one of the players"""

        board = self.get_board()
        south_moves = self._game.get_legal_moves(board, self._game.SOUTH)
        north_moves = self._game.get_legal_moves(board, self._game.NORTH)

        return move in south_moves or move in north_moves

    def is_capture_move(self, move):
        """If the move would capture at least one seed"""

        board = self.get_board()
        is_capture = move < 12 and self._game.is_capture(board, move)

        return is_capture

    def has_position(self, board, turn):
        """Returns true if the match contains the specified position
           in the positions prior to the current"""

        return (board, turn) in self._positions[:self._current_index + 1]

    def get_legal_moves(self):
        """Get the legal moves for the current position"""

        turn = self.get_turn()
        board = self.get_board()
        moves = self._game.get_legal_moves(board, turn)

        return tuple(moves)

    def set_comment(self, comment):
        """Adds a comment to the current move"""

        self._comments[self._current_index] = comment

    def set_position(self, board, turn):
        """Sets a new position and initialitzes match properties"""

        # Set the board position and turn

        self._turn = turn
        self._board = board[:]
        self._moves = []
        self._positions = [(self._board[:], self._turn)]
        self._comments = [None]
        self._has_ended = False
        self._current_index = 0

        # Fill default tags

        self._tags = {}
        self.reset_tags()

        # Set start position tag

        if self._board != self._game.get_initial_board() \
        and self._turn != self._game.SOUTH:
            notation = self._game.to_board_notation(self._board, self._turn)
            self._tags['FEN'] = '%s' % notation

    def add_move(self, move):
        """Adds a new move to the match after the current position"""

        if not self.is_legal_move(move):
            raise ValueError("Not a legal move")

        # Update the board and switch the turn

        self._board = self._game.make_move(self._board, move)
        self._turn = -self._turn

        # Check if the match ended and compute the final board

        if self._game.is_endgame(self._board, self._turn) \
        or self.has_position(self._board, self._turn):
            self._board = self._game.get_final_board(self._board)
            self._has_ended = True
            self._tags['Result'] = '%d-%d' % (
                self._board[12], self._board[13])
        elif self._tags['Result'] != '*':
            self._tags['Result'] = '*'

        # Record the move and position

        self._moves = self._moves[:self._current_index]
        self._comments = self._comments[:self._current_index + 1]
        self._positions = self._positions[:self._current_index + 1]
        self._moves.append(move)
        self._comments.append(None)
        self._positions.append((self._board[:], self._turn))
        self._current_index += 1

    def undo_last_move(self):
        """Undoes the last move"""

        if self.can_undo():
            self._current_index -= 1
            self._turn = self._positions[self._current_index][1]
            self._board = self._positions[self._current_index][0]
            self._has_ended = False

    def redo_last_move(self):
        """Redoes the last move"""

        if self.can_redo():
            self._current_index += 1
            self._turn = self._positions[self._current_index][1]
            self._board = self._positions[self._current_index][0]

            # Check if the match ended on that position

            if self._game.is_endgame(self._board, self._turn):
                self._has_ended = True

    def undo_all_moves(self):
        """Undoes all the moves"""

        if self.can_undo():
            self._current_index = 0
            self._turn = self._positions[0][1]
            self._board = self._positions[0][0]
            self._has_ended = False

    def redo_all_moves(self):
        """Redoes all the moves"""

        if self.can_redo():
            self._current_index = len(self._positions) - 1
            self._turn = self._positions[self._current_index][1]
            self._board = self._positions[self._current_index][0]

            # Check if the match ended on that position

            if self._game.is_endgame(self._board, self._turn):
                self._has_ended = True

    def reset_tags(self):
        """Clears all the match tags"""

        self._tags.clear()

        for tag in self.__TAG_ROSTER:
            self._tags[tag] = '?'

        self._tags['Variant'] = self._game.get_ruleset_name()
        self._tags['Result'] = '*'

    def get_tag_roster(self):
        """Obtains the mandatory tag identifiers"""

        return self.__TAG_ROSTER

    def get_tag(self, tag):
        """Returns a match tag value or none"""

        value = None

        if tag in self._tags and self._tags[tag] != '?':
            value = self._tags[tag]

        return value

    def get_tags(self):
        """Returns a tuple view of this match tags"""

        tags = []

        for tag in self.__TAG_ROSTER:
            tags.append((tag, self._tags[tag]))

        for tag, value in sorted(self._tags.items()):
            if tag not in self.__TAG_ROSTER:
                tags.append((tag, value))

        return tuple(tags)

    def set_tag(self, name, value):
        """Tags this match with a value"""

        if not isinstance(name, str):
            raise ValueError("Tag name must be a string")

        if not isinstance(value, str):
            raise ValueError("Tag value must be a string")

        self._tags[name.strip()] = value.strip()

    def set_tags(self, tags):
        """Sets the tags from the given tuple"""

        self.reset_tags()

        for name, value in tags:
            self.set_tag(name, value)

    def get_notation(self):
        """Converts this match to a valid notation tuple"""

        count = 1.0
        tokens = []
        board, turn = self._positions[0]

        for i in range(len(self._moves)):
            next_board, next_turn = self._positions[i + 1]
            move = self._moves[i]
            comment = self._comments[1 + i]
            number = int(count)
            captures = ''

            if count == number:
                tokens.append('%d.' % number)

            if next_turn == self._game.NORTH:
                if board[12] != next_board[12]:
                    captures = '+%d' % (
                        next_board[12] - board[12])
            elif board[13] != next_board[13]:
                captures = '+%d' % (
                    next_board[13] - board[13])

            alpha = self._game.to_move_notation(move)
            tokens.append('%s%s' % (alpha, captures))

            if comment is not None:
                tokens.append('{')
                tokens.extend(comment.split())
                tokens.append('}')

            board = next_board
            count += 0.5

        if self._tags['Result'] != '*':
            tokens.append(self._tags['Result'])

        return tuple(tokens)

    def __hash__(self):
        """Computes a hash for this object"""

        header = tuple(self._tags.items())
        contents = tuple(self._comments)
        states = tuple(self._positions)

        return hash((states, header, contents))

    def __eq__(self, other):
        """Compare two objects for equality"""

        if not isinstance(other, Match):
            return False

        if other._positions != self._positions:
            return False

        if other._comments != self._comments:
            return False

        if other._tags != self.__tags:
            return False

        return True
