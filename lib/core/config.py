# -*- coding: utf-8 -*-
"""Centralized pyRevit configuration access for the pyArchitect extension.

The whole extension shares one settings file, ``pyrevit_pyArchitect.ini`` in
pyRevit's universal appdata folder, opened through pyRevit itself.  Each
feature keeps its options in its own section of that file; pass ``section`` to
:func:`get_option` and :func:`set_option` to reach one.  Settings with no
natural owner live in the default ``pyArchitect`` section.

Storage, INI parsing and option encoding are all pyRevit's; this module only
picks the right entry point for the running version and keeps the extension's
call sites stable.  pyRevit 6 and 7 differ in three places:

* The settings file is opened with ``open_config_file`` on pyRevit 7 and with
  ``PyRevitConfigParser`` on pyRevit 6.  Both hand back an object with the same
  ``has_section``/``add_section``/``get_section`` surface, so everything past
  that point is shared.
* ``get_option(name, default)`` returns the default for a missing option on
  pyRevit 7, but raises on pyRevit 6 whenever that default is ``None``.  Reads
  here always pass a private sentinel and map it back afterwards.
* Option names starting with an underscore stay reserved: pyRevit 6 routes
  those to the section object's own attributes rather than to the file.
"""

import json
import os

import pyrevit
from pyrevit.coreutils import appdata
from pyrevit.userconfig import user_config


CONFIG_FILE_ID = "pyArchitect"
SECTION = "pyArchitect"

_MISSING = object()
_LEGACY_JSON_PREFIX = "__pyarchitect_json__:"
_LEGACY_DATA_FILES = {"navis": "pyArchitectNavis"}


def user_data_path(*parts):
    """Build a path inside the per-user pyArchitect data folder.

    Rooted at pyRevit's own roaming folder so an all-users or portable install
    resolves the way pyRevit resolves it.
    """
    return os.path.join(pyrevit.PYREVIT_APP_DIR, "pyArchitect", *parts)


def config_file_path():
    """Return the path of the extension's single settings file."""
    return appdata.get_universal_data_file(CONFIG_FILE_ID, "ini")


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


def _open_ini(path):
    """Open an ini file through pyRevit, whichever generation is running.

    Returns a ``(container, save)`` pair.
    """
    try:
        from pyrevit.coreutils.configparser import open_config_file
    except ImportError:
        from pyrevit.coreutils.configparser import PyRevitConfigParser

        parser = PyRevitConfigParser(path if os.path.isfile(path) else None)
        return parser, lambda: parser.save(path)
    sections = open_config_file(path)
    return sections, sections.save


def _open():
    """Open the extension's settings file, seeding it on first use."""
    path = config_file_path()
    first_use = not os.path.isfile(path)
    container, save = _open_ini(path)
    if first_use:
        _adopt_legacy(container)
        save()
    return container, save


def _copy_section(source, container, section_name):
    """Copy every option of one section into the extension's settings file."""
    if source is None:
        return
    target = _section(container, section_name, create=True)
    for name in source:
        target.set_option(name, _read(source, name, None))


def _adopt_legacy(container):
    """Pull settings written before the extension had a single config file.

    Earlier builds split settings between pyRevit's shared config and one ini
    file per feature.  This runs once, when the extension's own file does not
    exist yet, so upgrading does not lose saved settings.  It can be dropped
    once installs have rolled over.
    """
    _copy_section(_section(user_config, SECTION), container, SECTION)
    for file_id, section_name in _LEGACY_DATA_FILES.items():
        path = appdata.get_universal_data_file(file_id, "ini")
        if not os.path.isfile(path):
            continue
        legacy, _ = _open_ini(path)
        _copy_section(_section(legacy, section_name), container, section_name)


def get_option(name, default=None, section=SECTION):
    """Read a setting from the extension's settings file."""
    container, _ = _open()
    found = _section(container, section)
    return _read(found, name, default) if found else default


def set_option(name, value, section=SECTION):
    """Save a setting to the extension's settings file."""
    container, save = _open()
    _section(container, section, create=True).set_option(name, value)
    save()
