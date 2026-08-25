# -*- coding: utf-8 -*-
"""Persistent defaults for the canonical Navisworks view."""

from pyrevit import forms

from tools import config


class NavisViewSettings(object):
    def __init__(self, view_name="Navisworks", profile="UNIVERSAL",
                 hide_revit_links=True, recreate_existing=True):
        self.view_name = view_name
        self.profile = profile
        self.hide_revit_links = hide_revit_links
        self.recreate_existing = recreate_existing


def load():
    return NavisViewSettings(
        config.get_option("navis_view_name", "Navisworks"),
        config.get_option("navis_profile", "UNIVERSAL"),
        config.get_option("navis_hide_revit_links", True),
        config.get_option("navis_recreate_existing", True))


def save(settings):
    config.set_option("navis_view_name", settings.view_name)
    config.set_option("navis_profile", settings.profile)
    config.set_option("navis_hide_revit_links", settings.hide_revit_links)
    config.set_option("navis_recreate_existing", settings.recreate_existing)


def configure():
    """Shift-click configuration using pyRevit's extension config section."""
    settings = load()
    view_name = forms.ask_for_string(
        default=settings.view_name,
        prompt="Exact name for the shared Navisworks 3D view:",
        title="pyArchitect Navisworks settings")
    if not view_name:
        return None

    profile = forms.CommandSwitchWindow.show(
        ["UNIVERSAL", "AR", "KR", "OV", "VK", "EOM", "CUSTOM"],
        message="Default Navisworks view profile")
    if not profile:
        return None

    settings.view_name = view_name.strip()
    settings.profile = profile
    settings.hide_revit_links = forms.alert(
        "Hide Revit links in the Navisworks view?",
        yes=True, no=True)
    settings.recreate_existing = forms.alert(
        "Recreate an existing view instead of updating it in place?",
        yes=True, no=True)
    save(settings)
    return settings
