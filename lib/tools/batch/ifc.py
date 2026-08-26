# -*- coding: utf-8 -*-
"""IFC-specific batch export domain services."""

import os

import Autodesk.Revit.DB as DB

from core.transaction import WrappedTransaction
from tools.batch.documents import OpenedBatchDocument, RevitDocumentOpener
from tools.export.persistence import save_sync_and_relinquish


class ModelExportItem(object):
    def __init__(
        self, name, source_path, export_path, mapping_file="", new_name="", views=None
    ):
        self.name = name
        self.source_path = source_path
        self.export_path = export_path
        self.mapping_file = mapping_file
        self.new_name = new_name
        self.views = views or []
        self.exists = os.path.isfile(source_path)

    @property
    def label(self):
        return self.name if self.exists else "{} (file not found)".format(self.name)


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
    with open(file_path, "r") as mapping_file:
        lines = mapping_file.read().splitlines()

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(";")
        if len(parts) < 3:
            errors.append(
                "Line {}: expected at least Name;SourcePath;ExportPath".format(line_no)
            )
            continue
        views = []
        if len(parts) > 5 and parts[5].strip():
            views = [view.strip() for view in parts[5].split(",") if view.strip()]
        items.append(
            ModelExportItem(
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
                parts[3].strip() if len(parts) > 3 else "",
                parts[4].strip() if len(parts) > 4 else "",
                views,
            )
        )
    return items, errors


class IFCBatchExporter(object):
    def __init__(self, application, ui_application, logger=None):
        self.application = application
        self.logger = logger
        self.document_opener = RevitDocumentOpener(application, ui_application)

    @staticmethod
    def resolve_views(document, view_names):
        if not view_names:
            return [(None, None)]
        views_by_name = {}
        collector = DB.FilteredElementCollector(document).OfClass(DB.View3D)
        for view in collector.WhereElementIsNotElementType().ToElements():
            if not view.IsTemplate:
                views_by_name[view.Name] = view
        return [(name, views_by_name.get(name)) for name in view_names]

    @staticmethod
    def build_options(settings, mapping_file, view):
        options = DB.IFCExportOptions()
        options.FileVersion = settings.ifc_version
        if view is not None:
            options.FilterViewId = view.Id
            options.AddOption("UseActiveViewGeometry", "true")

        for key, value in settings.bool_flags.items():
            options.AddOption(key, "true" if value else "false")
        options.AddOption("SitePlacement", str(settings.site_placement))
        options.AddOption(
            "ExportLinkedFiles", "true" if settings.export_links_merged else "false"
        )
        if settings.bool_flags.get("ExportUserDefinedPsets") and mapping_file:
            options.AddOption("ExportUserDefinedPsetsFileName", mapping_file)
        return options

    def _save_or_sync(self, document):
        try:
            save_sync_and_relinquish(document, "Batch IFC export")
        except Exception as ex:
            if self.logger:
                self.logger.warning(
                    "Could not save/sync '{}': {}".format(document.Title, ex)
                )

    def _export_linked_documents(self, document, export_path, settings, results):
        links = DB.FilteredElementCollector(document).OfClass(DB.RevitLinkInstance)
        for link_instance in links.WhereElementIsNotElementType().ToElements():
            link_document = link_instance.GetLinkDocument()
            if link_document is None:
                results.append((link_instance.Name, "link", "Not loaded - skipped"))
                continue
            try:
                options = self.build_options(settings, "", None)
                with WrappedTransaction(
                    link_document, "Export linked IFC", warning_suppressor=True
                ):
                    link_document.Export(export_path, link_document.Title, options)
                results.append((link_document.Title, "link", "OK"))
            except Exception as ex:
                results.append(
                    (link_document.Title, "link", "Export failed: {}".format(ex))
                )

    def export_item(self, item, settings):
        results = []
        try:
            with OpenedBatchDocument(
                self.document_opener, item.source_path, settings.open_without_links
            ) as document:
                try:
                    if not os.path.isdir(item.export_path):
                        os.makedirs(item.export_path)
                except Exception as ex:
                    return [
                        (item.name, "-", "Cannot create export folder: {}".format(ex))
                    ]

                view_names = item.views or (
                    [settings.default_view_name] if settings.default_view_name else []
                )
                base_name = item.new_name or item.name
                if base_name.lower().endswith(".rvt"):
                    base_name = base_name[:-4]

                for label, view in self.resolve_views(document, view_names):
                    if view_names and view is None:
                        results.append((item.name, label, "View not found - skipped"))
                        continue
                    file_name = (
                        base_name if label is None else "{}_{}".format(base_name, label)
                    )
                    try:
                        with WrappedTransaction(
                            document, "Export IFC", warning_suppressor=True
                        ):
                            document.Export(
                                item.export_path,
                                file_name,
                                self.build_options(settings, item.mapping_file, view),
                            )
                        results.append((item.name, label or "(default view)", "OK"))
                    except Exception as ex:
                        results.append(
                            (
                                item.name,
                                label or "(default view)",
                                "Export failed: {}".format(ex),
                            )
                        )

                if settings.export_links_separately:
                    self._export_linked_documents(
                        document, item.export_path, settings, results
                    )
                if settings.save_after:
                    self._save_or_sync(document)
        except Exception as ex:
            results.append((item.name, "-", "Failed to prepare/open: {}".format(ex)))
        return results
