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

from gi.repository import GLib


class OptionFactory(object):
    """Connect command line options to an application"""

    __TYPES = {
        '&s':    GLib.OptionArg.STRING,
        '^&ay':  GLib.OptionArg.FILENAME,
        '^a&ay': GLib.OptionArg.FILENAME_ARRAY,
        '^a&s':  GLib.OptionArg.STRING_ARRAY,
        'b':     GLib.OptionArg.NONE,
        'd':     GLib.OptionArg.DOUBLE,
        'i':     GLib.OptionArg.INT,
        'x':     GLib.OptionArg.INT64
    }

    def __init__(self, descriptors):
        """Creates a new factory for a configuration"""

        self._descriptors = descriptors

    def connect(self, target):
        """Connects the set of configured options to a target"""

        for action_name, params in self._descriptors:
            self.connect_option(target, action_name, params)

    def connect_option(self, target, action_name, params):
        """Creates an option and adds it to a target"""

        option = self.create_option_entry(action_name, *params)
        target.add_main_option_entries((option,))

    def create_option_entry(self, name, text, type_name=None, type_string='b'):
        """Creates a new command line option entry"""

        option = GLib.OptionEntry()

        option.arg = self.get_type_for_variant_string(type_string)
        option.arg_description = type_name
        option.description = text
        option.long_name = name
        option.short_name = 0

        return option

    def get_type_for_variant_string(self, type_string):
        """Obtains a suitable option type for a variant type"""

        return self.__TYPES[type_string]
