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

from gi.repository import Gtk
from ..filters import OGNFileFilter


class MatchChooserDialog(Gtk.FileChooserDialog):
    """A file chooser for oware match files"""

    __gtype_name__ = 'MatchChooserDialog'

    def __init__(self, window):
        super(MatchChooserDialog, self).__init__()

        self.add_filter(OGNFileFilter())
        self.connect('response', self.on_response)
        self.set_transient_for(window)
        self.set_modal(True)

    def on_response(self, dialog, response):
        """Hide the dialog when a response is emitted"""

        self.hide()

    def add_cancel_button(self, label):
        """Adds a cancel button to the dialog"""

        response = Gtk.ResponseType.CANCEL
        button = self._create_action_button(label)

        self.add_action_widget(button, response)

    def add_accept_button(self, label):
        """Adds an accept button to the dialog"""

        response = Gtk.ResponseType.ACCEPT
        button = self._create_action_button(label)
        styles = button.get_style_context()
        styles.add_class('suggested-action')

        self.add_action_widget(button, response)

    def _create_action_button(self, label):
        """Adds an action button to the dialog"""

        button = Gtk.Button(label)
        button.set_visible(True)
        button.set_can_default(True)

        return button
