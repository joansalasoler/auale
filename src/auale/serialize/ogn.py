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

import io
import re

from game import Oware
from game import Match


class OGNSerializer(object):
    """Marshal match objects to Oware Game Notation"""

    def __init__(self):
        self.__version = 1
        self._comment_regex = re.compile(r'([^}]*)')
        self._move_regex = re.compile(r'([A-Fa-f])')
        self._tag_regex = re.compile(r'\s*\[\s*(\w+)\s+"((?:[^"]|\\")*)"\s*\]')
        self._varitation_regex = re.compile(r'([^)]*)')

    @property
    def version(self):
        return self.__version

    def dump(self, match, file):
        """Saves a match to a file"""

        self._write_tags(match, file)

        if len(match.get_moves()) > 0:
            file.write('\n')
            self._write_moves(match, file)

    def load(self, file):
        """Load a match from a file"""

        return self.loads(file.read())

    def dumps(self, match):
        """Dumps a match to a string"""

        buffer = io.StringIO()
        self.dump(match, buffer)

        return buffer.getvalue()

    def loads(self, string):
        """Loads a match from a string"""

        match = Match(Oware)

        tags, index = self._read_tags(string)
        moves, comments, index = self._read_moves(Oware, string, index)

        if 'FEN' in tags:
            notation = tags['FEN']
            board, turn = Oware.to_position(notation)
            match.set_position(board, turn)

        for notation, comment in zip(moves, comments):
            move = Oware.to_move(notation)
            match.add_move(move)
            match.set_comment(comment)

        for name, value in tags.items():
            match.set_tag(name, value)

        return match

    def read_header(self, file, size=None):
        """Reads the OGN header from a file"""

        string = file.read(size)
        tags, index = self._read_tags(string)

        return tags

    def _read_tags(self, string, index=0):
        """Reads all header tags from the string"""

        tags = {}

        while index < len(string):
            m = self._tag_regex.match(string, index)

            if m is None:
                break

            tag = m.group(1)
            value = self._unescape(m.group(2))
            tags[tag] = value
            index = m.end(0)

        return (tags, index)

    def _read_moves(self, game, string, index):
        """Reads all the moves from the string"""

        comments = []
        moves = []

        while index < len(string):
            if string[index] == '{':
                comment, index = self._read_comment(string, index)
                comments[-1] = comment
            elif string[index] == '(':
                variation, index = self._read_variation(string, index)
            else:
                m = self._move_regex.match(string, index)
                if m is not None:
                    notation = m.group(1)
                    comments.append(None)
                    moves.append(notation)
                index += 1

        return (moves, comments, index)

    def _read_comment(self, string, index):
        """Reads a single comment from the string"""

        comment = None

        if index < len(string):
            m = self._comment_regex.match(string, index + 1)

            if m is not None:
                index = m.end(1)
                comment = ' '.join(m.group(1).split())

        return (comment, index)

    def _read_variation(self, string, index):
        """Reads a single comment from the string"""

        variation = None

        if index < len(string):
            m = self._varitation_regex.match(string, index + 1)

            if m is not None:
                variation = m.group(1)
                index = m.end(1)

        return (variation, index)

    def _write_tags(self, match, file):
        """Writes this match tags to a file"""

        tags = dict(match.get_tags())

        for name in match.get_tag_roster():
            value = self._escape(tags[name])
            string = '[%s "%s"]\n' % (name, value)
            file.write(string)

        for name, value in tags.items():
            if name not in match.get_tag_roster():
                value = self._escape(value)
                string = '[%s "%s"]\n' % (name, value)
                file.write(string)

    def _write_moves(self, match, file):
        """Writes moves from a match to a file"""

        tokens = match.get_notation()
        line = str(tokens[0])

        for token in tokens[1:]:
            if 1 + len(line) + len(token) < 80:
                line = '%s %s' % (line, token)
                continue

            file.write('%s\n' % line)
            line = str(token)

        file.write('%s\n' % line)

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
