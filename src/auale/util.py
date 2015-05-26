#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some methods provided here were copied, for convenience, from the standard
Python 3 module library. Please, see the Python distribution for licensing
information.
"""

import os, sys
import gettext
import locale

__MESSAGES_PATH = './res/messages/'


def _which(cmd, mode=os.F_OK | os.X_OK, path=None):
    """Given a command, mode, and a PATH string, return the path which
    conforms to the given mode on the PATH, or None if there is no such
    file.

    `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
    of os.environ.get("PATH"), or can be overridden with a custom search
    path.

    """
    # Check that a given file can be accessed with the correct mode.
    # Additionally check that `file` is not a directory, as on Windows
    # directories pass the os.access check.
    def _access_check(fn, mode):
        return (os.path.exists(fn) and os.access(fn, mode)
                and not os.path.isdir(fn))

    # If we're given a path with a directory part, look it up directly rather
    # than referring to PATH directories. This includes checking relative to the
    # current directory, e.g. ./script
    if os.path.dirname(cmd):
        if _access_check(cmd, mode):
            return cmd
        return None

    if path is None:
        path = os.environ.get("PATH", os.defpath)
    if not path:
        return None
    path = path.split(os.pathsep)

    if sys.platform == "win32":
        # The current directory takes precedence on Windows.
        if not os.curdir in path:
            path.insert(0, os.curdir)

        # PATHEXT is necessary to check on Windows.
        pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
        # See if the given file matches any of the expected path extensions.
        # This will allow us to short circuit when given "python.exe".
        # If it does match, only test that one, otherwise we have to try
        # others.
        if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
            files = [cmd]
        else:
            files = [cmd + ext for ext in pathext]
    else:
        # On other platforms you don't have things like PATHEXT to tell you
        # what file suffixes are executable, so just pass on cmd as-is.
        files = [cmd]

    seen = set()
    for dir in path:
        normdir = os.path.normcase(dir)
        if not normdir in seen:
            seen.add(normdir)
            for thefile in files:
                name = os.path.join(dir, thefile)
                if _access_check(name, mode):
                    return name
    return None


def resource_path(path):
    """Returns an absolute path for the given resource file"""
    
    # Obtain this module's path
    
    file = os.path.abspath(__file__)
    folder = os.path.dirname(file)
    
    # This module may be in a compressed file
    
    if os.path.isfile(folder):
        folder = os.path.dirname(folder)
    
    return os.path.normcase(
        os.path.realpath(os.path.join(folder, path)))


def install_gettext(domain):
    """Sets the text domain and installs it"""
    
    # LANG must be set on some platforms (e.g. Windows)
    
    if 'LANG' not in os.environ:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANG'] = lang
    
    # Use the standard system path for messages if possible,
    # otherwise default to __MESSAGES_PATH
    
    path = None
    
    if not gettext.find(domain):
        path = resource_path(__MESSAGES_PATH)
    
    # Set text domain for Python code
    
    gettext.bindtextdomain(domain, path)
    gettext.textdomain(domain)
    
    # Set text domain for non Python code. On Windows 'libintl'
    # must be loaded to do so
    
    if hasattr(locale, 'bindtextdomain'):
        locale.bindtextdomain(domain, path)
    else:
        from ctypes import cdll
        intl = cdll.LoadLibrary('libintl-8.dll')
        intl.bind_textdomain_codeset(domain, 'UTF-8')
        intl.bindtextdomain(domain, path)
    
    # Install gettext's _() method in __builtins__
    
    gettext.install(domain, path, codeset = 'utf-8')


# With Python 3 use shutil

try:
    import shutil
    
    if hasattr(shutil, 'which'):
        which = shutil.which
    else:
        which = _which
except:
    which = _which

