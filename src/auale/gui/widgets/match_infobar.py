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
from gi.repository import Gtk
from gi.repository import Pango
from i18n import gettext as _


class MatchInfobar(Gtk.InfoBar):
    """An infobar that shows information about a match"""

    __gtype_name__ = 'MatchInfobar'
    __icon_size = Gtk.IconSize.LARGE_TOOLBAR

    def __init__(self):
        super(MatchInfobar, self).__init__()

        self._image = Gtk.Image()
        self._label = Gtk.Label()
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self.set_message_type(Gtk.MessageType.OTHER)
        self.set_property('height-request', 40)
        self.set_valign(Gtk.Align.START)

        content_area = self.get_content_area()
        content_area.add(self._image)
        content_area.add(self._label)

    def show_file_message(self, markup):
        """Show a message about a match file"""

        self._show_message('match-file', markup)

    def show_help_message(self, markup):
        """Show a help message about"""

        self._show_message('match-help', markup)

    def show_comment_message(self, markup):
        """Show a comment on a match positon"""

        self._show_message('match-comment', markup)

    def show_error_message(self, markup):
        """Show an error message"""

        self._show_message('match-error', markup)

    def show_match_comment(self, match):
        """Show the comment for the current match position"""

        comment = match.get_comment() or ''
        text = GLib.markup_escape_text(comment)

        self.show_comment_message(text)

    def show_match_information(self, match):
        """Show information about a match file"""

        event = self._escape_match_tag(match, 'Event')
        south = self._escape_match_tag(match, 'South')
        north = self._escape_match_tag(match, 'North')
        result = self._escape_match_tag(match, 'Result')

        title = event or _('Match')
        players = f'{ south } vs. { north }'
        scores = result != '*' and f' ({ result })' or ''
        message = f'<b>{ title }</b>: { players }{ scores }'

        self.show_file_message(message)

    def _show_message(self, icon_name, markup):
        """Show an message with a custom icon"""

        icon = Gio.content_type_get_symbolic_icon(icon_name)
        self._image.set_from_gicon(icon, self.__icon_size)
        self._label.set_markup(markup)

    def _escape_match_tag(self, match, tag_name):
        """Returns an escaped tag markup or none if the tag is empty"""

        tag = match.get_tag(tag_name)
        value = tag and GLib.markup_escape_text(tag)

        return value
