# -*- coding: utf-8 -*-
"""Persistent defaults for the canonical Navisworks view."""

import os

from pyrevit import forms

from tools import config
from tools.navis.profiles import (
    PROFILES_PATH_OPTION,
    install_user_profiles,
    load_profiles,
)


OPTIONS = [
    ("view_name", "navis_view_name", "Navisworks"),
    ("profile", "navis_profile", "UNIVERSAL"),
    ("hide_revit_links", "navis_hide_revit_links", True),
    ("recreate_existing", "navis_recreate_existing", True),
]


class NavisViewSettings(object):
    def __init__(self, **overrides):
        for name, _, default in OPTIONS:
            setattr(self, name, overrides.get(name, default))


def load():
    values = dict(
        (name, config.get_option(option, default)) for name, option, default in OPTIONS
    )
    return NavisViewSettings(**values)


def save(settings):
    for name, option, _ in OPTIONS:
        config.set_option(option, getattr(settings, name))


def configure():
    """Shift-click configuration using pyRevit's extension config section."""
    settings = load()
    profiles = load_profiles(force_reload=True)

    view_name = forms.ask_for_string(
        default=settings.view_name,
        prompt="Exact name for the shared Navisworks 3D view:",
        title="pyArchitect Navisworks settings",
    )
    if not view_name:
        return None

    profile = forms.CommandSwitchWindow.show(
        profiles.ids,
        message="Default Navisworks view profile",
    )
    if not profile:
        return None

    settings.view_name = view_name.strip()
    settings.profile = profile
    settings.hide_revit_links = forms.alert(
        "Hide Revit links in the Navisworks view?", yes=True, no=True
    )
    settings.recreate_existing = forms.alert(
        "Recreate an existing view instead of updating it in place?", yes=True, no=True
    )
    save(settings)

    if forms.alert(
        "Edit the profile definitions (categories hidden per discipline)?",
        yes=True,
        no=True,
    ):
        edit_profiles()
    return settings


def edit_profiles():
    """Make a user-editable copy of the profiles and open it."""
    path = install_user_profiles()
    config.set_option(PROFILES_PATH_OPTION, path)
    try:
        os.startfile(path)
    except Exception:
        forms.alert("Profiles available at:\n{}".format(path))
    return path
