# -*- coding: utf-8 -*-
"""Centralized pyRevit configuration access for the pyArchitect extension.

Use :func:`get_option` for extension-wide settings stored in pyRevit's shared
configuration.  Feature-specific settings that belong in their own file use the
``data_*`` functions, which open that file through pyRevit as well.

Storage, INI parsing and option encoding are all pyRevit's; this module only
picks the right entry point for the running version and keeps the extension's
call sites stable.  pyRevit 6 and 7 differ in three places:

* A standalone settings file is opened with ``open_config_file`` on pyRevit 7
  and with ``PyRevitConfigParser`` on pyRevit 6.  Both hand back an object with
  the same ``has_section``/``add_section``/``get_section`` surface that
  ``user_config`` itself has, so everything past that point is shared.
* ``get_option(name, default)`` returns the default for a missing option on
  pyRevit 7, but raises on pyRevit 6 whenever that default is ``None``.  Reads
  here always pass a private sentinel and map it back afterwards.
* Option names starting with an underscore stay reserved: pyRevit 6 routes
  those to the section object's own attributes rather than to the file.
"""

import json
import os

import pyrevit
from pyrevit import script
from pyrevit.coreutils import appdata
from pyrevit.userconfig import user_config


SECTION = "pyArchitect"

_MISSING = object()
_LEGACY_JSON_PREFIX = "__pyarchitect_json__:"


def user_data_path(*parts):
    """Build a path inside the per-user pyArchitect data folder.

    Rooted at pyRevit's own roaming folder so an all-users or portable install
    resolves the way pyRevit resolves it.
    """
    return os.path.join(pyrevit.PYREVIT_APP_DIR, "pyArchitect", *parts)


def _section(container, section_name, create=False):
    """Return a named section from any pyRevit config container.

    Works against ``user_config``, a pyRevit 7 ``ConfigSections`` and a
    pyRevit 6 ``PyRevitConfigParser`` alike.  Returns None for a missing
    section when ``create`` is False.
    """
    if container.has_section(section_name):
        return container.get_section(section_name)
    return container.add_section(section_name) if create else None


def _read(section, name, default):
    """Read one option, normalising the pyRevit 6 and 7 miss behaviours."""
    value = section.get_option(name, _MISSING)
    if value is _MISSING:
        return default
    return _decode_legacy(value)


def _decode_legacy(value):
    """Decode values pyArchitect wrote before it used pyRevit's own encoder."""
    if hasattr(value, "startswith") and value.startswith(_LEGACY_JSON_PREFIX):
        try:
            return json.loads(value[len(_LEGACY_JSON_PREFIX) :])
        except ValueError:
            return value
    return value


def get_settings():
    """Return the extension-wide configuration section, creating it if needed."""
    return _section(user_config, SECTION, create=True)


def get_option(name, default=None):
    """Read an extension-wide setting from pyRevit's shared config."""
    return _read(get_settings(), name, default)


def set_option(name, value):
    """Save an extension-wide setting to pyRevit's shared config."""
    get_settings().set_option(name, value)
    script.save_config()


def data_file_path(file_id, file_ext="ini"):
    """Return a pyRevit universal data-file path for a feature."""
    return appdata.get_universal_data_file(file_id, file_ext)


def _open_data_file(file_id, file_ext):
    """Open a feature settings file through pyRevit's own config parser.

    Returns a ``(container, save)`` pair.
    """
    path = data_file_path(file_id, file_ext)
    try:
        from pyrevit.coreutils.configparser import open_config_file
    except ImportError:
        from pyrevit.coreutils.configparser import PyRevitConfigParser

        parser = PyRevitConfigParser(path if os.path.isfile(path) else None)
        return parser, lambda: parser.save(path)
    sections = open_config_file(path)
    return sections, sections.save


def get_data_option(file_id, section_name, name, default=None, file_ext="ini"):
    """Read a setting from a feature-specific pyRevit data file."""
    container, _ = _open_data_file(file_id, file_ext)
    section = _section(container, section_name)
    return _read(section, name, default) if section else default


def set_data_option(file_id, section_name, name, value, file_ext="ini"):
    """Save a setting to a feature-specific pyRevit data file."""
    container, save = _open_data_file(file_id, file_ext)
    _section(container, section_name, create=True).set_option(name, value)
    save()
