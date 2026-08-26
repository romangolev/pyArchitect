# -*- coding: utf-8 -*-
"""WPF and pyRevit interaction for the Batch IFC command."""

import os
import System

import Autodesk.Revit.DB as DB

from pyrevit import forms
from pyrevit.forms import WPFWindow

from tools.batch.ifc import ExportSettings, ModelExportItem, parse_model_list
from tools.batch.input import BatchInputCsv, BatchInputPrompt


CONTROL_NAMES = [
    "txtSelectionSummary",
    "cmbVersion",
    "cmbSitePlacement",
    "txtDefaultView",
    "chkSplitWalls",
    "chkSteel",
    "chk2D",
    "chkParts",
    "chkSolidRep",
    "chkFamilyTypeRef",
    "chkSiteElevation",
    "chkStoreGuid",
    "chkOnlyView",
    "chkRooms",
    "chkSkipLinkLoad",
    "chkLinksMerged",
    "chkLinksSeparate",
    "chkRevitPsets",
    "chkCommonPsets",
    "chkBaseQuantities",
    "chkSchedulesAsPsets",
    "chkUserPsets",
    "chkSaveAfter",
    "chkOpenFolders",
]


class SettingsWindow(WPFWindow):
    def __init__(self, xaml_file_name, item_count):
        WPFWindow.__init__(self, xaml_file_name)
        self.settings = None
        for control_name in CONTROL_NAMES:
            setattr(self, control_name, self.FindName(control_name))

        self.txtSelectionSummary.Text = "{} model(s) selected".format(item_count)
        self.txtDefaultView.Text = "Navisworks"
        version_names = [value for value in System.Enum.GetNames(DB.IFCVersion)]
        self.cmbVersion.ItemsSource = version_names
        self.cmbVersion.SelectedItem = (
            "IFC2x3CV2" if "IFC2x3CV2" in version_names else version_names[0]
        )

        self.chkCommonPsets.IsChecked = True
        self.chkBaseQuantities.IsChecked = True
        self.chkRooms.IsChecked = True
        self.chkOpenFolders.IsChecked = True

    def on_cancel(self, sender, args):
        self.settings = None
        self.DialogResult = False
        self.Close()

    def on_run(self, sender, args):
        settings = ExportSettings()
        settings.ifc_version = getattr(DB.IFCVersion, str(self.cmbVersion.SelectedItem))
        settings.site_placement = self.cmbSitePlacement.SelectedIndex
        settings.default_view_name = self.txtDefaultView.Text.strip()

        settings.bool_flags["SplitWallsAndColumns"] = bool(self.chkSplitWalls.IsChecked)
        settings.bool_flags["IncludeSteelElements"] = bool(self.chkSteel.IsChecked)
        settings.bool_flags["Export2DElements"] = bool(self.chk2D.IsChecked)
        settings.bool_flags["ExportPartsAsBuildingElements"] = bool(
            self.chkParts.IsChecked
        )
        settings.bool_flags["ExportSolidModelRep"] = bool(self.chkSolidRep.IsChecked)
        settings.bool_flags["UseFamilyAndTypeNameForReference"] = bool(
            self.chkFamilyTypeRef.IsChecked
        )
        settings.bool_flags["IncludeSiteElevation"] = bool(
            self.chkSiteElevation.IsChecked
        )
        settings.bool_flags["StoreIFCGUID"] = bool(self.chkStoreGuid.IsChecked)
        settings.bool_flags["VisibleElementsOfCurrentView"] = bool(
            self.chkOnlyView.IsChecked
        )
        settings.bool_flags["ExportRoomsInView"] = bool(self.chkRooms.IsChecked)
        settings.bool_flags["ExportInternalRevitPropertySets"] = bool(
            self.chkRevitPsets.IsChecked
        )
        settings.bool_flags["ExportIFCCommonPropertySets"] = bool(
            self.chkCommonPsets.IsChecked
        )
        settings.bool_flags["ExportBaseQuantities"] = bool(
            self.chkBaseQuantities.IsChecked
        )
        settings.bool_flags["ExportSchedulesAsPsets"] = bool(
            self.chkSchedulesAsPsets.IsChecked
        )
        settings.bool_flags["ExportUserDefinedPsets"] = bool(
            self.chkUserPsets.IsChecked
        )

        settings.export_links_merged = bool(self.chkLinksMerged.IsChecked)
        settings.export_links_separately = bool(self.chkLinksSeparate.IsChecked)
        settings.open_without_links = bool(self.chkSkipLinkLoad.IsChecked)
        settings.save_after = bool(self.chkSaveAfter.IsChecked)
        settings.open_folders = bool(self.chkOpenFolders.IsChecked)

        if settings.open_without_links and (
            settings.export_links_merged or settings.export_links_separately
        ):
            forms.alert(
                "Open without Revit links cannot be used when exporting linked models. "
                "Disable the linked-model export options or open links normally.",
                title="Batch IFC Export",
            )
            return

        self.settings = settings
        self.DialogResult = True
        self.Close()


