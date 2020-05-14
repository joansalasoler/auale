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

import re

class Parser(object):
    """Parses commands into plain dictionaries."""

    def __init__(self, rules):
        self._skip = r'\S*'
        self._stop = r'(?:\s+|$)'
        self._patterns = self._compile_rules(rules)

    def parse(self, line):
        """Converts a string into a dictionary of values"""

        haystack = line.split('\n', 1)[0]
        haystack = haystack.strip()

        for pattern in self._patterns:
            if match := pattern.match(haystack):
                return match.groupdict()

    def _compile_rules(self, rules=()):
        """Compiles a set of command rules as regular expressions"""

        return tuple(self._compile(*rule) for rule in rules)

    def _compile(self, pattern, childs=()):
        """Builds a rule and compiles it into a regular expression"""

        group = '|'.join(childs + (self._skip,))
        arguments = f'(?:(?:{ group }){ self._stop })*'
        regex = f'{ pattern }{ arguments }'

        return re.compile(regex)
