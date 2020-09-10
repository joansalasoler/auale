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
import logging
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
    __DEFAULT_COMMAND = '[default]'

    def __init__(self):
        GObject.GObject.__init__(self)

        self._logger = logging.getLogger('uci')
        self._engine_command = self.__DEFAULT_COMMAND
        self._engine_strength = Strength.EASY
        self._engine_side = Side.NORTH
        self._human_player = None
        self._south_engine = None
        self._north_engine = None

    @GObject.Signal
    def engine_start_error(self, error: object):
        """Emitted if the engine could not be started"""

    @GObject.Signal
    def engine_failure_error(self, reason: str):
        """Emitted on engine malfunctions"""

    def get_human_player(self):
        """Gets the human player"""

        return self._human_player

    def get_engine_player(self):
        """Gets the main engine player"""

        return self._south_engine

    def get_engine_strength(self):
        """Gets the engine strength"""

        return self._engine_strength

    def get_engine_side(self):
        """Gets the side on which the engine is playing"""

        return self._engine_side

    def get_north_player(self):
        """Gets the north player"""

        human = self._human_player
        engine = self._south_engine
        is_engine = self._engine_side.is_north
        north_player = engine if is_engine else human

        return north_player

    def get_south_player(self):
        """Gets the south player"""

        human = self._human_player
        engine = self._north_engine
        is_engine = self._engine_side.is_south
        south_player = engine if is_engine else human

        return south_player

    def get_player_for_turn(self, match):
        """Gets the player to move for the given match"""

        game = match.get_game()
        north_player = self.get_north_player()
        south_player = self.get_south_player()
        is_south_turn = match.get_turn() == game.SOUTH
        player = south_player if is_south_turn else north_player

        return player

    def set_engine_strength(self, strength):
        """Sets the engine strength"""

        try:
            self._engine_strength = strength
            self._south_engine.set_playing_strength(strength)
            self._north_engine.set_playing_strength(strength)
        except BaseException:
            self._logger.warning('Could not set engine strength')

    def set_engine_side(self, side):
        """Sets the side on which the engine is playing"""

        self._engine_side = side

    def set_engine_command(self, command):
        """Sets a custom engine command to use"""

        value = command or self.__DEFAULT_COMMAND
        self._engine_command = value.strip()
        self._logger.debug(f'Engine command: { self._engine_command }')

    def on_engine_failure(self, engine, reason):
        """Handle engine termination errors"""

        self._south_engine.quit()
        self._north_engine.quit()
        self._south_engine = Human()
        self._north_engine = Human()
        self._logger.warning(reason)
        self.engine_failure_error.emit(reason)

    def start_players(self):
        """Starts the player processes"""

        self._south_engine = self._create_engine()
        self._north_engine = self._create_engine()
        self._human_player = Human()

    def quit_players(self):
        """Quits all the running players"""

        self._south_engine.quit()
        self._north_engine.quit()
        self._human_player.quit()

    def _create_engine(self):
        """Creates a new engine player"""

        try:
            custom = self._get_custom_command()
            default = self._get_default_command()
            command = custom if self._has_custom_command() else default
            engine = self._create_engine_for_command(command)
        except BaseException as error:
            self._logger.warning(f'Could not start engine')
            self.engine_start_error.emit(error)
            engine = Human()

        return engine

    def _create_engine_for_command(self, command):
        """Create an engine player for the given command"""

        engine = Engine(command)
        engine.connect('failure', self.on_engine_failure)

        return engine

    def _has_custom_command(self):
        """Checks if a custom engine command was set"""

        command = self._engine_command
        is_custom = command != self.__DEFAULT_COMMAND

        return is_custom

    def _get_custom_command(self):
        """Get a command to run a custom engine"""

        command = self._engine_command.split()
        command = (shutil.which(command[0]), *command[1:])

        return command

    def _get_default_command(self):
        """Get a command to run the default engine"""

        file_path = os.path.dirname(__file__)
        base_path = os.path.abspath(os.path.join(file_path, os.pardir))
        engine_path = os.path.join(base_path, self.__DEFAULT_ENGINE_PATH)
        command = (shutil.which('java'), '-jar', engine_path)

        return command
