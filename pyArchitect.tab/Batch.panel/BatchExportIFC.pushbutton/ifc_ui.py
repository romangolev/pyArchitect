# -*- coding: utf-8 -*-

import json
import os
import System

import Autodesk.Revit.DB as DB

from System.Windows import Thickness

from pyrevit import forms

from core import config
from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.batch.ifc import IFCBatchExporter, ExportSettings, ModelExportItem
from tools.batch.strings import S


OPTIONS_CONFIG_KEY = "batch_ifc_options"



FLAG_GROUPS = [
    (
        "ifc.group.geometry",
        [
            "SplitWallsAndColumns",
            "IncludeSteelElements",
            "Export2DElements",
            "ExportPartsAsBuildingElements",
            "ExportSolidModelRep",
            "VisibleElementsOfCurrentView",
            "ExportRoomsInView",
            "IncludeSiteElevation",
        ],
    ),
    (
        "ifc.group.psets",
        [
            "ExportInternalRevitPropertySets",
            "ExportIFCCommonPropertySets",
            "ExportBaseQuantities",
            "ExportSchedulesAsPsets",
            "ExportUserDefinedPsets",
        ],
    ),
    (
        "ifc.group.identity",
        [
            "UseFamilyAndTypeNameForReference",
            "StoreIFCGUID",
        ],
    ),
]

OPTION_GROUPS = [
    (
        "ifc.group.links",
        [
            ("open_without_links", False),
            ("export_links_merged", False),
            ("export_links_separately", False),
        ],
    ),
    (
        "ifc.group.after",
        [
            ("save_after", False),
            ("open_folders", True),
        ],
    ),
]

FLAG_KEYS = [key for _, keys in FLAG_GROUPS for key in keys]

CHECKBOX_DEFAULTS = [entry for _, entries in OPTION_GROUPS for entry in entries]

ROW_MARGIN = (0, 0, 0, 5)


class IfcOptionsPresenter(BatchOptionsPresenter):
    source_description = S("form.source_description")
    selection_description = S("ifc.selection_description")
    options_description = S("ifc.options_description")

    def __init__(self, defaults=None):
        self.defaults = defaults or load_options()
        self.version = None
        self.default_view = None
        self.export_folder = None
        self.flag_controls = {}
        self.controls = {}

    def build(self, host):
        version_names = list(System.Enum.GetNames(DB.IFCVersion))
        default_version = System.Enum.GetName(DB.IFCVersion, self.defaults.ifc_version)
        self.version = widgets.combobox(
            version_names,
            (
                version_names.index(default_version)
                if default_version in version_names
                else 0
            ),
        )
        self.default_view = widgets.textbox(self.defaults.default_view_name)
        self.export_folder = widgets.FolderPicker(
            self.defaults.export_folder,
            pick_tooltip=S("ifc.tooltip.pick_folder"),
            on_default=self._default_export_folder,
            default_tooltip=S("ifc.tooltip.default_folder"),
            on_change=self._export_folder_changed,
        )

        self.flag_controls = dict(
            (
                key,
                widgets.checkbox(
                    S("ifc.flag." + key),
                    self.defaults.bool_flags[key],
                    margin=ROW_MARGIN,
                ),
            )
            for key in FLAG_KEYS
        )
        self.controls = dict(
            (
                name,
                widgets.checkbox(
                    S("ifc.option." + name), checked, margin=ROW_MARGIN
                ),
            )
            for name, checked in CHECKBOX_DEFAULTS
        )
        self.controls["open_without_links"].Click += self._enforce_link_options
        self.controls["export_links_merged"].Click += self._enforce_link_options
        self.controls["export_links_separately"].Click += self._enforce_link_options

        flags = dict(
            (group_key, [self.flag_controls[key] for key in keys])
            for group_key, keys in FLAG_GROUPS
        )
        options = dict(
            (group_key, [self.controls[name] for name, _ in entries])
            for group_key, entries in OPTION_GROUPS
        )

        identity = widgets.group(
            S("ifc.group.identity"), *flags["ifc.group.identity"]
        )
        identity.Margin = Thickness(0, 16, 0, 0)

        host.Children.Add(
            widgets.stack(
                widgets.columns(
                    widgets.stack(
                        widgets.label(S("ifc.label.version")), self.version
                    ),
                    widgets.stack(
                        widgets.label(S("ifc.label.default_view")), self.default_view
                    ),
                    gutter=14,
                ),
                widgets.label(S("ifc.label.export_folder")),
                self.export_folder.control,
                widgets.separator((0, 16, 0, 14)),
                widgets.columns(
                    widgets.group(
                        S("ifc.group.geometry"), *flags["ifc.group.geometry"]
                    ),
                    widgets.stack(
                        widgets.group(
                            S("ifc.group.psets"), *flags["ifc.group.psets"]
                        ),
                        identity,
                    ),
                ),
                widgets.separator((0, 16, 0, 14)),
                widgets.columns(
                    widgets.group(S("ifc.group.links"), *options["ifc.group.links"]),
                    widgets.group(S("ifc.group.after"), *options["ifc.group.after"]),
                ),
            )
        )

    def _default_export_folder(self):
        default = self.form.default_export_folder() if self.form else ""
        if not default:
            forms.alert(
                S("ifc.alert.no_default_folder"),
                title=S("ifc.title"),
            )
        return default

    def _export_folder_changed(self, sender, args):
        if self.form:
            self.form.refresh_run_state()

    def validation_error(self):
        if self.export_folder is None or self.export_folder.path:
            return None
        items = self.form.loaded_items() if self.form else []
        if items and all(item.options.get("export_path") for item in items):
            return None
        return S("ifc.error.no_export_folder")

    def _enforce_link_options(self, sender, args):
        if sender == self.controls["open_without_links"] and sender.IsChecked:
            self.controls["export_links_merged"].IsChecked = False
            self.controls["export_links_separately"].IsChecked = False
        elif sender.IsChecked:
            self.controls["open_without_links"].IsChecked = False

    def read_options(self):
        settings = ExportSettings()
        settings.ifc_version = getattr(DB.IFCVersion, str(self.version.SelectedItem))
        settings.default_view_name = self.default_view.Text.strip()
        settings.export_folder = self.export_folder.path
        for key, control in self.flag_controls.items():
            settings.bool_flags[key] = bool(control.IsChecked)
        for name, control in self.controls.items():
            setattr(settings, name, bool(control.IsChecked))
        return settings


