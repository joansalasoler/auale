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
from gi.repository import GObject
from gi.repository import Gtk
from serialize import OGNSerializer


class MatchManager(GObject.GObject):
    """Service to manage oware match files"""

    __gtype_name__ = 'MatchManager'

    def __init__(self):
        GObject.GObject.__init__(self)

        self._etag = None
        self._file = None
        self._match = None
        self._hash = hash(None)
        self._serializer = OGNSerializer()
        self._recent_manager = Gtk.RecentManager.get_default()

    @GObject.Signal
    def file_changed(self, match: object, is_new: bool):
        """Emitted on file changes"""

    @GObject.Signal
    def file_load_error(self, error: object):
        """Emitted on file load errors"""

    @GObject.Signal
    def file_save_error(self, error: object):
        """Emitted on file save errors"""

    @GObject.Signal(
        flags=GObject.SignalFlags.RUN_LAST,
        accumulator=GObject.signal_accumulator_true_handled
    )
    def file_overwrite(self, match: object) -> bool:
        """Emitted before a modified file is overwritten"""

    @GObject.Signal(
        flags=GObject.SignalFlags.RUN_LAST,
        accumulator=GObject.signal_accumulator_true_handled
    )
    def file_unload(self, match: object) -> bool:
        """Emitted before the match file is unloaded"""

    def get_file(self):
        """Current match file or none"""

        return self._file

    def get_game(self):
        """Game of the current match"""

        return self._match.get_game()

    def get_match(self):
        """Current match object"""

        return self._match

    def has_file_storage(self):
        """If the match is linked to a file """

        return bool(self.get_file())

    def has_unsaved_changes(self):
        """If the match contains unsaved changes"""

        return self._hash != hash(self._match)

    def unload(self):
        """Unloads the current match if any"""

        response = self._unload_is_not_aborted()

        if response is True:
            self._hash = hash(None)
            self._match = None
            self._file = None

        return not response

    def load_new_match(self):
        """Loads a new empty match"""

        if self._unload_is_not_aborted():
            self._etag = None
            self._file = None
            self._match = Match(Oware)
            self._hash = hash(self._match)
            self.file_changed.emit(self._match, True)

        return self._match

    def load_from_uri(self, uri):
        """Loads a match from an URI into this manager"""

        try:
            if self._unload_is_not_aborted():
                file, etag = self._obtain_file_for_uri(uri)
                match, etag = self._load_match_from_uri(uri)
                self._update_match_file(file, match, etag)
        except BaseException as error:
            self.file_load_error.emit(error)

        return self._match

    def save_to_uri(self, uri):
        """Saves the loaded match to the given file"""

        try:
            match = self._match
            file, etag = self._obtain_file_for_uri(uri)

            if self._overwrite_is_not_aborted(file):
                match, etag = self._save_match_to_file(file, match)
                self._update_match_file(file, match, etag)
        except BaseException as error:
            self.file_save_error.emit(error)

        return self._match

    def _load_match_from_uri(self, uri):
        """Loads a match from the given file path"""

        file = Gio.File.new_for_uri(uri)
        success, contents, etag = file.load_contents()
        data = contents.decode('utf-8')
        match = self._serializer.loads(data)

        return match, etag

    def _save_match_to_file(self, file, match, etag=None):
        """Saves a match to the given file"""

        data = self._serializer.dumps(self._match).encode('utf-8')
        save_params = (etag, False, Gio.FileCreateFlags.NONE, None)
        success, etag = file.replace_contents(data, *save_params)

        return match, etag

    def _update_match_file(self, file, match, etag):
        """Updates the current file information"""

        is_new = match != self._match

        self._etag = etag
        self._file = file
        self._match = match
        self._hash = hash(match)
        self._recent_manager.add_item(file.get_uri())
        self.file_changed.emit(match, is_new)

    def _unload_is_not_aborted(self):
        """Emits an unload event if match is not none"""

        signal = self.file_unload
        must_emit = isinstance(self._match, Match)
        can_continue = signal.emit(self._match) if must_emit else True

        return can_continue

    def _overwrite_is_not_aborted(self, file):
        """Emits an overwrite event if file changed since last read"""

        can_continue = True

        if self._is_current_file(file):
            signal = self.file_overwrite
            must_emit = self._etag != self._obtain_etag_for_file(file)
            can_continue = signal.emit(self._match) if must_emit else True

        return can_continue

    def _is_current_file(self, file):
        """If equal to the current file"""

        return file == self._file

    def _is_current_uri(self, uri):
        """If equal to the URI of the current file"""

        return self._file and uri == self._file.get_uri()

    def _obtain_etag_for_file(self, file):
        """Get the entity tag for the given file"""

        attribute = Gio.FILE_ATTRIBUTE_ETAG_VALUE
        query_params = (Gio.FileQueryInfoFlags.NONE, None)
        file_info = file.query_info(attribute, *query_params)

        return file_info.get_etag()

    def _obtain_file_for_uri(self, uri):
        """Get a file object for the given path"""

        file = self._file
        etag = self._etag

        if not self._is_current_uri(uri):
            file = Gio.File.new_for_uri(uri)
            etag = None

        return file, etag
