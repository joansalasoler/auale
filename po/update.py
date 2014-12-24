#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Aualé oware graphic user interface.
# Copyright (C) 2014 Joan Sala Soler <contact@joansala.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, sys, re
import shutil, subprocess

# Import the util and App modules from the package

sys.path.append(
    '%s/../src/auale/' % os.path.dirname(
        os.path.abspath(__file__)
    )
)

import util
from gui import App

# Configuration options

OUTPUT_FOLDER = 'src/auale/res/messages'
BUGS_ADDRESS = 'contact@joansala.com'

# Update and compile translation files

xgettext = util.which('xgettext')
msgmerge = util.which('msgmerge')
msgfmt = util.which('msgfmt')

if not (xgettext and msgmerge and msgfmt):
    raise Exception("Gettext tools not found")

# Change cwd to the root folder

folder = os.path.dirname(os.path.abspath(__file__))
os.chdir(util.resource_path('%s/../' % folder))

# Update the template file with new strings

print("-- Updating template file.")

command = (
    xgettext,
    '--sort-output',
    '--package-name=%s' % App.NAME,
    '--package-version=%s' % App.VERSION,
    '--output=po/%s.pot' % App.DOMAIN,
    '--msgid-bugs-address=%s' % BUGS_ADDRESS,
    '--files-from=po/POTFILES.in',
)

if subprocess.call(command):
    raise Exception("Cannot update template file")

# Update and format translation files

if os.path.isdir(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)

if os.path.exists(OUTPUT_FOLDER):
    raise Exception("Output folder could not be emptied")

for name in os.listdir('po'):
    match = re.match(r'^([^.]+)[.]po$', name)
    if not match: continue
    code = match.group(1)
    
    print("-- Updating translation: %s." % code)
    
    subprocess.call((
        msgmerge, '--verbose', '--update',
        'po/%s.po' % code,
        'po/%s.pot' % App.DOMAIN
    ))
    
    print("-- Formatting translation: %s." % code)
    
    folder = '%s/%s/LC_MESSAGES/' % (OUTPUT_FOLDER, code)
    os.makedirs(folder)
    
    subprocess.call((
        msgfmt, '--verbose', '--check',
        '--output-file=%s/%s.mo' % (folder, App.DOMAIN),
        'po/%s.po' % code
    ))
