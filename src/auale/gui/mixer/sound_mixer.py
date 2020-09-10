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

import sdl2 as Sdl
import sdl2.sdlmixer as SdlMixer
from gi.repository import Gio
from gi.repository import GObject


class SoundMixer(GObject.GObject):
    """Plays sounds for aplication window events"""

    __gtype_name__ = 'SoundMixer'
    __cache = dict()

    def __init__(self):
        GObject.GObject.__init__(self)
        SoundMixer.init()

    @staticmethod
    def init():
        """Initialize the sound mixer"""

        if not Sdl.SDL_WasInit(Sdl.SDL_INIT_AUDIO):
            SoundMixer._init_sdl_mixer()

    @staticmethod
    def quit():
        """Finalize the sound mixer"""

        if Sdl.SDL_WasInit(Sdl.SDL_INIT_AUDIO):
            SoundMixer._close_sdl_mixer()

    @staticmethod
    def _init_sdl_mixer():
        """Initialize the SDL mixer library"""

        frequency = SdlMixer.MIX_DEFAULT_FREQUENCY
        format = SdlMixer.MIX_DEFAULT_FORMAT

        Sdl.SDL_Init(Sdl.SDL_INIT_AUDIO)
        SdlMixer.Mix_Init(SdlMixer.MIX_INIT_OGG)
        SdlMixer.Mix_OpenAudio(frequency, format, 2, 1024)
        SdlMixer.Mix_AllocateChannels(32)

    @staticmethod
    def _close_sdl_mixer():
        """Finalize the SDL mixer library"""

        SdlMixer.Mix_CloseAudio()
        SdlMixer.Mix_Quit()
        Sdl.SDL_Quit()

    @staticmethod
    def get_sample(resource_path):
        """Obtains an audio sample from the cache"""

        return SoundMixer.__cache[resource_path]

    @staticmethod
    def cache_sample(resource_path):
        """Loads an audio sample and adds it to the cache"""

        if resource_path not in SoundMixer.__cache:
            sample = SoundMixer.load_sample(resource_path)
            SoundMixer.__cache[resource_path] = sample

    @staticmethod
    def load_sample(resource_path):
        """Loads an audio sample from a GTK resoure file"""

        flags = Gio.ResourceLookupFlags.NONE
        data = Gio.resources_lookup_data(resource_path, flags)
        data_buffer, data_size = data.get_data(), data.get_size()
        rw = Sdl.SDL_RWFromConstMem(data_buffer, data_size)
        sample = SdlMixer.Mix_LoadWAV_RW(rw, 0)

        return sample
