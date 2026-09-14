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
    def __init__(self):
        self.defaults = ExportSettings()
        self.version = None
        self.default_view = None
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
                *(
                    [self.flag_controls[key] for key, _ in FLAG_LABELS]
                    + [self.controls[name] for name, _, _ in CHECKBOX_LABELS]
                )
            )
        )

    def create_item_property(self, item):
        return widgets.textbox(item.options.get("export_path", ""), width=220)

    def read_item_property(self, item, control):
        options = dict(item.options)
        options["export_path"] = control.Text.strip()
        return options

    def read_options(self):
        settings = ExportSettings()
        settings.ifc_version = getattr(DB.IFCVersion, str(self.version.SelectedItem))
        settings.default_view_name = self.default_view.Text.strip()
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
    items = []
    for item in result["input"].items:
        export_path = item.options.get("export_path", "")
        if not export_path:
            forms.alert(
                "Specify an export folder for every selected model.",
                title="Batch IFC export",
            )
            return None, None
        items.append(
            ModelExportItem(
                item.options.get("name", os.path.basename(item.source_path)),
                item.source_path,
                export_path,
                item.options.get("mapping_file", ""),
                item.options.get("new_name", ""),
                item.options.get("views", []),
            )
        )
    return items, settings


def show_options_form():
    return show_batch_form("IFC export options", IfcOptionsPresenter(), True)
