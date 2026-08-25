# -*- coding: utf-8 -*-
"""Batch-export a list of Revit models to IFC.

Model list file format (semicolon separated, one model per line, '#' comments
and blank lines are ignored):

    Name;SourcePath;ExportPath;MappingFile;NewName;View1,View2,...

Only Name, SourcePath and ExportPath are required. MappingFile, NewName and
the comma-separated view list are optional. When no views are given, the
"Navisworks view name" from the settings window is used; when that is also
empty, the model is exported without pinning it to a specific view.
"""

import os
import shutil
import System
import tempfile
import Autodesk.Revit.DB as DB

from pyrevit import forms, script
from pyrevit.forms import WPFWindow

from core.transaction import WrappedTransaction

__helpurl__ = ""

uiapp = __revit__  # type: ignore
app = uiapp.Application
logger = script.get_logger()
output = script.get_output()

XAML_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui.xaml')


class ModelExportItem(object):
    def __init__(self, name, source_path, export_path, mapping_file="", new_name="", views=None):
        self.name = name
        self.source_path = source_path
        self.export_path = export_path
        self.mapping_file = mapping_file
        self.new_name = new_name
        self.views = views or []
        self.exists = os.path.isfile(source_path)

    @property
    def label(self):
        if self.exists:
            return self.name
        return "{} (file not found)".format(self.name)


class ExportSettings(object):
    def __init__(self):
        self.ifc_version = DB.IFCVersion.IFC2x3CV2
        self.site_placement = 0
        self.default_view_name = "Navisworks"
        self.export_links_merged = False
        self.export_links_separately = False
        self.open_without_links = False
        self.save_after = False
        self.open_folders = True
        self.bool_flags = {
            "SplitWallsAndColumns": False,
            "IncludeSteelElements": False,
            "Export2DElements": False,
            "VisibleElementsOfCurrentView": False,
            "ExportRoomsInView": True,
            "ExportInternalRevitPropertySets": False,
            "ExportIFCCommonPropertySets": True,
            "ExportBaseQuantities": True,
            "ExportSchedulesAsPsets": False,
            "ExportUserDefinedPsets": False,
            "ExportPartsAsBuildingElements": False,
            "ExportSolidModelRep": False,
            "UseFamilyAndTypeNameForReference": False,
            "IncludeSiteElevation": False,
            "StoreIFCGUID": False,
        }


def parse_model_list(file_path):
    items = []
    errors = []
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split(';')
        if len(parts) < 3:
            errors.append("Line {}: expected at least Name;SourcePath;ExportPath".format(line_no))
            continue
        name = parts[0].strip()
        source_path = parts[1].strip()
        export_path = parts[2].strip()
        mapping_file = parts[3].strip() if len(parts) > 3 else ""
        new_name = parts[4].strip() if len(parts) > 4 else ""
        views = []
        if len(parts) > 5 and parts[5].strip():
            views = [v.strip() for v in parts[5].split(',') if v.strip()]
        items.append(ModelExportItem(name, source_path, export_path, mapping_file, new_name, views))

    return items, errors


def build_items_from_manual_pick():
    paths = forms.pick_file(
        files_filter="Revit files (*.rvt)|*.rvt|All files (*.*)|*.*",
        multi_file=True, restore_dir=True)
    if not paths:
        return []
    export_folder = forms.pick_folder(title="Choose the export folder for all selected models")
    if not export_folder:
        return []
    items = []
    for p in paths:
        items.append(ModelExportItem(os.path.basename(p), p, export_folder))
    return items


def collect_model_list():
    choice = forms.CommandSwitchWindow.show(
        ["Import list from CSV/TXT", "Pick models manually"],
        message="How do you want to build the batch list?")
    if not choice:
        return None

    if choice == "Import list from CSV/TXT":
        list_file = forms.pick_file(
            files_filter="CSV/TXT files (*.csv;*.txt)|*.csv;*.txt|All files (*.*)|*.*",
            restore_dir=True)
        if not list_file:
            return None
        items, errors = parse_model_list(list_file)
        if errors:
            forms.alert("Some lines in the list could not be read:\n\n" + "\n".join(errors), title="Batch IFC Export")
        return items
    else:
        return build_items_from_manual_pick()


