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

from game import Match
from game import Oware
from gi.repository import Gio
from gi.repository import Gtk
from gi.repository import GObject
from serialize import OGNSerializer


class MatchManager(GObject.GObject):
    """Service to manage oware match files"""

    __gtype_name__ = 'MatchManager'

    def __init__(self):
        GObject.GObject.__init__(self)

        self._file = None
        self._match = Match(Oware)
        self._serializer = OGNSerializer()
        self._recent_manager = Gtk.RecentManager.get_default()

    @GObject.Signal
    def file_changed(self, match: object):
        """Emitted on file changes"""

    def get_file(self):
        """Current match file or none"""

        return self._file

    def get_match(self):
        """Current match object"""

        return self._match

    def load_from_uri(self, uri):
        """Loads a match from an URI into this manager"""

        file = Gio.File.new_for_uri(uri)
        data = file.load_bytes()[0].get_data().decode('utf-8')
        match = self._serializer.loads(data)

        self._file = file
        self._match = match
        self._recent_manager.add_item(uri)
        self.file_changed.emit(match)

        return match
