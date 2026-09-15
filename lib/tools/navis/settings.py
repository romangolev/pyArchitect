# -*- coding: utf-8 -*-
"""Persistent defaults for the canonical Navisworks view."""

import json

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


class ProfileEditor(forms.WPFWindow):
    """Small multiline JSON editor that avoids a separate user profile file."""

    XAML = """<Window xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\"
        xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\"
        Title=\"Navisworks profile presets\" Width=\"820\" Height=\"620\"
        WindowStartupLocation=\"CenterScreen\">
        <Grid Margin=\"10\">
            <Grid.RowDefinitions>
                <RowDefinition Height=\"Auto\" />
                <RowDefinition Height=\"*\" />
                <RowDefinition Height=\"Auto\" />
            </Grid.RowDefinitions>
            <TextBlock Text=\"JSON profile definitions (saved in pyArchitect's pyRevit configuration)\" TextWrapping=\"Wrap\" />
            <TextBox x:Name=\"tbProfiles\" Grid.Row=\"1\" Margin=\"0,8,0,8\"
                AcceptsReturn=\"True\" AcceptsTab=\"True\" VerticalScrollBarVisibility=\"Auto\"
                HorizontalScrollBarVisibility=\"Auto\" FontFamily=\"Consolas\" TextWrapping=\"NoWrap\" />
            <StackPanel Grid.Row=\"2\" Orientation=\"Horizontal\" HorizontalAlignment=\"Right\">
                <Button x:Name=\"btnCancel\" Width=\"90\" Margin=\"0,0,6,0\" Content=\"Cancel\" />
                <Button x:Name=\"btnSave\" Width=\"90\" Content=\"Save\" />
            </StackPanel>
        </Grid>
    </Window>"""

    def __init__(self, value):
        forms.WPFWindow.__init__(self, self.XAML, literal_string=True)
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
