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


@Gtk.Template(resource_path='/com/joansala/auale/gtk/dialogs/about_dialog.ui')
class AboutDialog(Gtk.AboutDialog):
    """About dialog"""

    __gtype_name__ = 'AboutDialog'

    def __init__(self, window):
        super(AboutDialog, self).__init__()

        self.set_transient_for(window)
        self.connect('delete-event', self.on_delete_event)

    def on_delete_event(self, dialog, event):
        """Hide the dialog when delete is emitted"""

        return self.hide_on_delete()
