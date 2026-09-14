# -*- coding: utf-8 -*-
"""Navisworks view profiles, loaded from editable JSON configuration.

Resolution order: the path stored in the ``navis_profiles_path`` option, the
per-user copy in the pyArchitect data folder, then the bundled defaults.
"""

import codecs
import json
import os
import shutil

from Autodesk.Revit.DB import BuiltInCategory

from tools import config


BUNDLED_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")
USER_PROFILES_PATH = config.user_data_path("navis_profiles.json")
PROFILES_PATH_OPTION = "navis_profiles_path"


def resolve_categories(names):
    """Map BuiltInCategory names to members, dropping ones this Revit lacks."""
    resolved = []
    for name in names or []:
        category = getattr(BuiltInCategory, name, None)
        if category is not None:
            resolved.append(category)
    return resolved


class NavisProfile(object):
    def __init__(self, profile_id, caption=None, name_markers=None, categories=None):
        self.id = profile_id
        self.caption = caption or profile_id
        self.name_markers = name_markers or []
        self.hidden_categories = categories or []


class ProfileLibrary(object):
    """Read-only view over one parsed profile configuration."""

    def __init__(self, data=None):
        data = data or {}
        groups = data.get("category_groups", {})
        self.always_hidden_categories = resolve_categories(
            data.get("always_hidden_categories")
        )
        self.centerline_categories = resolve_categories(
            data.get("centerline_categories")
        )
        self.centerline_subcategory_names = data.get("centerline_subcategory_names", [])
        self.profiles = [
            self._build(entry, groups) for entry in data.get("profiles", [])
        ]

    @staticmethod
    def _build(entry, groups):
        names = list(entry.get("hidden_categories", []))
        for group in entry.get("hidden_groups", []):
            names.extend(groups.get(group, []))
        return NavisProfile(
            entry["id"],
            entry.get("caption"),
            entry.get("name_markers"),
            resolve_categories(names),
        )

    @property
    def default_id(self):
        return self.profiles[0].id if self.profiles else "UNIVERSAL"

    @property
    def captions(self):
        return [profile.caption for profile in self.profiles]

    @property
    def ids(self):
        return [profile.id for profile in self.profiles]

    def get(self, profile_id):
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        return None

    def at(self, index):
        if index is None or index < 0 or index >= len(self.profiles):
            return None
        return self.profiles[index]

    def index_of(self, profile_id):
        for index, profile in enumerate(self.profiles):
            if profile.id == profile_id:
                return index
        return 0

    def hidden_categories(self, profile_id):
        profile = self.get(profile_id)
        return profile.hidden_categories if profile else []

    def guess(self, file_name):
        """Pick a profile from discipline markers found in a model name."""
        name = (file_name or "").upper()
        for profile in self.profiles:
            for marker in profile.name_markers:
                if marker.upper() in name:
                    return profile.id
        return self.default_id


_LIBRARY = None


def profiles_path():
    configured = config.get_option(PROFILES_PATH_OPTION, "")
    for path in [configured, USER_PROFILES_PATH]:
        if path and os.path.isfile(path):
            return path
    return BUNDLED_PROFILES_PATH


def read_profiles(path=None):
    path = path or profiles_path()
    with codecs.open(path, "r", "utf-8-sig") as profiles_file:
        return ProfileLibrary(json.loads(profiles_file.read()))


def load_profiles(force_reload=False):
    """Return the cached profile library, rebuilding it on demand."""
    global _LIBRARY
    if _LIBRARY is not None and not force_reload:
        return _LIBRARY

    path = profiles_path()
    try:
        _LIBRARY = read_profiles(path)
    except Exception as exception:
        print("Cannot read Navisworks profiles from '{}': {}".format(path, exception))
        _LIBRARY = read_profiles(BUNDLED_PROFILES_PATH)
    return _LIBRARY


def install_user_profiles(overwrite=False):
    """Copy the bundled profiles next to the other pyArchitect user data."""
    if overwrite or not os.path.isfile(USER_PROFILES_PATH):
        folder = os.path.dirname(USER_PROFILES_PATH)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        shutil.copy2(BUNDLED_PROFILES_PATH, USER_PROFILES_PATH)
    return USER_PROFILES_PATH
