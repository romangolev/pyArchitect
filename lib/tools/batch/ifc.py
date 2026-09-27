# -*- coding: utf-8 -*-
"""IFC-specific batch export domain services."""

import os

import Autodesk.Revit.DB as DB

from core.transaction import WrappedTransaction
from tools.batch.documents import OpenedBatchDocument, RevitDocumentOpener
from tools.batch.strings import S
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
        return self.name if self.exists else S("ifc.result.file_not_found", self.name)


class ExportSettings(object):
    def __init__(self):
        self.ifc_version = DB.IFCVersion.IFC2x3CV2
        self.site_placement = 0
        self.default_view_name = "Navisworks"
        self.export_folder = ""
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

    @staticmethod
    def export_file_names(item, settings):
        """Return every primary IFC file name this item is expected to create."""
        view_names = item.views or (
            [settings.default_view_name] if settings.default_view_name else []
        )
        base_name = item.new_name or item.name
        if base_name.lower().endswith(".rvt"):
            base_name = base_name[:-4]
        return [
            base_name if view_name is None else "{}_{}".format(base_name, view_name)
            for view_name in (view_names or [None])
        ]

    @classmethod
    def find_primary_export_collisions(cls, items, settings):
        """Find selected models that would write the same primary IFC file."""
        targets = {}
        collisions = []
        for item in items:
            folder = os.path.normcase(os.path.abspath(item.export_path))
            for file_name in cls.export_file_names(item, settings):
                target = os.path.normcase(os.path.join(folder, file_name))
                previous = targets.get(target)
                if previous is not None:
                    collisions.append((target, previous, item.source_path))
                else:
                    targets[target] = item.source_path
        return collisions

    def _save_or_sync(self, document):
        try:
            save_sync_and_relinquish(document, "Batch IFC Export")
        except Exception as ex:
            if self.logger:
                self.logger.warning(
                    S("ifc.result.save_sync_failed", document.Title, ex)
                )

    def _export_linked_documents(self, document, export_path, settings, results):
        links = DB.FilteredElementCollector(document).OfClass(DB.RevitLinkInstance)
        for link_instance in links.WhereElementIsNotElementType().ToElements():
            link_document = link_instance.GetLinkDocument()
            if link_document is None:
                results.append(
                    (link_instance.Name, "link", S("ifc.result.link_not_loaded"))
                )
                continue
            try:
                options = self.build_options(settings, "", None)
                with WrappedTransaction(
                    link_document, "Export linked IFC", warning_suppressor=True
                ):
                    exported = link_document.Export(
                        export_path, link_document.Title, options
                    )
                results.append(
                    (
                        link_document.Title,
                        "link",
                        "OK"
                        if exported
                        else S("ifc.result.export_returned_failure"),
                    )
                )
            except Exception as ex:
                results.append(
                    (
                        link_document.Title,
                        "link",
                        S("ifc.result.export_failed", ex),
                    )
                )

    def export_item(self, item, settings):
        results = []
        if settings.open_without_links and (
            settings.export_links_merged or settings.export_links_separately
        ):
            return [
                (
                    item.name,
                    "-",
                    S("ifc.result.links_conflict"),
                )
            ]
        try:
            with OpenedBatchDocument(
                self.document_opener, item.source_path, settings.open_without_links
            ) as document:
                try:
                    if not os.path.isdir(item.export_path):
                        os.makedirs(item.export_path)
                except Exception as ex:
                    return [
                        (item.name, "-", S("ifc.result.folder_failed", ex))
                    ]

                view_names = item.views or (
                    [settings.default_view_name] if settings.default_view_name else []
                )
                file_names = self.export_file_names(item, settings)

                for index, (label, view) in enumerate(
                    self.resolve_views(document, view_names)
                ):
                    if view_names and view is None:
                        results.append(
                            (item.name, label, S("ifc.result.view_not_found"))
                        )
                        continue
                    file_name = file_names[index]
                    try:
                        with WrappedTransaction(
                            document, "Export IFC", warning_suppressor=True
                        ):
                            exported = document.Export(
                                item.export_path,
                                file_name,
                                self.build_options(settings, item.mapping_file, view),
                            )
                        results.append(
                            (
                                item.name,
                                label or S("ifc.result.default_view"),
                                "OK"
                                if exported
                                else S("ifc.result.export_returned_failure"),
                            )
                        )
                    except Exception as ex:
                        results.append(
                            (
                                item.name,
                                label or S("ifc.result.default_view"),
                                S("ifc.result.export_failed", ex),
                            )
                        )

                if settings.export_links_separately:
                    self._export_linked_documents(
                        document, item.export_path, settings, results
                    )
                if settings.save_after:
                    self._save_or_sync(document)
        except Exception as ex:
            results.append((item.name, "-", S("ifc.result.open_failed", ex)))
        return results
