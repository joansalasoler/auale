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
from .match_chooser_dialog import MatchChooserDialog
from ..filters import AnyFileFilter


class OpenMatchDialog(MatchChooserDialog):
    """A file chooser to open an oware match"""

    __gtype_name__ = 'OpenMatchDialog'

    def __init__(self, window):
        super(OpenMatchDialog, self).__init__(window)

        self.set_title(_('Open an oware match'))
        self.add_cancel_button(_('Cancel'))
        self.add_accept_button(_('Open match'))

        self.set_action(Gtk.FileChooserAction.OPEN)
        self.add_filter(AnyFileFilter())
