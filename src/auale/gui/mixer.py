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

from __future__ import with_statement

import os, sys
import math, threading
import util

_SDL_IS_DISABLED = False

try:
    if 'win' in sys.platform:
        path = util.resource_path('./lib/sdl')
        os.environ['PYSDL2_DLL_PATH'] = path
    
    import sdl2 as sdl
    import sdl2.sdlmixer as mixer
except:
    _SDL_IS_DISABLED = True

from gui import App


class Mixer():
    """Plays sounds according to received events"""
    
    # Total number of open mixer objects. This is used to quit SDL
    # when no mixer objects are in use
    
    __OPENED_COUNT = 0
    
    # Audio files path
    
    __DROP_PATH = util.resource_path('./res/sound/drop.wav')
    __GATHER_PATH = util.resource_path('./res/sound/gather.wav')
    __PICK_UP_PATH = util.resource_path('./res/sound/pickup.wav')
    __ROTATE_PATH = util.resource_path('./res/sound/rotate.wav')
    __START_PATH = util.resource_path('./res/sound/start.wav')
    
    # WA: Fixes a 'TypeError' when using pySDL2 & Python3
    
    if sys.version_info.major > 2:
        __DROP_PATH = __DROP_PATH.encode('utf-8')
        __GATHER_PATH = __GATHER_PATH.encode('utf-8')
        __PICK_UP_PATH = __PICK_UP_PATH.encode('utf-8')
        __ROTATE_PATH = __ROTATE_PATH.encode('utf-8')
        __START_PATH = __START_PATH.encode('utf-8')
    
    
    def __init__(self):
        """Initializes a new mixer object"""
        
        self._muted = False
        self._angle = 0.0
        self._last_channel = 15
        self._next_channel = 0
        self._lock = threading.Lock()
        
        # Check if SDL was loaded
        
        if _SDL_IS_DISABLED:
            return
        
        # Set PulseAudio environment variables
        
        if hasattr(os, "putenv"):
            os.putenv("PULSE_PROP_application.name", App.NAME)
            os.putenv("PULSE_PROP_application.icon_name", App.ICON)
            os.putenv("PULSE_PROP_media.role", App.ROLE)
        
        # Initialize SDL audio and mixer
        
        if not sdl.SDL_WasInit(sdl.SDL_INIT_AUDIO):
            sdl.SDL_Init(sdl.SDL_INIT_AUDIO)
        
        mixer.Mix_OpenAudio(
            mixer.MIX_DEFAULT_FREQUENCY,
            mixer.MIX_DEFAULT_FORMAT,
            2,
            1024
        )
        
        mixer.Mix_AllocateChannels(1 + self._last_channel)
        
        # Load available sounds files
        
        self._wav_drop   = mixer.Mix_LoadWAV(Mixer.__DROP_PATH)
        self._wav_gather = mixer.Mix_LoadWAV(Mixer.__GATHER_PATH)
        self._wav_pickup = mixer.Mix_LoadWAV(Mixer.__PICK_UP_PATH)
        self._wav_rotate = mixer.Mix_LoadWAV(Mixer.__ROTATE_PATH)
        self._wav_start  = mixer.Mix_LoadWAV(Mixer.__START_PATH)
        
        Mixer.__OPENED_COUNT += 1
        
        
    def is_disabled(self):
        """Tells if the mixer is disabled"""
        
        return _SDL_IS_DISABLED
    
    
    def stop_mixer(self):
        """Close resources and clean up"""
        
        if _SDL_IS_DISABLED:
            return
        
        mixer.Mix_CloseAudio()
        mixer.Mix_Quit()
        
        Mixer.__OPENED_COUNT -= 1
        
        if not Mixer.__OPENED_COUNT:
            sdl.SDL_Quit()
    
    
    def toggle_mute(self):
        """Enables and disables sound effects"""
        
        if _SDL_IS_DISABLED:
            return
        
        if self._muted:
            mixer.Mix_Volume(-1, mixer.MIX_MAX_VOLUME)
            self._muted = False
        else:
            mixer.Mix_Volume(-1, 0)
            self._muted = True
        
    
    def set_rotation(self, angle):
        """Sets the board rotation angle in radians"""
        
        if _SDL_IS_DISABLED:
            return
        
        if self._muted:
            return
        
        self._angle = angle
        
        
    def play_on_house(self, house, chunk):
        """Plays a chunk with a panning relative to a house."""
        
        if _SDL_IS_DISABLED:
            return
        
        if self._muted:
            return
        
        with self._lock:
            channel = self._next_channel
            self._next_channel = (1 + channel) % 15
        
        # Compute a nice panning effect
        
        if house < 6: place = house
        if house > 5: place = 11 - house
        if house == 12: place = 6
        if house == 13: place = -1
        
        cos = math.cos(self._angle)
        dis = 16 * cos * (place - 2.5)
        right = int(127 + dis)
        left = int(254 - right)
        
        # Play the sound on the choosen channel
        
        mixer.Mix_SetPanning(channel, left, right)
        mixer.Mix_PlayChannel(channel, chunk, 0)
    
    
    def on_board_rotate(self):
        """Plays a board rotation sound"""
        
        if _SDL_IS_DISABLED:
            return
        
        mixer.Mix_PlayChannel(
            self._last_channel,
            self._wav_rotate,
            0
        )
    
    
    def on_house_gather(self, house, seeds):
        """Plays a sound for a gather event"""
        
        if not _SDL_IS_DISABLED:
            self.play_on_house(house, self._wav_gather)
    
    
    def on_house_pickup(self, house, seeds):
        """Plays a sound for a seeds pick up event"""
        
        if not _SDL_IS_DISABLED:
            self.play_on_house(house, self._wav_pickup)
    
    
    def on_house_drop(self, house, seeds):
        """Plays a sound for a seed drop event"""
        
        if not _SDL_IS_DISABLED:
            self.play_on_house(house, self._wav_drop)
    
    
    def on_game_start(self):
        """Plays a game start sound"""
        
        if not _SDL_IS_DISABLED:
            self.play_on_house(2.5, self._wav_start)

