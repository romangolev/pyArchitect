# -*- coding: utf-8 -*-
"""Centralized pyRevit configuration access for the pyArchitect extension.

Use :func:`get_option` for extension-wide settings stored in pyRevit's shared
configuration.  Feature-specific settings that need their own INI file use
the ``data_*`` functions below; the storage implementation still lives here.
"""

import os

from pyrevit import script
from pyrevit.coreutils import appdata
from pyrevit.coreutils.configparser import PyRevitConfigParser
from pyrevit.userconfig import user_config


SECTION = "pyArchitect"

USER_DATA_FOLDER = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "pyRevit",
    "pyArchitect",
)


def user_data_path(*parts):
    """Build a path inside the per-user pyArchitect data folder."""
    return os.path.join(USER_DATA_FOLDER, *parts)


def get_settings():
    """Return the extension-wide configuration section, creating it if needed."""
    if not user_config.has_section(SECTION):
        user_config.add_section(SECTION)
    return user_config.get_section(SECTION)


def get_option(name, default=None):
    """Read an extension-wide setting from pyRevit's shared config."""
    return get_settings().get_option(name, default)


def set_option(name, value):
    """Save an extension-wide setting to pyRevit's shared config."""
    settings = get_settings()
    setattr(settings, name, value)
    script.save_config()


def data_file_path(file_id, file_ext="ini"):
    """Return a pyRevit universal data-file path for a feature."""
    return appdata.get_universal_data_file(file_id, file_ext)


def _data_settings(file_id, section_name, file_ext="ini"):
    """Open a feature data file and return its requested INI section."""
    path = data_file_path(file_id, file_ext)
    if not os.path.isfile(path):
        open(path, "w").close()
    parser = PyRevitConfigParser(cfg_file_path=path)
    try:
        section = parser.get_section(section_name)
    except AttributeError:
        section = parser.add_section(section_name)
    return parser, section


def get_data_option(file_id, section_name, name, default=None, file_ext="ini"):
    """Read a setting from a feature-specific pyRevit data INI file."""
    _, section = _data_settings(file_id, section_name, file_ext)
    return section.get_option(name, default)


def set_data_option(file_id, section_name, name, value, file_ext="ini"):
    """Save a setting to a feature-specific pyRevit data INI file."""
    parser, section = _data_settings(file_id, section_name, file_ext)
    setattr(section, name, value)
    parser.save_changes()
