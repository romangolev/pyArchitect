# -*- coding: utf-8 -*-
"""pyArchitect settings stored through pyRevit's supported config API."""

from pyrevit import script


SECTION = "pyArchitect"


def get_settings():
    """Return the extension-wide configuration section, creating it if needed."""
    return script.get_config(SECTION)


def get_option(name, default=None):
    return get_settings().get_option(name, default)


def set_option(name, value):
    settings = get_settings()
    setattr(settings, name, value)
    script.save_config()
