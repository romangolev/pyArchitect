# -*- coding: utf-8 -*-
"""Navisworks view profiles persisted in pyArchitect's pyRevit config."""

import codecs
import json
import os

from Autodesk.Revit.DB import BuiltInCategory

from core import config


BUNDLED_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "profiles.json")
# Legacy locations are read once so existing custom profiles are not lost.
USER_PROFILES_PATH = config.user_data_path("navis_profiles.json")
PROFILES_PATH_OPTION = "navis_profiles_path"
PROFILES_JSON_OPTION = "navis_profiles_json"
CONFIG_FILE_ID = "navis"
CONFIG_SECTION = "pyArchitectNavis"


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


def _read_json_file(path):
    with codecs.open(path, "r", "utf-8-sig") as profiles_file:
        return json.loads(profiles_file.read())


def _bundled_profile_data():
    return _read_json_file(BUNDLED_PROFILES_PATH)


def _legacy_profile_data():
    stored = config.get_option(PROFILES_JSON_OPTION, "")
    if stored:
        try:
            return json.loads(stored)
        except Exception as exception:
            print("Cannot migrate stored Navisworks profiles: {}".format(exception))

    configured = config.get_option(PROFILES_PATH_OPTION, "")
    for path in [configured, USER_PROFILES_PATH]:
        if path and os.path.isfile(path):
            try:
                return _read_json_file(path)
            except Exception as exception:
                print(
                    "Cannot migrate Navisworks profiles from '{}': {}".format(
                        path, exception
                    )
                )
    return None


def get_profiles_json():
    """Return stored preset JSON, migrating legacy files on first use."""
    stored = config.get_data_option(
        CONFIG_FILE_ID, CONFIG_SECTION, PROFILES_JSON_OPTION, ""
    )
    if stored:
        return stored

    data = _legacy_profile_data() or _bundled_profile_data()
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    config.set_data_option(
        CONFIG_FILE_ID, CONFIG_SECTION, PROFILES_JSON_OPTION, serialized
    )
    return serialized


def save_profiles_json(value):
    """Validate and persist profile definitions as one pyRevit config value."""
    global _LIBRARY
    data = json.loads(value)
    library = ProfileLibrary(data)
    if not library.profiles:
        raise ValueError("At least one Navisworks profile is required")
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    config.set_data_option(
        CONFIG_FILE_ID, CONFIG_SECTION, PROFILES_JSON_OPTION, serialized
    )
    _LIBRARY = library
    return library


def reset_profiles():
    """Restore the bundled presets in pyArchitect's pyRevit config."""
    return save_profiles_json(
        json.dumps(_bundled_profile_data(), ensure_ascii=False, separators=(",", ":"))
    )


def load_profiles(force_reload=False):
    """Return profiles stored in pyArchitect's pyRevit configuration."""
    global _LIBRARY
    if _LIBRARY is not None and not force_reload:
        return _LIBRARY

    try:
        _LIBRARY = ProfileLibrary(json.loads(get_profiles_json()))
    except Exception as exception:
        print("Cannot read configured Navisworks profiles: {}".format(exception))
        _LIBRARY = ProfileLibrary(_bundled_profile_data())
    return _LIBRARY
