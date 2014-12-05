#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Aualé oware graphic user interface.
Copyright (C) 2014 Joan Sala Soler <contact@joansala.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
 
import os, sys
import argparse
import util

from gui import App, GTKView


def __(message):
    """Return an unicode translation as a string"""
    
    return _(message).encode('utf-8')


def parse_arguments():
    """Initializes the arguments parser"""
    
    parser = argparse.ArgumentParser(
        description = __("A graphical user interface for oware")
    )
    
    parser.add_argument(
        '-v', '--version', action = 'version',
        version = '%s %s' % (App.NAME, App.VERSION),
        help = __("show program's version number and exit")
    )
    
    parser.add_argument(
        'filepath', action = 'store', nargs = '?',
        default = None,
        type = str,
        help = __("a match file to open on startup"),
        metavar = __("match_file")
    )
    
    return parser.parse_args()
    

if __name__ == "__main__":
    util.install_gettext(App.DOMAIN)
    args = parse_arguments()
    
    if args.filepath is not None:
        args.filepath = os.path.abspath(
            os.path.normcase(args.filepath)
        )
    
    view = GTKView(args.filepath)

