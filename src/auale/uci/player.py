#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014-2015 Joan Sala Soler <contact@joansala.com>
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

import os, sys, threading, subprocess

from game import Oware, Match
from uci import UCIClient


class UCIPlayer():
    """
    This class is an abstraction of an engine player that implements the UCI
    protocol and provides useful methods to interact with the engine.
    """
    
    class Strength:
        EASY = 0
        MEDIUM = 1
        HARD = 2
        EXPERT = 3
    
    ABORT_DELAY = 10.0
    
    
    def __init__(self, command, game):
        """Initializes this UCI engine"""
        
        self._depth = 4
        self._move_time = 600
        self._strength = UCIPlayer.Strength.EASY
        self._position = 'startpos'
        self._moves = None
        
        # Start the process and get the client
        
        starti = None
        
        if hasattr(subprocess, 'STARTUPINFO'):
            starti = subprocess.STARTUPINFO()
            starti.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        self._service = subprocess.Popen(
            command, bufsize = 1,
            startupinfo = starti,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            universal_newlines = True
        )
        
        self._client = UCIClient(game, self._service)
        self._game = game
        
        # Initialize the engine
        
        self._init_uci()
        self._name = self._client.get_name()
        self._author = self._client.get_author()
    
    
    def get_name(self):
        """Returns the engine name"""
        
        return self._name
    
    
    def get_author(self):
        """Returns the engine author"""
        
        return self._author
        
        
    def get_strength(self):
        """Returns this player's current strength"""
        
        return self._strength
        
        
    def set_depth(self, depth):
        """Sets the maximum allowed search depth"""
        
        if depth is not None:
            if type(depth) != int or depth <= 0:
                raise ValueError("Not a valid depth value")
        
        self._depth = depth
    
    
    def set_move_time(self, move_time):
        """Sets the maximum allowed time per move"""
        
        if type(move_time) != int or move_time <= 0:
            raise ValueError("Not a valid time per move")
        
        self._move_time = move_time
    
    
    def set_strength(self, strength):
        """Sets this engine depth and time per move according to
           a provided strength value"""
        
        if UCIPlayer.Strength.EASY == strength:
            self.set_depth(4)
            self.set_move_time(600)
        elif UCIPlayer.Strength.MEDIUM == strength:
            self.set_depth(10)
            self.set_move_time(1000)
        elif UCIPlayer.Strength.HARD == strength:
            self.set_depth(16)
            self.set_move_time(2000)
        elif UCIPlayer.Strength.EXPERT == strength:
            self.set_depth(None)
            self.set_move_time(3600)
        else:
            raise ValueError("Not a valid strength value")
        
        self._strength = strength
    
    
    def set_position(self, match):
        """Sets the board position for the player"""
        
        self._position = 'startpos'
        self._moves = None
        
        # Sent position must include last capture
        
        current = match.get_current_index()
        match_positions = match.get_positions()[:1 + current]
        match_moves = list(match.get_moves()[:1 + current])
        
        # Build the position string
        
        capture = self._get_capture_index(match_positions)
        (startpos, turn) = match_positions[capture]
        
        if startpos != self._game.get_initial_board():
            notation = self._game.to_board_notation(startpos, turn)
            self._position = 'fen %s' % notation
        
        # Build the moves string
        
        if capture != current:
            match_moves = match_moves[capture:current]
            notation = self._game.to_moves_notation(match_moves)
            self._moves = notation
    
    
    def new_match(self):
        """Start a new match"""
        
        self._client.send('ucinewgame')
        self._client.send('isready')
        
        while not self._client.is_ready():
            self._client.receive()
    
    
    def quit(self):
        """Asks the engine to quit"""
        
        self._client.send('quit')
    
    
    def stop(self):
        """Asks the engine to stop thinking"""
        
        self._client.send('stop')
    
    
    def retrieve_move(self):
        """Asks the player to think and returns a move"""
        
        self.start_thinking()
        
        while self._client.is_thinking():
            self._client.receive()
        
        return self._client.get_best_move()
    
    
    def start_thinking(self):
        """Instructs the engine to think"""
        
        pos_command = self._position_command()
        go_command = self._go_command()
        
        self.abort_computation()
        self._client.send(pos_command)
        self._client.send(go_command)
    
    
    def start_pondering(self):
        """Instructs the engine to ponder"""
        
        moves = []
        
        best_move = self._client.get_best_move()
        ponder_move = self._client.get_ponder_move()
        
        if best_move != self._game.NULL_MOVE:
            moves.append(best_move)
        
        if ponder_move != self._game.NULL_MOVE:
            moves.append(ponder_move)
        
        pos_command = self._position_command(moves)
        go_command = self._go_command()
        
        self.abort_computation()
        self._client.send(pos_command)
        self._client.send('go ponder')
    
    
    def abort_computation(self):
        """Aborts any ongoing computations"""
        
        if self._client.is_pondering():
            self._client.send('stop')
            
            while self._client.is_pondering():
                self._client.receive()
        
        if self._client.is_thinking():
            self._client.send('stop')
            
            while self._client.is_thinking():
                self._client.receive()
    
    
    def _go_command(self):
        """Returns a suitable go command"""
        
        command = ['go']
        
        if self._depth is not None:
            command.append('depth')
            command.append(str(self._depth))
        
        command.append('movetime')
        command.append(str(self._move_time))
        
        return ' '.join(command)
    
    
    def _position_command(self, moves = None):
        """Returns a position command for the match"""
        
        command = []
        notation = ''
        
        command.append('position')
        command.append(self._position)
        
        if self._moves is not None:
            notation = str(self._moves)
        
        if moves is not None and len(moves) > 0:
            notation += self._game.to_moves_notation(moves)
        
        if len(notation) > 0:
            command.append('moves')
            command.append(notation)
        
        return ' '.join(command)
    
    
    def _get_capture_index(self, positions):
        """Returns the last capture index"""
        
        index = 0
        
        for i in range(len(positions) - 1, 0, -1):
            (nboard, turn) = positions[i]
            (pboard, turn) = positions[i - 1]
            
            if nboard[12] != pboard[12] \
            or nboard[13] != pboard[13]:
                index = i
                break
        
        return index
    
    
    def _init_uci(self):
        """Starts the engine in UCI mode"""
        
        timer = threading.Timer(
            UCIPlayer.ABORT_DELAY,
            self._destroy_service
        )
        
        timer.start()
        
        try:
            self._client.send('uci')
            
            while not self._client.is_uci_ready():
                self._client.receive()
        finally:
            timer.cancel()
        
        
    def _destroy_service(self):
        """Kills the opened process"""
        
        self._service.kill()

