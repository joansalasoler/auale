#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

"""
Aualé oware graphic user interface.
Copyright (C) 2014 Joan Sala Soler <contact@joansala.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, re
import codecs


class Match(object):
    """Represents an oware match"""
    
    __TAG_ROSTER = (
        "Variant", "Event", "Site",  "Date",
        "Round",   "South", "North", "Result", 
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
        self._current_move = 0
        self._tags = {}
        
        self.new_match()
        
        
    def __str__(self):
        """Returns a string representation of this object"""
        
        return 'Match(board=%s, turn=%s)' % \
            (self.get_board(), self.get_turn())
        
        
    def new_match(self):
        """Starts a new match with the defaul position"""
        
        self.set_position(
            self._game.get_initial_board(),
            self._game.SOUTH
        )
        
        
    def get_current_index(self):
        """Return the index of the current move"""
        
        return self._current_move
        
        
    def get_moves(self):
        """Returns a tuple of performed moves"""
        
        return tuple(self._moves)
        
        
    def get_positions(self):
        """Returns a tuple of played positions"""
        
        return tuple(self._positions)
        
        
    def get_south_store(self):
        """Returns the current south store"""
        
        board = self._positions[self._current_move][0]
        
        return board[12]
        
        
    def get_north_store(self):
        """Returns the current north store"""
        
        board = self._positions[self._current_move][0]
        
        return board[13]
        
        
    def get_previous_move(self):
        """Returns the previous move on the match history"""
        
        if self._current_move <= 0:
            raise IndexError
        
        return self._moves[self._current_move - 1]
        
        
    def get_next_move(self):
        """Returns the next move on the match history"""
        
        return self._moves[self._current_move + 1]
        
        
    def get_board(self):
        """Returns a copy of the current board position"""
        
        return self._board[:]
        
        
    def get_turn(self):
        """Returns the current turn"""
        
        return self._turn
        
        
    def get_winner(self):
        """Returns the winner of the match (1 = South, -1 = North) or
           zero if the match ended in a draw or it hasn't ended yet"""
        
        if self._has_ended:
            return self._game.get_winner(
                self._board, self._turn)
            
        return 0
        
        
    def get_comment(self):
        """Returns the comment for the current move"""
        
        if self._current_move == 0:
            return None
        
        return self._comments[self._current_move]
    
    
    def can_undo(self):
        """Return True if a move can be undone"""
        
        return self._current_move > 0
        
        
    def can_redo(self):
        """Return True if a move can be redone"""
        
        return self._current_move < len(self._moves)
        
        
    def has_ended(self):
        """Returns if the match ended on the current position"""
        
        return self._has_ended
        
        
    def is_legal_move(self, move):
        """Returns true if the move is legal for the current position"""
        
        return move in self._game.xlegal_moves(
            self.get_board(), self.get_turn())
        
        
    def has_position(self, board, turn):
        """Returns true if the match contains the specified position
           in the positions prior to the current"""
        
        return (board, turn) in self._positions[:self._current_move + 1]
        
        
    def set_comment(self, comment):
        """Adds a comment to the current move"""
        
        self._comments[self._current_move] = comment
        
        
    def set_position(self, board, turn):
        """Sets a new position and initialitzes match properties"""
        
        # Set the board position and turn
        
        self._turn = turn
        self._board = board[:]
        self._moves = []
        self._positions = [(self._board[:], self._turn)]
        self._comments = [None]
        self._has_ended = False
        self._current_move = 0
        
        # Fill default tags
        
        self._tags = {}
        
        for tag in self.__TAG_ROSTER:
            self._tags[tag] = '?'
        
        self._tags['Variant'] = self._game.get_ruleset_name()
        self._tags['Result'] = '*'
        
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
        
        self._board = self._game.compute_board(self._board, move)
        self._turn = -self._turn
        
        # Check if the match ended and compute the final board
        
        if self._game.is_end(self._board, self._turn) \
        or self.has_position(self._board, self._turn):
            self._board = self._game.get_final_board(self._board)
            self._has_ended = True
            self._tags['Result'] = '%d-%d' % (
                self._board[12], self._board[13])
        elif self._tags['Result'] != '*':
            self._tags['Result'] = '*'
        
        # Record the move and position
        
        self._moves = self._moves[:self._current_move]
        self._comments = self._comments[:self._current_move + 1]
        self._positions = self._positions[:self._current_move + 1]
        self._moves.append(move)
        self._comments.append(None)
        self._positions.append((self._board[:], self._turn))
        self._current_move += 1
    
    
    def undo_last_move(self):
        """Undoes the last move"""
        
        if self.can_undo():
            self._current_move -= 1
            self._turn = self._positions[self._current_move][1]
            self._board = self._positions[self._current_move][0]
            self._has_ended = False
        
        
    def redo_last_move(self):
        """Redoes the last move"""
        
        if self.can_redo():
            self._current_move += 1
            self._turn = self._positions[self._current_move][1]
            self._board = self._positions[self._current_move][0]
            
            # Check if the match ended on that position
            
            if self._game.is_end(self._board, self._turn):
                self._has_ended = True
    
    
    def undo_all_moves(self):
        """Undoes all the moves"""
        
        if self.can_undo():
            self._current_move = 0
            self._turn = self._positions[0][1]
            self._board = self._positions[0][0]
            self._has_ended = False
        
        
    def redo_all_moves(self):
        """Redoes all the moves"""
        
        if self.can_redo():
            self._current_move = len(self._positions) - 1
            self._turn = self._positions[self._current_move][1]
            self._board = self._positions[self._current_move][0]
            
            # Check if the match ended on that position
            
            if self._game.is_end(self._board, self._turn):
                self._has_ended = True
    
    
    def set_tag(self, name, value):
        """Tags this match with a value"""
        
        if type(name) != str:
            raise ValueError("Tag name must be a string")
            
        if type(value) != str:
            raise ValueError("Tag value must be a string")
            
        self._tags[name.strip()] = value.strip()
        
        
    def get_tags(self):
        """Returns a tuple view of this match tags"""
        
        tags = []
        
        for tag in self.__TAG_ROSTER:
            tags.append((tag, self._tags[tag]))
        
        for tag, value in sorted(self._tags.items()):
            if tag not in self.__TAG_ROSTER:
                tags.append((tag, value))
        
        return tuple(tags)
        
        
    def get_tag(self, tag):
        """Returns a match tag value"""
        
        if tag not in self._tags:
            return None
        
        return self._tags[tag]
        
        
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
        
        
    def save(self, path):
        """Save this match to a file"""
        
        with codecs.open(path, 'w', 'utf-8') as fileo:
            self._write_tags(fileo)
            if len(self._moves) > 0:
                self._write(fileo, '\n')
                self._write_moves(fileo)
        
        
    def load(self, path):
        """Load a match from a file"""
        
        # Read the match from a file
        
        try:
            with codecs.open(path, 'r', 'utf-8') as fileo:
                header = self._read(fileo, 8)
                if header != '[Variant': raise ValueError()
                string = header + self._read(fileo)
            
            (tags, index) = self._read_tags(string, 0)
            (moves, comments, index) = self._read_moves(string, index)
            
            match = Match(self._game)
            
            if 'FEN' in tags:
                notation = tags['FEN']
                (board, turn) = self._game.to_position(notation)
                match.set_position(board, turn)
            
            for move in moves:
                match.add_move(move)
        except:
            raise ValueError(
                "Not a valid match file")
        
        # Set this match properties
        
        self._tags = tags
        self._turn = match._turn
        self._board = match._board
        self._moves = match._moves
        self._comments = comments
        self._positions = match._positions
        self._has_ended = match._has_ended
        self._current_move = match._current_move
        
        
    def _unescape(self, value):
        """Unescapes a tag value"""
        
        value = value.replace('\\"', '\"')
        value = value.replace('\\\\', '\\')
        
        return value
        
        
    def _escape(self, value):
        """Escapes a tag value"""
        
        value = value.replace('\\', '\\\\')
        value = value.replace('\"', '\\"')
        
        return value
    
    
    def _read(self, fileo, size = -1):
        """Read a string from a file. If an unicode string is returned
           this method converts it to an utf-8 string"""
        
        string = fileo.read(size)
        
        if sys.version_info.major < 3:
            string = string.encode('utf-8')
        
        return string
    
    
    def _write(self, fileo, string):
        """Writes a string to a file. If an unicode string is provided
           this method converts it to an utf-8 string"""
        
        if sys.version_info.major < 3:
            string = string.decode('utf-8')
        
        fileo.write(string)
    
    
    def _read_tags(self, string, index):
        """Reads all header tags from the string"""
        
        pattern = re.compile(r'\s*\[\s*(\w+)\s+"((?:[^"]|\\")*)"\s*\]')
        
        # Create a new default tag set
        
        tags = {}
        
        for tag in self.__TAG_ROSTER:
            tags[tag] = '?'
        
        tags['Variant'] = self._game.get_ruleset_name()
        tags['Result'] = '*'
        
        # Parse tags from the string
        
        while index < len(string):
            m = pattern.match(string, index)
            if m is None: break
            tag = m.group(1)
            value = self._unescape(m.group(2))
            tags[tag] = value
            index = m.end(0)
        
        return (tags, index)
        
        
    def _read_moves(self, string, index):
        """Reads all the moves from the string"""
        
        move_pattern = re.compile(r'([A-Fa-f])')
        comments = [None]
        moves = []
        
        while index < len(string):
            if string[index] == '{':
                comment, index = self._read_comment(string, index)
                if len(comments) > 0: comments[-1] = comment
            elif string[index] == '(':
                variation, index = self._read_variation(string, index)
            else:
                m = move_pattern.match(string, index)
                if m is not None:
                    notation = m.group(1)
                    move = self._game.to_move(notation)
                    comments.append(None)
                    moves.append(move)
                index += 1
        
        return (moves, comments, index)
        
        
    def _read_comment(self, string, index):
        """Reads a single comment from the string"""
        
        comment = None
        
        if index < len(string):
            pattern = re.compile(r'([^}]*)')
            m = pattern.match(string, index + 1)
            
            if m is not None:
                index = m.end(1)
                comment = ' '.join(m.group(1).split())
        
        return (comment, index)
        
        
    def _read_variation(self, string, index):
        """Reads a single comment from the string"""
        
        variation = None
        
        if index < len(string):
            pattern = re.compile(r'([^)]*)')
            m = pattern.match(string, index + 1)
            
            if m is not None:
                variation = m.group(1)
                index = m.end(1)
        
        return (variation, index)
        
        
    def _write_tags(self, fileo):
        """Writes this match tags to a file"""
        
        for tag in self.__TAG_ROSTER:
            value = self._escape(self._tags[tag])
            string = '[%s "%s"]\n' % (tag, value)
            self._write(fileo, string)
        
        for tag in self._tags:
            if tag not in self.__TAG_ROSTER:
                value = self._escape(self._tags[tag])
                string = '[%s "%s"]\n' % (tag, value)
                self._write(fileo, string)
    
    
    def _write_moves(self, fileo):
        """Writes moves from a match to a file"""
        
        tokens = self.get_notation()
        line = str(tokens[0])
        
        for token in tokens[1:]:
            if 1 + len(line) + len(token) < 80:
                line = '%s %s' % (line, token)
                continue
            
            self._write(fileo, '%s\n' % line)
            line = str(token)
        
        self._write(fileo, '%s\n' % line)
    
