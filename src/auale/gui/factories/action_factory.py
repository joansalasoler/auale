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

from gi.repository import Gio
from gi.repository import GLib


class ActionFactory(object):
    """Connect actions to object instances"""

    _BUILDER_METHODS = {
        'property': 'create_property_action',
        'setting':  'create_setting_action',
        'simple':   'create_simple_action',
        'state':    'create_state_action'
    }

    __METHOD_NAMES = {
        'property': 'on_{name}_property_changed',
        'setting':  'on_{name}_setting_changed',
        'simple':   'on_{name}_action_activate',
        'state':    'on_{name}_action_change_state'
    }

    __SIGNAL_NAMES = {
        'property': 'notify',
        'setting':  'notify',
        'simple':   'activate',
        'state':    'change-state'
    }

    def __init__(self, descriptors):
        """Creates a new factory for a configuration"""

        self._descriptors = dict(descriptors)

    def connect(self, target, group_name):
        """Connects the set of configured actions to a target"""

        group_descriptors = self._descriptors[group_name]

        for action_type, params in group_descriptors:
            self.connect_action(target, action_type, params)

    def connect_action(self, target, action_type, params):
        """Creates an action and connects it to a target"""

        builder = self._BUILDER_METHODS[action_type]
        action = getattr(self, builder)(target, *params)
        self.maybe_connect_signal(target, action, action_type)
        target.add_action(action)

    def create_property_action(self, target, name, property_name=None):
        """Creates a new object property action"""

        action = Gio.PropertyAction.new(name, target, property_name or name)

        return action

    def create_setting_action(self, target, name):
        """Creates a new settings action"""

        settings = target.get_local_settings()
        action = settings.create_action(name)

        return action

    def create_simple_action(self, target, name, type_string=None):
        """Creates a new stateless simple action"""

        parameter_type = self.get_variant_type_for_string(type_string)
        action = Gio.SimpleAction.new(name, parameter_type)

        return action

    def create_state_action(self, target, name, state_string, type_string=None):
        """Creates a new stateful simple action"""

        state = self.get_variant_for_string(state_string)
        parameter_type = self.get_variant_type_for_string(type_string)
        action = Gio.SimpleAction.new_stateful(name, parameter_type, state)

        return action

    def maybe_connect_signal(self, target, action, action_type):
        """Connects an action signal if a method for it exists on target"""

        action_name = action.get_name()
        method_name = self.get_method_name(action_type, action_name)
        signal_name = self.get_signal_name(action_type, action_name)

        if hasattr(target, method_name):
            callback = getattr(target, method_name)
            action.connect(signal_name, callback)

    def get_variant_for_string(self, state_string):
        """Parses a variant string as a variant value"""

        return GLib.Variant.parse(None, state_string, None, None)

    def get_variant_type_for_string(self, type_string):
        """Parses a variant type string as a variant type"""

        return type_string and GLib.VariantType.new(type_string)

    def get_method_name(self, action_type, action_name):
        """Obtains a suitable method name for an action"""

        action_id = action_name.replace('-', '_')
        method_name = self.__METHOD_NAMES[action_type]

        return method_name.format(name=action_id)

    def get_signal_name(self, action_type, action_name):
        """Obtains a suitable signal name for an action"""

        return self.__SIGNAL_NAMES[action_type]