def select_models(items):
    missing = [i for i in items if not i.exists]
    valid = [i for i in items if i.exists]

    if missing:
        forms.alert(
            "{} model(s) were not found on disk and will be skipped:\n\n".format(len(missing)) +
            "\n".join(i.source_path for i in missing),
            title="Batch IFC Export")

    if not valid:
        forms.alert("No existing models to export.", title="Batch IFC Export")
        return None

    selected = forms.SelectFromList.show(
        valid,
        title="Select models to export",
        multiselect=True,
        button_name="Select",
        name_attr='label')
    return selected


CONTROL_NAMES = [
    'txtSelectionSummary', 'cmbVersion', 'cmbSitePlacement', 'txtDefaultView',
    'chkSplitWalls', 'chkSteel', 'chk2D', 'chkParts', 'chkSolidRep',
    'chkFamilyTypeRef', 'chkSiteElevation', 'chkStoreGuid', 'chkOnlyView',
    'chkRooms', 'chkSkipLinkLoad', 'chkLinksMerged', 'chkLinksSeparate', 'chkRevitPsets',
    'chkCommonPsets', 'chkBaseQuantities', 'chkSchedulesAsPsets',
    'chkUserPsets', 'chkSaveAfter', 'chkOpenFolders',
]


class SettingsWindow(WPFWindow):
    def __init__(self, xaml_file_name, item_count):
        WPFWindow.__init__(self, xaml_file_name)
        self.settings = None

        for control_name in CONTROL_NAMES:
            setattr(self, control_name, self.FindName(control_name))

        self.txtSelectionSummary.Text = "{} model(s) selected".format(item_count)
        self.txtDefaultView.Text = "Navisworks"

        version_names = [v for v in System.Enum.GetNames(DB.IFCVersion)]
        self.cmbVersion.ItemsSource = version_names
        default_version = "IFC2x3CV2" if "IFC2x3CV2" in version_names else version_names[0]
        self.cmbVersion.SelectedItem = default_version

        # sensible defaults for common IFC exports
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
        settings.bool_flags["ExportPartsAsBuildingElements"] = bool(self.chkParts.IsChecked)
        settings.bool_flags["ExportSolidModelRep"] = bool(self.chkSolidRep.IsChecked)
        settings.bool_flags["UseFamilyAndTypeNameForReference"] = bool(self.chkFamilyTypeRef.IsChecked)
        settings.bool_flags["IncludeSiteElevation"] = bool(self.chkSiteElevation.IsChecked)
        settings.bool_flags["StoreIFCGUID"] = bool(self.chkStoreGuid.IsChecked)
        settings.bool_flags["VisibleElementsOfCurrentView"] = bool(self.chkOnlyView.IsChecked)
        settings.bool_flags["ExportRoomsInView"] = bool(self.chkRooms.IsChecked)
        settings.bool_flags["ExportInternalRevitPropertySets"] = bool(self.chkRevitPsets.IsChecked)
        settings.bool_flags["ExportIFCCommonPropertySets"] = bool(self.chkCommonPsets.IsChecked)
        settings.bool_flags["ExportBaseQuantities"] = bool(self.chkBaseQuantities.IsChecked)
        settings.bool_flags["ExportSchedulesAsPsets"] = bool(self.chkSchedulesAsPsets.IsChecked)
        settings.bool_flags["ExportUserDefinedPsets"] = bool(self.chkUserPsets.IsChecked)

        settings.export_links_merged = bool(self.chkLinksMerged.IsChecked)
        settings.export_links_separately = bool(self.chkLinksSeparate.IsChecked)
        settings.open_without_links = bool(self.chkSkipLinkLoad.IsChecked)
        settings.save_after = bool(self.chkSaveAfter.IsChecked)
        settings.open_folders = bool(self.chkOpenFolders.IsChecked)

        if settings.open_without_links and (
                settings.export_links_merged or settings.export_links_separately):
            forms.alert(
                "Open without Revit links cannot be used when exporting linked models. "
                "Disable the linked-model export options or open links normally.",
                title="Batch IFC Export")
            return

        self.settings = settings
        self.DialogResult = True
        self.Close()


