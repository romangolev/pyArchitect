# -*- coding: utf-8 -*-
"""Persistent defaults for the canonical Navisworks view."""

import json
import os

from pyrevit import forms

from tools import config
from tools.navis.profiles import (
    get_profiles_json,
    load_profiles,
    save_profiles_json,
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
    """Show the Shift-click settings window and save only on confirmation."""
    window = NavisSettingsWindow(load(), load_profiles(force_reload=True))
    if not window.show():
        return None
    save(window.settings)
    return window.settings


def edit_profiles():
    """Edit JSON presets and store them in pyArchitect's pyRevit config."""
    stored_profiles = get_profiles_json()
    try:
        editor_value = json.dumps(
            json.loads(stored_profiles), ensure_ascii=False, indent=2
        )
    except Exception:
        # Keep malformed JSON visible so the user can repair it in place.
        editor_value = stored_profiles
    editor = ProfileEditor(editor_value)
    if not editor.show():
        return None
    try:
        save_profiles_json(editor.value)
    except Exception as exception:
        forms.alert(
            "Profile presets were not saved:\n{}".format(exception),
            title="pyArchitect Navisworks settings",
        )
        return None
    forms.alert(
        "Navisworks profile presets saved to pyArchitect configuration.",
        title="pyArchitect Navisworks settings",
    )
    return True


class NavisSettingsWindow(forms.WPFWindow):
    """Single Shift-click editor for the Navis view and its default preset."""

    XAML_PATH = os.path.join(os.path.dirname(__file__), "navis_settings.xaml")

    def __init__(self, settings, profiles):
        forms.WPFWindow.__init__(self, self.XAML_PATH)
        self.settings = settings
        self.profiles = profiles
        self.saved = False
        self.tbViewName.Text = settings.view_name
        self.cbHideLinks.IsChecked = settings.hide_revit_links
        self.cbRecreate.IsChecked = settings.recreate_existing
        self._load_profiles(settings.profile)
        self.btnEditProfiles.Click += self._edit_profiles
        self.btnCancel.Click += self._cancel
        self.btnSave.Click += self._save

    def _load_profiles(self, selected_profile):
        self.cbProfile.Items.Clear()
        for profile in self.profiles.profiles:
            self.cbProfile.Items.Add(profile.caption)
        self.cbProfile.SelectedIndex = self.profiles.index_of(selected_profile)

    def _edit_profiles(self, sender, args):
        selected = self.profiles.at(self.cbProfile.SelectedIndex)
        selected_id = selected.id if selected else self.settings.profile
        if edit_profiles():
            self.profiles = load_profiles(force_reload=True)
            self._load_profiles(selected_id)

    def _save(self, sender, args):
        view_name = self.tbViewName.Text.strip()
        profile = self.profiles.at(self.cbProfile.SelectedIndex)
        if not view_name:
            forms.alert(
                "Specify a Navisworks 3D view name.",
                title="pyArchitect Navisworks settings",
            )
            return
        if profile is None:
            forms.alert(
                "Select a default profile.", title="pyArchitect Navisworks settings"
            )
            return
        self.settings.view_name = view_name
        self.settings.profile = profile.id
        self.settings.hide_revit_links = bool(self.cbHideLinks.IsChecked)
        self.settings.recreate_existing = bool(self.cbRecreate.IsChecked)
        self.saved = True
        self.Close()

    def _cancel(self, sender, args):
        self.Close()

    def show(self):
        self.ShowDialog()
        return self.saved


class ProfileEditor(forms.WPFWindow):
    """Small multiline JSON editor that avoids a separate user profile file."""

    XAML_PATH = os.path.join(os.path.dirname(__file__), "profile_editor.xaml")

    def __init__(self, value):
        forms.WPFWindow.__init__(self, self.XAML_PATH)
        self.value = None
        self.tbProfiles.Text = value
        self.btnSave.Click += self._save
        self.btnCancel.Click += self._cancel

    def _save(self, sender, args):
        self.value = self.tbProfiles.Text
        self.Close()

    def _cancel(self, sender, args):
        self.Close()

    def show(self):
        self.ShowDialog()
        return self.value is not None
