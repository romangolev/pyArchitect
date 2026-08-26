# -*- coding: utf-8 -*-
"""pyArchitect settings stored through pyRevit's supported config API."""

from pyrevit import script
from pyrevit.userconfig import user_config


SECTION = "pyArchitect"


def get_settings():
    """Return the extension-wide configuration section, creating it if needed."""
    if not user_config.has_section(SECTION):
        user_config.add_section(SECTION)
    return user_config.get_section(SECTION)


def get_option(name, default=None):
    return get_settings().get_option(name, default)


def set_option(name, value):
    settings = get_settings()
    setattr(settings, name, value)
    script.save_config()
