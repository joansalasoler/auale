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

import locale
import sys

# On the Windows platform 'libintl' must loaded to enable gettext
# support for the application. This module ensures that the correct
# gettext library is loaded and can be imported by othe modules.

module = locale

if 'win' in sys.platform:
    if not hasattr(locale, 'bindtextdomain'):
        from ctypes import cdll
        module = cdll.LoadLibrary('libintl-8.dll')

gettext = module.gettext
