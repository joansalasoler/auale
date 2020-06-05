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


class RequestOverwriteDialog(Gtk.MessageDialog):
    """A dialog to request stroing the current match"""

    __gtype_name__ = 'RequestOverwriteDialog'

    def __init__(self, window):
        super(RequestOverwriteDialog, self).__init__()

        self.set_modal(True)
        self.set_title(_('Match changed on disk'))

        self.add_button(_('Save anyway'), Gtk.ResponseType.ACCEPT)
        self.add_button(_('Don\'t save'), Gtk.ResponseType.REJECT)

        self.set_property('message-type', Gtk.MessageType.WARNING)
        self.set_property('text', _('The file was modified by another program'))
        self.set_property('secondary_text', _('Do you really want to overwrite it?'))

        self.set_transient_for(window)

    def confirm(self):
        """Runs the dialog and then hides it"""

        response = self.run()
        self.hide()

        return response