def ask_settings(item_count):
    window = SettingsWindow(XAML_FILE, item_count)
    result = window.ShowDialog()
    if not result:
        return None
    return window.settings


def unload_revit_links(model_path):
    """Set Revit links to unload in a closed, disposable RVT copy."""
    transmission_data = DB.TransmissionData.ReadTransmissionData(model_path)
    if transmission_data is None:
        return

    for reference_id in transmission_data.GetAllExternalFileReferenceIds():
        reference = transmission_data.GetLastSavedReferenceData(reference_id)
        if reference is None:
            continue
        if reference.ExternalFileReferenceType != DB.ExternalFileReferenceType.RevitLink:
            continue
        transmission_data.SetDesiredReferenceData(
            reference_id,
            reference.GetPath(),
            reference.PathType,
            False)

    transmission_data.IsTransmitted = True
    DB.TransmissionData.WriteTransmissionData(model_path, transmission_data)


def create_linkless_copy(source_path):
    """Return a disposable local copy of source_path with Revit links unloaded."""
    temp_folder = tempfile.mkdtemp(prefix="pyArchitect_BatchIFC_")
    copy_path = os.path.join(temp_folder, os.path.basename(source_path))
    try:
        shutil.copy2(source_path, copy_path)
        unload_revit_links(DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(copy_path))
        return copy_path, temp_folder
    except Exception:
        shutil.rmtree(temp_folder, ignore_errors=True)
        raise


def dismiss_coordination_model_load_error(sender, args):
    """Dismiss only the known Coordination Model load-error dialog."""
    try:
        dialog_text = "{} {}".format(
            getattr(args, "Message", ""),
            getattr(args, "DialogId", "")).lower()
        if ("unable to load coordination model" in dialog_text or
                "coordinationmodel" in dialog_text):
            args.OverrideResult(1)  # IDOK
    except Exception:
        pass


def open_model(source_path, detach_from_central=False):
    model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(source_path)
    open_options = DB.OpenOptions()
    open_options.DetachFromCentralOption = (
        DB.DetachFromCentralOption.DetachAndPreserveWorksets
        if detach_from_central else
        DB.DetachFromCentralOption.DoNotDetach)
    open_options.SetOpenWorksetsConfiguration(
        DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenAllWorksets))
    uiapp.DialogBoxShowing += dismiss_coordination_model_load_error
    try:
        return app.OpenDocumentFile(model_path, open_options)
    finally:
        uiapp.DialogBoxShowing -= dismiss_coordination_model_load_error


def save_or_sync(document):
    try:
        if document.IsWorkshared:
            DB.WorksharingUtils.RelinquishOwnership(
                document, DB.RelinquishOptions(True), DB.TransactWithCentralOptions())
            sync_options = DB.SynchronizeWithCentralOptions()
            sync_options.SetRelinquishOptions(DB.RelinquishOptions(True))
            sync_options.Comment = "Batch IFC export"
            document.SynchronizeWithCentral(DB.TransactWithCentralOptions(), sync_options)
        else:
            document.Save()
    except Exception as ex:
        logger.warning("Could not save/sync '{}': {}".format(document.Title, ex))


def resolve_views(document, view_names):
    """Returns a list of (label, View3D-or-None) tuples.

    An empty view_names list yields a single (None, None) entry meaning
    "export without pinning a specific view".
    """
    if not view_names:
        return [(None, None)]

    views_by_name = {}
    collector = DB.FilteredElementCollector(document).OfClass(DB.View3D).WhereElementIsNotElementType().ToElements()
    for v in collector:
        if not v.IsTemplate:
            views_by_name[v.Name] = v

    resolved = []
    for name in view_names:
        resolved.append((name, views_by_name.get(name)))
    return resolved


def build_ifc_options(settings, mapping_file, view):
    options = DB.IFCExportOptions()
    options.FileVersion = settings.ifc_version
    if view is not None:
        options.FilterViewId = view.Id
        options.AddOption("UseActiveViewGeometry", "true")

    for key, value in settings.bool_flags.items():
        options.AddOption(key, "true" if value else "false")
    options.AddOption("SitePlacement", str(settings.site_placement))
    options.AddOption("ExportLinkedFiles", "true" if settings.export_links_merged else "false")

    if settings.bool_flags.get("ExportUserDefinedPsets") and mapping_file:
        options.AddOption("ExportUserDefinedPsetsFileName", mapping_file)

    return options


