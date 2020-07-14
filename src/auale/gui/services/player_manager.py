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

import os
import shutil
from gi.repository import GObject

from uci import Engine
from uci import Human
from uci import Strength
from ..values import Side


class PlayerManager(GObject.GObject):
    """Service to manage match players"""

    __gtype_name__ = 'PlayerManager'
    __DEFAULT_ENGINE_PATH = '../data/engine/Aalina.jar'

    def __init__(self):
        GObject.GObject.__init__(self)

        self._command = None
        self._human = Human()
        self._engine = self._create_engine()
        self._south = self._human
        self._north = self._engine
        self._engine_strength = Strength.EASY
        self._engine_side = Side.NORTH

    def get_engine(self):
        """Gets an engine player"""

        return self._engine

    def get_south(self):
        """Gets the south player"""

        return self._south

    def get_north(self):
        """Gets the north player"""

        return self._north

    def set_south(self, player):
        """Sets the south player"""

        self._south = player

    def set_north(self, player):
        """Sets the north player"""

        self._north = player

    def get_engine_strength(self):
        """Gets the engine strength"""

        return self._engine_strength

    def set_engine_strength(self, strength):
        """Sets the engine strength"""

        self._engine_strength = strength
        self._engine.set_playing_strength(strength)

    def get_engine_side(self, side):
        """Gets the side on which the engine is playing"""

        return self._engine_side

    def set_engine_side(self, side):
        """Sets the side on which the engine is playing"""

        self._engine_side = side

    def get_engine_command(self):
        """Gets the custom engine command if any"""

        return self._command

    def set_engine_command(self, command):
        """Sets a custom engine command to use"""

        self._command = command

    def has_custom_command(self):
        """Checks if a custom engine command was set"""

        return self._command is not None

    def engine_is_enabled(self):
        """Checks if the engine player is enabled"""

        return isinstance(self._engine, Engine)

    def on_engine_failure(self, engine, reason):
        """Handle engine termination errors"""

        if engine == self._engine:
            self._engine = Human()

        if engine == self._south:
            self._south = self._human

        if engine == self._north:
            self._north = self._human

    def quit_engines(self):
        """Quits any running engine players"""

        self._engine.quit()
        self._north.quit()
        self._south.quit()

    def _create_engine(self):
        """Creates a new engine player"""

        try:
            custom = self._get_custom_command()
            default = self._get_default_command()
            command = custom if self.has_custom_command() else default
            engine = self._create_engine_for_command(command)
        except BaseException:
            engine = Human()

        return engine

    def _create_engine_for_command(self, command):
        """Create an engine player for the given command"""

        engine = Engine(command)
        engine.connect('failure', self.on_engine_failure)

        return engine

    def _get_custom_command(self):
        """Get a command to run a custom engine"""

        command = self._command.split() if self._command else ['']
        command = (shutil.which(command[0]),)

        return command

    def _get_default_command(self):
        """Get a command to run the default engine"""

        file_path = os.path.dirname(__file__)
        base_path = os.path.abspath(os.path.join(file_path, os.pardir))
        engine_path = os.path.join(base_path, self.__DEFAULT_ENGINE_PATH)
        command = (shutil.which('java'), '-jar', engine_path)

        return command
