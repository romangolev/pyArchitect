# -*- coding: utf-8 -*-

import os
import System

import Autodesk.Revit.DB as DB

from pyrevit import forms

from tools.batch import widgets
from tools.batch.form import BatchOptionsPresenter, show_batch_form
from tools.batch.ifc import ExportSettings, ModelExportItem


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

    def __init__(self):
        self.defaults = ExportSettings()
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

        self.flag_controls = dict(
            (key, widgets.checkbox(text, self.defaults.bool_flags[key]))
            for key, text in FLAG_LABELS
        )
        self.controls = dict(
            (name, widgets.checkbox(text, checked))
            for name, text, checked in CHECKBOX_LABELS
        )

        host.Children.Add(
            widgets.stack(
                widgets.label("IFC version"),
                self.version,
                widgets.label("Default 3D view name"),
                self.default_view,
                widgets.label("Export folder"),
                self.export_folder,
                *(
                    [self.flag_controls[key] for key, _ in FLAG_LABELS]
                    + [self.controls[name] for name, _, _ in CHECKBOX_LABELS]
                )
            )
        )

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
    return items, settings


def show_options_form():
    return show_batch_form("IFC export options", IfcOptionsPresenter(), True)
