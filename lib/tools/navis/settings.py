# -*- coding: utf-8 -*-
"""Persistent defaults for the canonical Navisworks view."""

import json
import os

from pyrevit import forms

from core import config
from tools.navis.profiles import (
    CONFIG_SECTION,
    category_is_available,
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
    values = {}
    for name, option, default in OPTIONS:
        value = config.get_option(option, None, section=CONFIG_SECTION)
        if value is None:
            value = config.get_option(option, default)
        values[name] = value
    return NavisViewSettings(**values)


def save(settings):
    for name, option, _ in OPTIONS:
        config.set_option(option, getattr(settings, name), section=CONFIG_SECTION)


def configure():
    """Show the Shift-click settings window and save only on confirmation."""
    window = NavisSettingsWindow(load(), load_profiles(force_reload=True))
    if not window.show():
        return None
    save(window.settings)
    return window.settings


def edit_profiles():
    """Edit profile category visibility and persist it in pyRevit config."""
    try:
        editor = ProfileEditor(json.loads(get_profiles_json()))
    except Exception as exception:
        forms.alert(
            "Cannot open profile presets:\n{}".format(exception),
            title="pyArchitect Navisworks settings",
        )
        return None
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

    resolve_theme = True
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
    """Checkbox editor for category visibility in each Navis profile."""

    resolve_theme = True
    XAML_PATH = os.path.join(os.path.dirname(__file__), "profile_editor.xaml")

    def __init__(self, data):
        forms.WPFWindow.__init__(self, self.XAML_PATH)
        self.value = None
        self.data = data
        self.profiles = data.get("profiles", [])
        self.category_names = self._category_names()
        self.profile_categories = {}
        self.current_profile_index = None
        for profile in self.profiles:
            self.cbProfile.Items.Add(profile.get("caption", profile["id"]))
        self.cbProfile.SelectionChanged += self._select_profile
        self.btnSave.Click += self._save
        self.btnCancel.Click += self._cancel
        if self.profiles:
            self.cbProfile.SelectedIndex = 0

    def _category_names(self):
        names = set()
        for categories in self.data.get("category_groups", {}).values():
            names.update(categories)
        for profile in self.profiles:
            names.update(profile.get("hidden_categories", []))
        return sorted(names)

    def _effective_categories(self, profile):
        categories = set(profile.get("hidden_categories", []))
        groups = self.data.get("category_groups", {})
        for group in profile.get("hidden_groups", []):
            categories.update(groups.get(group, []))
        return categories

    def _store_current_profile(self):
        if self.current_profile_index is None:
            return
        selected = set(
            name for name, checkbox in self.category_checks.items() if checkbox.IsChecked
        )
        profile = self.profiles[self.current_profile_index]
        self.profile_categories[profile["id"]] = selected

    def _select_profile(self, sender, args):
        self._store_current_profile()
        index = self.cbProfile.SelectedIndex
        if index < 0 or index >= len(self.profiles):
            return
        self.current_profile_index = index
        profile = self.profiles[index]
        selected = self.profile_categories.get(
            profile["id"], self._effective_categories(profile)
        )
        self.category_checks = {}
        self.lbCategories.Items.Clear()
        from System.Windows.Controls import CheckBox

        for name in self.category_names:
            checkbox = CheckBox()
            available = category_is_available(name)
            checkbox.Content = name
            checkbox.IsChecked = name in selected
            if not available:
                checkbox.Content = "{} (not available in this Revit version)".format(
                    name
                )
                checkbox.ToolTip = (
                    "This category is not available in the running Revit version "
                    "and cannot be edited."
                )
                checkbox.IsEnabled = False
            self.category_checks[name] = checkbox
            self.lbCategories.Items.Add(checkbox)

    def _save(self, sender, args):
        self._store_current_profile()
        for profile in self.profiles:
            categories = self.profile_categories.get(profile["id"])
            if categories is None:
                continue
            profile["hidden_categories"] = sorted(categories)
            profile.pop("hidden_groups", None)
        self.value = json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        self.Close()

    def _cancel(self, sender, args):
        self.Close()

    def show(self):
        self.ShowDialog()
        return self.value is not None
