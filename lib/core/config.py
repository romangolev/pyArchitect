# -*- coding: utf-8 -*-
"""Centralized pyRevit configuration access for the pyArchitect extension.

Use :func:`get_option` for extension-wide settings stored in pyRevit's shared
configuration.  Feature-specific settings that need their own INI file use
the ``data_*`` functions below; the storage implementation still lives here.
"""

import codecs
import json
import os

from pyrevit import script
from pyrevit.coreutils import appdata
from pyrevit.userconfig import user_config


SECTION = "pyArchitect"
_DATA_VALUE_PREFIX = "__pyarchitect_json__:"

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


def _read_data_file(path):
    """Read the small INI subset needed by pyArchitect data files.

    This intentionally avoids pyRevit's internal config-parser classes. Those
    classes are not available in every IronPython engine that pyRevit supports.
    """
    sections = {}
    current_section = None
    if not os.path.isfile(path):
        return sections
    with codecs.open(path, "r", "utf-8-sig") as data_file:
        for line in data_file:
            text = line.strip()
            if not text or text.startswith(";") or text.startswith("#"):
                continue
            if text.startswith("[") and text.endswith("]"):
                current_section = text[1:-1].strip()
                sections.setdefault(current_section, {})
            elif current_section and "=" in text:
                name, value = text.split("=", 1)
                sections[current_section][name.strip()] = value.strip()
    return sections


def _write_data_file(path, sections):
    folder = os.path.dirname(path)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with codecs.open(path, "w", "utf-8") as data_file:
        for section_name in sorted(sections):
            data_file.write(u"[{}]\n".format(section_name))
            for name in sorted(sections[section_name]):
                data_file.write(
                    u"{} = {}\n".format(name, sections[section_name][name])
                )
            data_file.write(u"\n")


def _decode_data_value(value):
    """Decode new values while accepting plain values from the old INI writer."""
    if value.startswith(_DATA_VALUE_PREFIX):
        return json.loads(value[len(_DATA_VALUE_PREFIX) :])
    # Earlier builds stored boolean values directly through pyRevit's parser.
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def get_data_option(file_id, section_name, name, default=None, file_ext="ini"):
    """Read a setting from a feature-specific pyRevit data INI file."""
    sections = _read_data_file(data_file_path(file_id, file_ext))
    value = sections.get(section_name, {}).get(name)
    return _decode_data_value(value) if value is not None else default


def set_data_option(file_id, section_name, name, value, file_ext="ini"):
    """Save a setting to a feature-specific pyRevit data INI file."""
    path = data_file_path(file_id, file_ext)
    sections = _read_data_file(path)
    section = sections.setdefault(section_name, {})
    section[name] = _DATA_VALUE_PREFIX + json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    )
    _write_data_file(path, sections)
