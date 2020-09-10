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

import sdl2.sdlmixer as SdlMixer
from gi.repository import GObject
from .sound_mixer import SoundMixer


class SoundSample(GObject.GObject):
    """Represents a cached audio sample"""

    __gtype_name__ = 'SoundSample'

    def __init__(self):
        GObject.GObject.__init__(self)

        self._path = None
        self._signal = None
        self._target = None
        self._loop = 0

    def get_loop(self):
        """Gets the loop of this sample"""

        return self._loop

    def set_loop(self, loop):
        """Sets the loop of this sample"""

        self._loop = loop

    def get_path(self):
        """Gets the path of this sample"""

        return self._path

    def set_path(self, path):
        """Sets the path of this sample"""

        self._path = path
        SoundMixer.cache_sample(path)

    def get_signal(self):
        """Gets the signal of this sample"""

        return self._signal

    def set_signal(self, signal):
        """Sets the signal of this sample"""

        self._signal = signal

    def get_target(self):
        """Gets the target of this sample"""

        return self._target

    def set_target(self, target):
        """Sets the target of this sample"""

        self._target = target

    def play(self, context):
        """Play this sample on the given context"""

        group_id = context.get_id()
        sample = SoundMixer.get_sample(self._path)
        channel = SdlMixer.Mix_PlayChannel(-1, sample, self._loop)
        SdlMixer.Mix_GroupChannel(channel, group_id)

    loop = GObject.Property(get_loop, set_loop, type=int)
    path = GObject.Property(get_path, set_path, type=str)
    signal = GObject.Property(get_signal, set_signal, type=str)
    target = GObject.Property(get_target, set_target, type=str)
