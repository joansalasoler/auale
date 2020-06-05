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
from i18n import gettext as _


class RequestSaveDialog(Gtk.MessageDialog):
    """A dialog to request stroing the current match"""

    __gtype_name__ = 'RequestSaveDialog'

    def __init__(self, window):
        super(RequestSaveDialog, self).__init__()

        self.set_modal(True)
        self.set_title(_('Match with unsaved changes'))

        self.add_button(_('Discard unsaved changes'), Gtk.ResponseType.ACCEPT)
        self.add_button(_('Cancel'), Gtk.ResponseType.CANCEL)
        self.add_button(_('Save'), Gtk.ResponseType.REJECT)

        self.set_property('message-type', Gtk.MessageType.QUESTION)
        self.set_property('text', _('Do you want to save the current match?'))
        self.set_property('secondary_text', _('Your changes will be lost if you don\'t save them.'))

        self.set_transient_for(window)

    def confirm(self):
        """Runs the dialog and then hides it"""

        response = self.run()
        self.hide()

        return response
