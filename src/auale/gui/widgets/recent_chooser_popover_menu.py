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
from gi.repository import Gtk

from . import RecentChooserMenuitem
from ..filters import OGNRecentFilter


@Gtk.Template.from_file('gui/widgets/recent_chooser_popover_menu.ui')
class RecentChooserPopoverMenu(Gtk.Bin):
    """A recent chooser widget that can be used on a popover"""

    __gtype_name__ = 'RecentChooserPopoverMenu'

    __MAX_ITEMS = 20

    __FILTER_FLAGS = (
        ('age', Gtk.RecentFilterFlags.AGE),
        ('display_name', Gtk.RecentFilterFlags.DISPLAY_NAME),
        ('mime_type', Gtk.RecentFilterFlags.MIME_TYPE),
        ('uri', Gtk.RecentFilterFlags.URI)
    )

    _manager = Gtk.RecentManager()
    _container = Gtk.Template.Child('container')

    def __init__(self, **kwargs):
        super(RecentChooserPopoverMenu, self).__init__(**kwargs)

        self._action_name = None
        self._filter = OGNRecentFilter()
        self._container.connect('map', self.on_container_map, self._manager)

    def get_action_name(self):
        """Gets the action associated with the menu"""

        return self._action_name

    def set_action_name(self, name):
        """Sets the action associated with the menu"""

        self._action_name = name

        for menuitem in self._container.get_children():
            menuitem.set_action_name(name)

    def on_container_map(self, container, manager):
        """Rebuild the menu each time it is mapped"""

        for child in container.get_children():
            container.remove(child)

        for item in manager.get_items()[:self.__MAX_ITEMS]:
            info = self.create_recent_filter_info(item)

            if self._filter.filter(info) and item.exists():
                menuitem = self.create_menuitem(item)
                button = menuitem.get_child()
                menuitem.connect('focus', self.on_menuitem_focus)
                button.connect('clicked', self.on_menuitem_clicked)
                container.add(menuitem)

        window = self.get_child()
        adjustment = window.get_vadjustment()
        adjustment.set_value(0)

    def on_menuitem_clicked(self, menuitem):
        """Hides the popover when a menuitem is activated"""

        popover = menuitem.get_ancestor(Gtk.Popover)

        if isinstance(popover, Gtk.Popover):
            popover.hide()

    def on_menuitem_focus(self, menuitem, direction):
        """Ensures the focused menuitem is visible"""

        window = self.get_child()
        window_height = window.get_allocated_height()
        adjustment = window.get_vadjustment()
        allocation = menuitem.get_allocation()

        top = allocation.y
        bottom = top + allocation.height
        scroll_top = adjustment.get_value()

        if top < scroll_top:
            adjustment.set_value(top)
        elif bottom > window_height + scroll_top:
            adjustment.set_value(bottom - window_height)

    def create_menuitem(self, item):
        """Creates a new menuitem for the menu"""

        menuitem = RecentChooserMenuitem()

        uri = item.get_uri()
        name = item.get_display_name()
        mime_type = item.get_mime_type()
        tooltip = item.get_uri_display()
        icon = Gio.content_type_get_symbolic_icon(mime_type)

        menuitem.set_from_gicon(icon)
        menuitem.set_display_name(name)
        menuitem.set_tooltip_text(tooltip)

        menuitem.set_can_default(True)
        menuitem.set_action_target_value(uri)
        menuitem.set_action_name(self.get_action_name())

        return menuitem

    def create_recent_filter_info(self, item):
        """Maps a recent info item to a recent filter info item"""

        info = Gtk.RecentFilterInfo()

        for name, flag in self.__FILTER_FLAGS:
            info.contains |= flag
            method = f'get_{ name }'
            value = getattr(item, method)()
            setattr(info, name, value)

        return info
