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


@Gtk.Template(resource_path='/com/joansala/auale/gtk/dialogs/scoresheet_dialog.ui')
class ScoresheetDialog(Gtk.Dialog):
    """Match scoresheet dialog"""

    __gtype_name__ = 'ScoresheetDialog'

    def __init__(self):
        super(ScoresheetDialog, self).__init__()
