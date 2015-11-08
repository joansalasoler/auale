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

from __future__ import with_statement

import os, math, time, threading

from game import Oware
from gi.repository import GLib
from gi.repository import GObject


class Animator(GObject.GObject):
    """Animates a canvas object"""
    
    __gtype_name__ = 'Animator'
    
    __gsignals__ = {
        
        'move-animation-finished': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE, ()
        ),
        
        'rotate-animation-finished': (
            GObject.SIGNAL_RUN_FIRST,
            GObject.TYPE_NONE, ()
        )
    }
    
    __PICKUP_ACTION = 0
    __DROP_ACTION = 1
    __GATHER_ACTION = 2
    
    
    def __init__(self, canvas, mixer):
        """Object initialization"""
        
        super(Animator, self).__init__()
        
        self._canvas = canvas
        self._mixer = mixer
        self._queue = []
        self._lock = threading.Lock()
        
        # Start the animation callback
        
        self._canvas.add_tick_callback(
            self._animate_canvas, None
        )
    
    
    def _animate_canvas(self, widget, clock, data = None):
        """Canvas animation loop"""
        
        with self._lock:
            if len(self._queue) == 0:
                return True
            
            finished = []
            
            for i in range(len(self._queue)):
                (method, args, start, step) = self._queue[i]
                delay = time.time() - start
                self._queue[i][3] = step + 1
                
                if method(delay, step, *args) == False:
                    finished.append((i, method))
            
            count = 0
            
            for index, method in finished:
                self._queue.pop(index - count)
                count += 1
            
        self._canvas.queue_draw()
        
        for index, method in finished:
            if method == self._animate_rotation:
                self.emit('rotate-animation-finished')
            elif method == self._animate_move:
                self.emit('move-animation-finished')
        
        return True
        
        
    def _add(self, method, *args):
        """Adds a method to the draw queue"""
        
        with self._lock:
            self._queue.append([
                method, args, time.time(), 0])
        
        
    def _remove(self, method):
        """Removes a method from the draw queue"""
        
        index = None
        
        with self._lock:
            for i in range(len(self._queue)):
                if method == self._queue[i][0]:
                    index = i
                    break
            
            if index is not None:
                self._queue.pop(index)
        
        
    def rotate_board(self):
        """Queue a board rotation animation"""
        
        angle = self._canvas.get_rotation()
        target = (angle == 0.0) and math.pi or 0.0
        self._add(self._animate_rotation, target)
        
        
    def make_move(self, match, move):
        """Queue a move animation"""
        
        frames = self._compute_move_frames(match, move)
        self._add(self._animate_move, frames)
        
        
    def stop_move(self):
        """Stops a move animation"""
        
        self._remove(self._animate_move)
        
        
    def _animate_rotation(self, delay, step, target):
        """Canvas rotation animation method"""
        
        if step == 0:
            self._mixer.on_board_rotate()
        
        angle = self._canvas.get_rotation()
        radians = delay * (math.pi / 0.4)
        
        if angle < target:
            rotation = radians - angle
            if angle + rotation > target:
                rotation = target - angle
            self._canvas.rotate(rotation)
            self._mixer.set_rotation(
                self._canvas.get_rotation())
            return True
            
        if angle > target:
            rotation = radians - math.pi + angle
            if angle - rotation < target:
                rotation = angle - target
            self._canvas.rotate(-rotation)
            self._mixer.set_rotation(
                self._canvas.get_rotation())
            return True
            
        self._canvas.set_active(None)
        
        return False
    
    
    def _animate_move(self, delay, step, frames):
        """Move animation method"""
        
        frame = int(delay / 0.4)
        
        if frame >= len(frames):
            self._canvas.set_active(None)
            return False
        
        (drawn, action, house, board) = frames[frame]
        
        if drawn == True:
            return True
        
        frames[frame][0] = True
        
        if action == Animator.__PICKUP_ACTION:
            self._mixer.on_house_pickup(house, 1)
        elif action == Animator.__DROP_ACTION:
            self._mixer.on_house_drop(house, 1)
        elif action == Animator.__GATHER_ACTION:
            self._mixer.on_house_gather(house, 1)
        
        if action == Animator.__PICKUP_ACTION:
            self._canvas.set_active(None)
            self._canvas.set_highlight(house)
            self._canvas.set_board(board)
        else:
            self._canvas.set_active(house)
            self._canvas.set_board(board)
        
        return True
    
    
    def _compute_move_frames(self, match, move):
        """Computes key frames of a move animation"""
        
        frames = list()
        
        # Pick up house seeds
        
        board = list(match.get_board())
        turn = match.get_turn()
        seeds = board[move]
        board[move] = 0
        
        frames.append([
            False, Animator.__PICKUP_ACTION,
            move, tuple(board)
        ])
        
        # Sow from the moved house
        
        for house in Oware._SEED_DRILL[move][:seeds]:
            board[house] += 1
            
            frames.append([
                False, Animator.__DROP_ACTION,
                house, tuple(board)
            ])
        
        # Gather seeds when possible
        
        if 4 > board[house] > 1:
            if move < 6 and house > 5:
                board_copy = board[:]
                frames_copy = frames[:]
                
                for house in Oware._HARVESTER[house]:
                    if not 4 > board_copy[house] > 1:
                        break
                    
                    board_copy[12] += board_copy[house]
                    board_copy[house] = 0
                    
                    frames_copy.append([
                        False, Animator.__GATHER_ACTION,
                        12, tuple(board_copy)
                    ])
                
                if board_copy[6:12] != Oware._EMPTY_ROWL:
                    frames = frames_copy
                    board = board_copy
            elif move > 5 and house < 6:
                board_copy = board[:]
                frames_copy = frames[:]
                
                for house in Oware._HARVESTER[house]:
                    if not 4 > board_copy[house] > 1:
                        break
                    
                    board_copy[13] += board_copy[house]
                    board_copy[house] = 0
                    
                    frames_copy.append([
                        False, Animator.__GATHER_ACTION,
                        13, tuple(board_copy)
                    ])
                
                if board_copy[0:6] != Oware._EMPTY_ROWL:
                    frames = frames_copy
                    board = board_copy
        
        # Gather remaining seeds when applicable
        
        if match.has_position(tuple(board), -turn) or \
        not Oware.has_legal_moves(tuple(board), -turn):
            for house in (6, 7, 8, 9, 10, 11):
                if board[house] > 0:
                    board[13] += board[house]
                    board[house] = 0
                    
                    frames.append([
                        False, Animator.__GATHER_ACTION,
                        13, tuple(board)
                    ])
            
            for house in (0, 1, 2, 3, 4, 5):
                if board[house] > 0:
                    board[12] += board[house]
                    board[house] = 0
                    
                    frames.append([
                        False, Animator.__GATHER_ACTION,
                        12, tuple(board)
                    ])
        
        return frames
    
