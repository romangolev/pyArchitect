# -*- coding: utf-8 -*-

import os
import System

from System.Windows import Thickness
from System.Windows.Controls import CheckBox, ComboBox, StackPanel, TextBlock, TextBox

import Autodesk.Revit.DB as DB

from pyrevit import forms

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


class IfcOptionsPresenter(BatchOptionsPresenter):
    def __init__(self):
        self.version = None
        self.default_view = None
        self.flag_controls = {}
        self.open_without_links = None
        self.export_links_merged = None
        self.export_links_separately = None
        self.save_after = None
        self.open_folders = None

    def build(self, host):
        panel = StackPanel()
        panel.Children.Add(self._label("IFC version"))
        self.version = ComboBox()
        version_names = [value for value in System.Enum.GetNames(DB.IFCVersion)]
        self.version.ItemsSource = version_names
        self.version.SelectedItem = (
            "IFC2x3CV2" if "IFC2x3CV2" in version_names else version_names[0]
        )
        panel.Children.Add(self.version)
        panel.Children.Add(self._label("Default 3D view name"))
        self.default_view = TextBox()
        self.default_view.Text = "Navisworks"
        panel.Children.Add(self.default_view)
        for key, label in FLAG_LABELS:
            control = CheckBox()
            control.Content = label
            control.IsChecked = ExportSettings().bool_flags[key]
            self.flag_controls[key] = control
            panel.Children.Add(control)
        self.open_without_links = self._checkbox("Open without Revit links")
        self.export_links_merged = self._checkbox("Export links in the same IFC")
        self.export_links_separately = self._checkbox("Export linked models separately")
        self.save_after = self._checkbox("Save/synchronize after export")
        self.open_folders = self._checkbox("Open export folders when complete", True)
        for control in [
            self.open_without_links,
            self.export_links_merged,
            self.export_links_separately,
            self.save_after,
            self.open_folders,
        ]:
            panel.Children.Add(control)
        host.Children.Add(panel)

    def create_item_property(self, item):
        output = TextBox()
        output.Width = 220
        output.Text = item.options.get("export_path", "")
        return output

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
        settings.open_without_links = bool(self.open_without_links.IsChecked)
        settings.export_links_merged = bool(self.export_links_merged.IsChecked)
        settings.export_links_separately = bool(self.export_links_separately.IsChecked)
        settings.save_after = bool(self.save_after.IsChecked)
        settings.open_folders = bool(self.open_folders.IsChecked)
        return settings

    @staticmethod
    def _label(text):
        label = TextBlock()
        label.Text = text
        label.Margin = Thickness(0, 8, 0, 2)
        return label

    @staticmethod
    def _checkbox(text, checked=False):
        control = CheckBox()
        control.Content = text
        control.IsChecked = checked
        return control


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
