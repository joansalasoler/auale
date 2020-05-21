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

import subprocess

from .client import Client
from .strength import Strength


class Engine(Client):
    """Client for an external UCI engine"""

    __counter = 0
    __quit_timeout = 8.0

    def __init__(self, command):
        process = self._create_process(command)
        Client.__init__(self, process.stdout, process.stdin)
        Engine.__counter += 1

        self._id = Engine.__counter
        self._process = process
        self._strength = Strength.EASY
        self._author = 'Unknown author'
        self._name = 'Unknown engine'
        self.connect('id-received', self._on_id_received)
        self.connect('response-timeout', self._on_response_timeout)
        self.connect('termination', self._on_termination)
        self.start()

    def get_player_name(self):
        """Returns this engine name"""

        return self._name

    def get_author_name(self):
        """Returns this engine's author"""

        return self._author

    def get_playing_strength(self):
        """Returns the current playing strength"""

        return self._strength

    def set_playing_strength(self, strength):
        """Configures the strength of the engine"""

        self.set_search_depth(strength.search_depth)
        self.set_search_timeout(strength.search_timeout)
        self._strength = strength

    def _on_id_received(self, client, args):
        """Listens for identification messages"""

        if isinstance(args['author'], str):
            self._author = args['author']

        if isinstance(args['name'], str):
            self._name = args['name']

    def _on_response_timeout(self, client, command):
        """Listens for response timeouts"""

        if self._process.poll() is None:
            self.emit('failure', 'Response timeout')
            self._terminate_process()

    def _on_termination(self, client):
        """Listens for the client to terminate"""

        try:
            self._process.wait(self.__quit_timeout)
        except subprocess.TimeoutExpired:
            self.emit('failure', 'Quit timeout')
            self._terminate_process()

    def _create_process(self, command):
        """Creates an engine subprocess"""

        startupinfo = None

        # Required if the OS is Windows

        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Create and return the engine subprocess

        return subprocess.Popen(
            command,
            bufsize=1,
            startupinfo=startupinfo,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True
        )

    def _terminate_process(self):
        """Ensures the engine process is terminated"""

        try:
            self._logger.warning('Terminating engine')
            self._process.terminate()
            self._process.wait(self.__quit_timeout)
        except subprocess.TimeoutExpired:
            self._logger.warning('Killing engine')
            self._process.kill()

    def __repr__(self):
        return '<Engine({0}, {1})>'.format(self._id, self._name)
