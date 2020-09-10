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
from gi.repository import Gio
from gi.repository import GObject
from gi.repository import Json


class SoundContext(GObject.GObject):
    """Plays sounds on a given context"""

    __gtype_name__ = 'SoundContext'
    __counter = 0

    def __init__(self):
        GObject.GObject.__init__(self)
        SoundContext.__counter += 1

        self._is_muted = False
        self._id = SoundContext.__counter
        self._samples = []

    def get_id(self):
        """Unique integer identifier of this group"""

        return self._id

    def is_muted(self):
        """Checks if this context is muted"""

        return self._is_muted

    def mute_context(self):
        """Stops playing sounds on this context"""

        if not self.is_muted():
            self._is_muted = True
            SdlMixer.Mix_HaltGroup(self._id)

    def unmute_context(self):
        """Resumes playing sounds on this context"""

        self._is_muted = False

    def play_sample(self, sample):
        """Plays an audio sample on this context"""

        if not self.is_muted():
            sample.play(self)

    def connect_signals(self, widget):
        """Context the loaded signals to the given object"""

        for sample in self._samples:
            if widget.__gtype_name__ == sample.get_target():
                signal_name = sample.get_signal()
                widget.connect(signal_name, self._invoke_play, sample)

    def load_from_resource(self, resource_path):
        """Loads a sound script from a resource file"""

        flags = Gio.ResourceLookupFlags.NONE
        data = Gio.resources_lookup_data(resource_path, flags)
        contents = data.get_data().decode('utf-8')
        script = Json.from_string(contents).get_array()

        for element in script.get_elements():
            node = element.get_object()
            type_name = node.get_string_member('type')
            instance = Json.gobject_deserialize(type_name, element)
            self._samples.append(instance)

    def _invoke_play(self, *params):
        """Invokes the play sample method"""

        self.play_sample(params[-1])