def collect_model_list():
    choice = forms.CommandSwitchWindow.show(
        [
            "Quick folder",
            "Import shared batch CSV",
            "Import legacy IFC list",
            "Pick models manually",
        ],
        message="How do you want to build the batch list?",
    )
    if not choice:
        return None
    if choice == "Quick folder":
        return _build_items_from_folder()
    if choice == "Import shared batch CSV":
        return _build_items_from_batch_csv()
    if choice == "Import legacy IFC list":
        list_file = forms.pick_file(
            files_filter="CSV/TXT files (*.csv;*.txt)|*.csv;*.txt|All files (*.*)|*.*",
            restore_dir=True,
        )
        if not list_file:
            return None
        items, errors = parse_model_list(list_file)
        if errors:
            forms.alert(
                "Some lines in the list could not be read:\n\n" + "\n".join(errors),
                title="Batch IFC Export",
            )
        return items
    return _build_items_from_manual_pick()


def _build_items_from_folder():
    batch_input = BatchInputPrompt().from_folder()
    if not batch_input:
        return []
    export_folder = forms.pick_folder(title="Choose the IFC export folder")
    if not export_folder:
        return []
    return _to_export_items(batch_input, export_folder)


def _build_items_from_batch_csv():
    csv_file = forms.pick_file(
        files_filter="Batch CSV files (*.csv)|*.csv", restore_dir=True
    )
    if not csv_file:
        return []
    try:
        batch_input = BatchInputCsv().load(csv_file)
    except Exception as exception:
        forms.alert(
            "Cannot read batch CSV:\n{}".format(exception), title="Batch IFC Export"
        )
        return []
    missing_output_paths = [
        item for item in batch_input.items if not item.options.get("export_path")
    ]
    export_folder = ""
    if missing_output_paths:
        export_folder = forms.pick_folder(title="Choose the default IFC export folder")
        if not export_folder:
            return []
    return _to_export_items(batch_input, export_folder)


def _to_export_items(batch_input, default_export_folder):
    return [
        ModelExportItem(
            item.options.get("name", os.path.basename(item.source_path)),
            item.source_path,
            item.options.get("export_path", default_export_folder),
            item.options.get("mapping_file", ""),
            item.options.get("new_name", ""),
            item.options.get("views", []),
        )
        for item in batch_input.items
    ]


def select_models(items):
    missing = [item for item in items if not item.exists]
    valid = [item for item in items if item.exists]
    if missing:
        forms.alert(
            "{} model(s) were not found on disk and will be skipped:\n\n".format(
                len(missing)
            )
            + "\n".join(item.source_path for item in missing),
            title="Batch IFC Export",
        )
    if not valid:
        forms.alert("No existing models to export.", title="Batch IFC Export")
        return None
    return forms.SelectFromList.show(
        valid,
        title="Select models to export",
        multiselect=True,
        button_name="Select",
        name_attr="label",
    )


def ask_settings(xaml_file, item_count):
    window = SettingsWindow(xaml_file, item_count)
    return window.settings if window.ShowDialog() else None


def _build_items_from_manual_pick():
    paths = forms.pick_file(
        files_filter="Revit files (*.rvt)|*.rvt|All files (*.*)|*.*",
        multi_file=True,
        restore_dir=True,
    )
    if not paths:
        return []
    export_folder = forms.pick_folder(
        title="Choose the export folder for all selected models"
    )
    if not export_folder:
        return []
    return [
        ModelExportItem(os.path.basename(path), path, export_folder) for path in paths
    ]
