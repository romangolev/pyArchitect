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


OPTIONS_CONFIG_KEY = "batch_ifc_options"



FLAG_GROUPS = [
    (
        "Geometry & elements",
        [
            ("SplitWallsAndColumns", "Split walls and columns by level"),
            ("IncludeSteelElements", "Include steel elements"),
            ("Export2DElements", "Export 2D elements"),
            ("ExportPartsAsBuildingElements", "Export parts"),
            ("ExportSolidModelRep", "Export solid model representation"),
            ("VisibleElementsOfCurrentView", "Export visible elements only"),
            ("ExportRoomsInView", "Export rooms/spaces"),
            ("IncludeSiteElevation", "Include site elevation"),
        ],
    ),
    (
        "Property sets",
        [
            ("ExportInternalRevitPropertySets", "Export Revit property sets"),
            ("ExportIFCCommonPropertySets", "Export IFC common property sets"),
            ("ExportBaseQuantities", "Export base quantities"),
            ("ExportSchedulesAsPsets", "Export schedules as property sets"),
            ("ExportUserDefinedPsets", "Export user-defined property sets"),
        ],
    ),
    (
        "Identity",
        [
            ("UseFamilyAndTypeNameForReference", "Use family/type reference"),
            ("StoreIFCGUID", "Store IFC GUID in model"),
        ],
    ),
]

OPTION_GROUPS = [
    (
        "Linked models",
        [
            ("open_without_links", "Open without Revit links", False),
            ("export_links_merged", "Export links in the same IFC", False),
            ("export_links_separately", "Export linked models separately", False),
        ],
    ),
    (
        "After the run",
        [
            ("save_after", "Save/synchronize after export", False),
            ("open_folders", "Open export folders when complete", True),
        ],
    ),
]

FLAG_LABELS = [pair for _, pairs in FLAG_GROUPS for pair in pairs]

CHECKBOX_LABELS = [entry for _, entries in OPTION_GROUPS for entry in entries]

ROW_MARGIN = (0, 0, 0, 5)


class IfcOptionsPresenter(BatchOptionsPresenter):
    source_description = "Pick where the models come from, then load them."
    selection_description = "Tick the models to export."
    options_description = (
        "These settings apply to every ticked model. Set the export folder, then "
        "run the export."
    )

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
            pick_tooltip="Pick the export folder",
            on_default=self._default_export_folder,
            default_tooltip="Use the folder the models came from",
            on_change=self._export_folder_changed,
        )

        self.flag_controls = dict(
            (
                key,
                widgets.checkbox(
                    text, self.defaults.bool_flags[key], margin=ROW_MARGIN
                ),
            )
            for key, text in FLAG_LABELS
        )
        self.controls = dict(
            (name, widgets.checkbox(text, checked, margin=ROW_MARGIN))
            for name, text, checked in CHECKBOX_LABELS
        )
        self.controls["open_without_links"].Click += self._enforce_link_options
        self.controls["export_links_merged"].Click += self._enforce_link_options
        self.controls["export_links_separately"].Click += self._enforce_link_options

        flags = dict(
            (title, [self.flag_controls[key] for key, _ in pairs])
            for title, pairs in FLAG_GROUPS
        )
        options = dict(
            (title, [self.controls[name] for name, _, _ in entries])
            for title, entries in OPTION_GROUPS
        )

        identity = widgets.group("Identity", *flags["Identity"])
        identity.Margin = Thickness(0, 16, 0, 0)

        host.Children.Add(
            widgets.stack(
                widgets.columns(
                    widgets.stack(widgets.label("IFC version"), self.version),
                    widgets.stack(
                        widgets.label("Default 3D view name"), self.default_view
                    ),
                    gutter=14,
                ),
                widgets.label("Export folder"),
                self.export_folder.control,
                widgets.separator((0, 16, 0, 14)),
                widgets.columns(
                    widgets.group(
                        "Geometry & elements", *flags["Geometry & elements"]
                    ),
                    widgets.stack(
                        widgets.group("Property sets", *flags["Property sets"]),
                        identity,
                    ),
                ),
                widgets.separator((0, 16, 0, 14)),
                widgets.columns(
                    widgets.group("Linked models", *options["Linked models"]),
                    widgets.group("After the run", *options["After the run"]),
                ),
            )
        )

    def _default_export_folder(self):
        default = self.form.default_export_folder() if self.form else ""
        if not default:
            forms.alert(
                "No default export folder is available. Revit Server routes have no "
                "local folder, so pick an export folder instead.",
                title="Batch IFC Export",
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
        return "Set an export folder on the Options tab before running the batch."

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
    for name, _, _ in CHECKBOX_LABELS:
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
    for name, _, _ in CHECKBOX_LABELS:
        values[name] = getattr(settings, name)
    config.set_option(OPTIONS_CONFIG_KEY, json.dumps(values))


def show_form():
    result = show_batch_form("Batch IFC Export", IfcOptionsPresenter())
    if not result:
        return None, None
    settings = result["options"]
    models = result["input"].items

    if not settings.export_folder and not all(
        item.options.get("export_path") for item in models
    ):
        forms.alert(
            "Specify an export folder for the selected models.",
            title="Batch IFC Export",
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
            "Multiple selected models would overwrite the same IFC file:\n{}".format(
                names
            ),
            title="Batch IFC Export",
        )
        return None, None
    return items, settings


def show_options_form():
    result = show_batch_form("Batch IFC Export settings", IfcOptionsPresenter(), True)
    if result:
        save_options(result["options"])
        forms.alert(
            "Export settings saved.", title="Batch IFC Export settings"
        )
    return result