def export_linked_documents(document, export_path, settings, results):
    links = DB.FilteredElementCollector(document).OfClass(DB.RevitLinkInstance).WhereElementIsNotElementType().ToElements()
    for link_instance in links:
        link_doc = link_instance.GetLinkDocument()
        if link_doc is None:
            results.append((link_instance.Name, "link", "Not loaded - skipped"))
            continue
        options = build_ifc_options(settings, "", None)
        try:
            with WrappedTransaction(link_doc, "Export linked IFC", warning_suppressor=True):
                link_doc.Export(export_path, link_doc.Title, options)
            results.append((link_doc.Title, "link", "OK"))
        except Exception as ex:
            results.append((link_doc.Title, "link", "Export failed: {}".format(ex)))


def export_model(item, settings):
    results = []
    temporary_folder = None
    try:
        source_path = item.source_path
        if settings.open_without_links:
            source_path, temporary_folder = create_linkless_copy(source_path)
        document = open_model(
            source_path,
            detach_from_central=temporary_folder is not None)
    except Exception as ex:
        if temporary_folder:
            shutil.rmtree(temporary_folder, ignore_errors=True)
        return [(item.name, "-", "Failed to prepare/open: {}".format(ex))]

    try:
        if not os.path.isdir(item.export_path):
            try:
                os.makedirs(item.export_path)
            except Exception as ex:
                return [(item.name, "-", "Cannot create export folder: {}".format(ex))]

        view_names = item.views or ([settings.default_view_name] if settings.default_view_name else [])
        base_name = item.new_name or item.name
        if base_name.lower().endswith(".rvt"):
            base_name = base_name[:-4]

        for label, view in resolve_views(document, view_names):
            if view_names and view is None:
                results.append((item.name, label, "View not found - skipped"))
                continue

            file_name = base_name if label is None else "{}_{}".format(base_name, label)
            options = build_ifc_options(settings, item.mapping_file, view)
            try:
                with WrappedTransaction(document, "Export IFC", warning_suppressor=True):
                    document.Export(item.export_path, file_name, options)
                results.append((item.name, label or "(default view)", "OK"))
            except Exception as ex:
                results.append((item.name, label or "(default view)", "Export failed: {}".format(ex)))

        if settings.export_links_separately:
            export_linked_documents(document, item.export_path, settings, results)

        if settings.save_after:
            save_or_sync(document)

    finally:
        try:
            document.Close(False)
        except Exception:
            pass
        if temporary_folder:
            shutil.rmtree(temporary_folder, ignore_errors=True)

    return results


def print_report(all_results):
    output.print_md("## Batch IFC export report")
    ok_count = sum(1 for r in all_results if r[2] == "OK")
    fail_count = len(all_results) - ok_count
    output.print_md("**{} succeeded, {} failed/skipped**".format(ok_count, fail_count))
    output.print_table(
        table_data=[[r[0], r[1], r[2]] for r in all_results],
        columns=["Model", "View", "Result"])


def main():
    items = collect_model_list()
    if not items:
        return

    selected = select_models(items)
    if not selected:
        return

    settings = ask_settings(len(selected))
    if not settings:
        return

    all_results = []
    with forms.ProgressBar(title="Exporting {value} of {max_value} models") as pb:
        for counter, item in enumerate(selected):
            pb.update_progress(counter, len(selected))
            all_results.extend(export_model(item, settings))
        pb.update_progress(len(selected), len(selected))

    print_report(all_results)

    if settings.open_folders:
        folders = set(i.export_path for i in selected)
        for folder in folders:
            try:
                os.startfile(folder)
            except Exception:
                pass

    forms.alert(
        "{} export operation(s) finished.\nSee the pyRevit output window for the detailed report.".format(len(all_results)),
        title="Batch IFC Export")


if __name__ == '__main__':
    main()
