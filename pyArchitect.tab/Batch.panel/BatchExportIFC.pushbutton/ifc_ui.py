# -*- coding: utf-8 -*-

import json
import os
import System

import Autodesk.Revit.DB as DB

from pyrevit import forms

from core import config
from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.batch.ifc import IFCBatchExporter, ExportSettings, ModelExportItem


OPTIONS_CONFIG_KEY = "batch_ifc_options"

FOLDER_GLYPH = u"\uED25"
RESET_GLYPH = u"\uE72C"


FLAG_LABELS = [
    ("SplitWallsAndColumns", "Split walls and columns by level"),
    ("IncludeSteelElements", "Include steel elements"),
    ("Export2DElements", "Export 2D elements"),
    ("ExportPartsAsBuildingElements", "Export parts"),
    ("ExportSolidModelRep", "Export solid model representation"),
    ("UseFamilyAndTypeNameForReference", "Use family/type reference"),
    ("IncludeSiteElevation", "Include site elevation"),
    ("StoreIFCGUID", "Store IFC GUID in model"),
    ("VisibleElementsOfCurrentView", "Export visible elements only"),
    ("ExportRoomsInView", "Export rooms/spaces"),
    ("ExportInternalRevitPropertySets", "Export Revit property sets"),
    ("ExportIFCCommonPropertySets", "Export IFC common property sets"),
    ("ExportBaseQuantities", "Export base quantities"),
    ("ExportSchedulesAsPsets", "Export schedules as property sets"),
    ("ExportUserDefinedPsets", "Export user-defined property sets"),
]

CHECKBOX_LABELS = [
    ("open_without_links", "Open without Revit links", False),
    ("export_links_merged", "Export links in the same IFC", False),
    ("export_links_separately", "Export linked models separately", False),
    ("save_after", "Save/synchronize after export", False),
    ("open_folders", "Open export folders when complete", True),
]


class IfcOptionsPresenter(BatchOptionsPresenter):
    selection_description = (
        "Tick the models to export. Every model is exported with the settings from the "
        "Options tab, into the export folder set there."
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
        self.export_folder = widgets.textbox(self.defaults.export_folder)
        self.export_folder.TextChanged += self._export_folder_changed

        browse = widgets.icon_button(FOLDER_GLYPH, "Pick export folder")
        browse.Click += self._pick_export_folder
        reset = widgets.icon_button(RESET_GLYPH, "Use the folder the models came from")
        reset.Click += self._reset_export_folder
        export_folder_row = widgets.fill_row(self.export_folder, browse, reset)

        self.flag_controls = dict(
            (key, widgets.checkbox(text, self.defaults.bool_flags[key]))
            for key, text in FLAG_LABELS
        )
        self.controls = dict(
            (name, widgets.checkbox(text, checked))
            for name, text, checked in CHECKBOX_LABELS
        )
        self.controls["open_without_links"].Click += self._enforce_link_options
        self.controls["export_links_merged"].Click += self._enforce_link_options
        self.controls["export_links_separately"].Click += self._enforce_link_options

        host.Children.Add(
            widgets.stack(
                widgets.label("IFC version"),
                self.version,
                widgets.label("Default 3D view name"),
                self.default_view,
                widgets.label("Export folder"),
                export_folder_row,
                *(
                    [self.flag_controls[key] for key, _ in FLAG_LABELS]
                    + [self.controls[name] for name, _, _ in CHECKBOX_LABELS]
                )
            )
        )

    def _pick_export_folder(self, sender, args):
        folder = forms.pick_folder()
        if folder:
            self.export_folder.Text = folder

    def _reset_export_folder(self, sender, args):
        default = self.form.default_export_folder() if self.form else ""
        if not default:
            forms.alert(
                "No default export folder is available. Revit Server routes have no "
                "local folder, so pick an export folder instead.",
                title="Batch IFC export",
            )
            return
        self.export_folder.Text = default

    def _export_folder_changed(self, sender, args):
        if self.form:
            self.form.refresh_run_state()

    def validation_error(self):
        if self.export_folder is None or self.export_folder.Text.strip():
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
        settings.export_folder = self.export_folder.Text.strip()
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
    result = show_batch_form("Batch IFC export", IfcOptionsPresenter())
    if not result:
        return None, None
    settings = result["options"]
    models = result["input"].items

    if not settings.export_folder and not all(
        item.options.get("export_path") for item in models
    ):
        forms.alert(
            "Specify an export folder for the selected models.",
            title="Batch IFC export",
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
            title="Batch IFC export",
        )
        return None, None
    return items, settings


def show_options_form():
    result = show_batch_form("IFC export options", IfcOptionsPresenter(), True)
    if result:
        save_options(result["options"])
        forms.alert("IFC export options saved.", title="IFC export options")
    return result
