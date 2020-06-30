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

import logging

from collections import namedtuple
from gi.repository import Manette
from .control import Control

Mapping = namedtuple('Mapping', (
    'control',      # Gamepad control
    'application',  # Target application
    'group',        # Action group name ('app' or 'win')
    'action'        # Action name
))


class ControlManager(object):
    """Maps gamepad controls to actions"""

    def __init__(self):
        self._entries = {}
        self._logger = logging.getLogger('gamepad')
        self._monitor = Manette.Monitor.new()
        self._monitor.connect('device-connected', self.on_device_connected)
        self.connext_devices()

    def connext_devices(self):
        """Connect the existing devices"""

        iterator = self._monitor.iterate()
        has_next, device = iterator.next()

        while has_next:
            self.connect_device(device)
            has_next, device = iterator.next()

    def connect_device(self, device):
        """Connect the required events to a gamepad"""

        device.connect('absolute-axis-event', self.on_absolute_axis_event)
        device.connect('button-press-event', self.on_button_press_event)
        device.connect('hat-axis-event', self.on_hat_axis_event)
        device.connect('disconnected', self.on_device_disconnected)

        self._logger.info(f'Gamepad connected: { device.get_name() }')

    def disconnect_device(self, device):
        """Disconnect all the events from a gamepad"""

        device.disconnect_by_func(self.on_absolute_axis_event)
        device.disconnect_by_func(self.on_button_press_event)
        device.disconnect_by_func(self.on_hat_axis_event)

        self._logger.info(f'Gamepad disconnected: { device.get_name() }')

    def set_controls_for_action(self, target, action, controls):
        """Set the gamepad controls that trigger an action"""

        for name in controls:
            control = Control.value_of(name)
            mapping = Mapping(control, target, *action.split('.'))
            entry = self._entries.setdefault(control.code, [])
            entry.append(mapping)

    def get_action_target(self, entry):
        """Obtains the target object for the given entry"""

        group = entry.group
        application = entry.application
        window = application.get_active_window()
        is_active = window and window.is_active()
        target = window if group == 'win' else application

        return target if is_active else None

    def on_device_connected(self, manager, device):
        """Emitted when a new gamepad is connected"""

        self.connect_device(device)

    def on_device_disconnected(self, device):
        """Emitted when a gamepad is disconnected"""

        self.disconnect_device(device)

    def on_button_press_event(self, device, event):
        """Emitted on a gamepad button press"""

        retrieved, code = event.get_button()

        if retrieved and code in self._entries:
            for entry in self._entries[code]:
                target = self.get_action_target(entry)
                target and target.activate_action(entry.action)

    def on_absolute_axis_event(self, device, event):
        """Emitted on a gamepad absolute axis events"""

        retrieved, code, direction = event.get_absolute()

        if retrieved and code in self._entries:
            for entry in self._entries[code]:
                if direction == entry.control.direction:
                    target = self.get_action_target(entry)
                    target and target.activate_action(entry.action)

    def on_hat_axis_event(self, device, event):
        """Emitted on a gamepad hat axis events"""

        retrieved, code, direction = event.get_hat()

        if retrieved and code in self._entries:
            for entry in self._entries[code]:
                if direction == entry.control.direction:
                    target = self.get_action_target(entry)
                    target and target.activate_action(entry.action)
