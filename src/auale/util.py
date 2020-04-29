# -*- coding: utf-8 -*-

"""
Some methods provided here were copied, for convenience, from the standard
Python 3 module library. Please, see the Python distribution for licensing
information.
"""

import os
import sys
import locale
import builtins

from gi.repository import Gio

__LOCALE_PATH = './res/locale/'
__SCHEMAS_PATH = './res/schemas/'


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


def get_gettext_module():
    """Obtains the gettext library to use"""

    # On Windows we load the intl library if the locale
    # module does not have support for gettext

    if not hasattr(locale, 'bindtextdomain'):
        from ctypes import cdll
        return cdll.LoadLibrary('libintl-8.dll')

    return locale


def install_gettext(domain):
    """Sets the text domain and installs it"""

    gettext = get_gettext_module()

    # Ensures LANG environment is set

    if 'LANG' not in os.environ or not os.environ['LANG']:
        lang, enc = gettext.getdefaultlocale()
        os.environ['LANG'] = lang

    # Ensures LOCPATH environment is set

    if 'LOCPATH' not in os.environ or not os.environ['LOCPATH']:
        path = resource_path(__LOCALE_PATH)

        if not os.path.isdir(path):
            path = '%s/share/locale' % sys.base_prefix

        os.environ['LOCPATH'] = path

    # Binds the text domain and adds a _() method

    path = os.environ['LOCPATH']
    gettext.bind_textdomain_codeset(domain, 'utf-8')
    gettext.bindtextdomain(domain, path)
    gettext.textdomain(domain)
    builtins._ = gettext.gettext


def putenv(varname, value):
    """Sets an environment variable making sure it is encoded as utf-8 if
       the version of Python > 2 (see os.putenv)"""

    try:
        os.putenv(varname, value)
    except TypeError:
        varname = varname.encode('utf-8')
        value = value.encode('utf-8')
        os.putenv(varname, value)


def get_gio_settings(schema_id):
    """Returns a Gio.Settings object for the specified schema. This method
       instantiates the object using the default source if the schema is
       installed on the system, otherwise, it fallsback to a local folder"""

    # Read setting from the default source if available

    if schema_id in Gio.Settings.list_schemas():
        return Gio.Settings(schema_id)

    # Fallback to a local application folder

    path = resource_path(__SCHEMAS_PATH)
    gss = Gio.SettingsSchemaSource
    default_source = gss.get_default()
    source = gss.new_from_directory(path, default_source, False)
    schema = source.lookup(schema_id, False)

    return Gio.Settings.new_full(schema, None, None)


# With Python 3 use shutil

try:
    import shutil

    if hasattr(shutil, 'which'):
        which = shutil.which
    else:
        which = _which
except:
    which = _which
