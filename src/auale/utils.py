#!/usr/bin/env python
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

import os
import sys
import locale
import builtins

from gi.repository import Gio


class Utils(object):

    __LOCALE_PATH = './res/locale/'
    __SCHEMAS_PATH = './res/schemas/'

    @staticmethod
    def resource_path(path):
        """Returns an absolute path for the given resource file"""

        # Obtain this module's path

        file = os.path.abspath(__file__)
        folder = os.path.dirname(file)

        # This module may be in a compressed file

        if os.path.isfile(folder):
            folder = os.path.dirname(folder)

        result = os.path.join(folder, path)
        result = os.path.realpath(result)
        result = os.path.normcase(result)

        return result

    @staticmethod
    def get_gettext_module():
        """Obtains the gettext library to use"""

        # On Windows we load the intl library if the locale
        # module does not have support for gettext

        if not hasattr(locale, 'bindtextdomain'):
            from ctypes import cdll
            return cdll.LoadLibrary('libintl-8.dll')

        return locale

    @staticmethod
    def install_gettext(domain):
        """Sets the text domain and installs it"""

        gettext = Utils.get_gettext_module()

        # Ensures LANG environment is set

        if 'LANG' not in os.environ or not os.environ['LANG']:
            lang, enc = gettext.getdefaultlocale()
            os.environ['LANG'] = lang

        # Ensures LOCPATH environment is set

        if 'LOCPATH' not in os.environ or not os.environ['LOCPATH']:
            path = Utils.resource_path(Utils.__LOCALE_PATH)

            if not os.path.isdir(path):
                path = '%s/share/locale' % sys.base_prefix

            os.environ['LOCPATH'] = path

        # Binds the text domain and adds a _() method

        path = os.environ['LOCPATH']
        gettext.bind_textdomain_codeset(domain, 'utf-8')
        gettext.bindtextdomain(domain, path)
        gettext.textdomain(domain)
        builtins._ = gettext.gettext

    @staticmethod
    def get_gio_settings(schema_id):
        """
        Returns a Gio.Settings object for the specified schema. This method
        instantiates the object using the default source if the schema is
        installed on the system, otherwise, it fallsback to a local folder
        """

        # Read setting from the default source if available

        if schema_id in Gio.Settings.list_schemas():
            return Gio.Settings(schema_id)

        # Fallback to a local application folder

        path = Utils.resource_path(Utils.__SCHEMAS_PATH)
        gss = Gio.SettingsSchemaSource
        default_source = gss.get_default()
        source = gss.new_from_directory(path, default_source, False)
        schema = source.lookup(schema_id, False)

        return Gio.Settings.new_full(schema, None, None)