def load_options():
    settings = ExportSettings()
    try:
        values = json.loads(config.get_option(OPTIONS_CONFIG_KEY, "{}"))
    except Exception:
        return settings
    if not isinstance(values, dict):
        return settings

    version_name = values.get("ifc_version")
    if version_name and hasattr(DB.IFCVersion, version_name):
        settings.ifc_version = getattr(DB.IFCVersion, version_name)
    settings.default_view_name = values.get(
        "default_view_name", settings.default_view_name
    )
    settings.export_folder = values.get("export_folder", settings.export_folder)
    for key in settings.bool_flags:
        if key in values.get("bool_flags", {}):
            settings.bool_flags[key] = bool(values["bool_flags"][key])
    for name, _ in CHECKBOX_DEFAULTS:
        if name in values:
            setattr(settings, name, bool(values[name]))
    if settings.open_without_links:
        settings.export_links_merged = False
        settings.export_links_separately = False
    return settings


def save_options(settings):
    values = {
        "ifc_version": str(System.Enum.GetName(DB.IFCVersion, settings.ifc_version)),
        "default_view_name": str(settings.default_view_name),
        "export_folder": str(settings.export_folder),
        "bool_flags": settings.bool_flags,
    }
    for name, _ in CHECKBOX_DEFAULTS:
        values[name] = getattr(settings, name)
    config.set_option(OPTIONS_CONFIG_KEY, json.dumps(values))


def show_form():
    result = show_batch_form(S("ifc.title"), IfcOptionsPresenter())
    if not result:
        return None, None
    settings = result["options"]
    models = result["input"].items

    if not settings.export_folder and not all(
        item.options.get("export_path") for item in models
    ):
        forms.alert(
            S("ifc.alert.specify_folder"),
            title=S("ifc.title"),
        )
        return None, None

    items = [
        ModelExportItem(
            item.options.get("name", os.path.basename(item.source_path)),
            item.source_path,
            item.options.get("export_path") or settings.export_folder,
            item.options.get("mapping_file", ""),
            item.options.get("new_name", ""),
            item.options.get("views", []),
        )
        for item in models
    ]
    collisions = IFCBatchExporter.find_primary_export_collisions(items, settings)
    if collisions:
        names = "\n".join(
            "{}\n  {}\n  {}".format(target, first, second)
            for target, first, second in collisions
        )
        forms.alert(
            S("ifc.alert.collisions", names),
            title=S("ifc.title"),
        )
        return None, None
    return items, settings


def show_options_form():
    result = show_batch_form(S("ifc.settings_title"), IfcOptionsPresenter(), True)
    if result:
        save_options(result["options"])
        forms.alert(
            S("ifc.alert.options_saved"), title=S("ifc.settings_title")
        )
    return result
