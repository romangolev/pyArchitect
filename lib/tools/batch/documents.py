# -*- coding: utf-8 -*-
"""Safe Revit document opening primitives for batch commands."""

import os
import shutil
import tempfile

import Autodesk.Revit.DB as DB


class TemporaryLinklessCopy(object):
    """Disposable RVT copy whose Revit links are unloaded before opening."""

    def __init__(self, source_path):
        self.source_path = source_path
        self.folder = None
        self.path = None

    def prepare(self):
        self.folder = tempfile.mkdtemp(prefix="pyArchitect_Batch_")
        self.path = os.path.join(self.folder, os.path.basename(self.source_path))
        try:
            shutil.copy2(self.source_path, self.path)
            self._unload_revit_links(self.path)
            return self.path
        except Exception:
            self.dispose()
            raise

    def _unload_revit_links(self, path):
        model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(path)
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

    def dispose(self):
        if self.folder:
            shutil.rmtree(self.folder, ignore_errors=True)
            self.folder = None
            self.path = None


class RevitDocumentOpener(object):
    """Opens documents while suppressing the known Coordination Model warning."""

    def __init__(self, application, ui_application):
        self.application = application
        self.ui_application = ui_application

    @staticmethod
    def _dismiss_coordination_model_load_error(sender, args):
        try:
            dialog_text = "{} {}".format(
                getattr(args, "Message", ""),
                getattr(args, "DialogId", "")).lower()
            if ("unable to load coordination model" in dialog_text or
                    "coordinationmodel" in dialog_text):
                args.OverrideResult(1)  # IDOK
        except Exception:
            pass

    def open(self, source_path, detach_from_central=False):
        model_path = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(source_path)
        open_options = DB.OpenOptions()
        open_options.DetachFromCentralOption = (
            DB.DetachFromCentralOption.DetachAndPreserveWorksets
            if detach_from_central else
            DB.DetachFromCentralOption.DoNotDetach)
        open_options.SetOpenWorksetsConfiguration(
            DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenAllWorksets))

        self.ui_application.DialogBoxShowing += self._dismiss_coordination_model_load_error
        try:
            return self.application.OpenDocumentFile(model_path, open_options)
        finally:
            self.ui_application.DialogBoxShowing -= self._dismiss_coordination_model_load_error


def save_sync_and_relinquish(document, comment):
    """Persist a changed batch model and relinquish all owned workshared data."""
    if document.IsWorkshared:
        transact_options = DB.TransactWithCentralOptions()
        relinquish_options = DB.RelinquishOptions(True)
        sync_options = DB.SynchronizeWithCentralOptions()
        sync_options.SetRelinquishOptions(relinquish_options)
        sync_options.Comment = comment
        document.SynchronizeWithCentral(transact_options, sync_options)
        DB.WorksharingUtils.RelinquishOwnership(
            document, relinquish_options, transact_options)
    else:
        document.Save()


class OpenedBatchDocument(object):
    """Context manager that opens a batch model and always releases resources."""

    def __init__(self, opener, source_path, open_without_revit_links=False):
        self.opener = opener
        self.source_path = source_path
        self.open_without_revit_links = open_without_revit_links
        self.temporary_copy = None
        self.document = None

    def __enter__(self):
        path_to_open = self.source_path
        if self.open_without_revit_links:
            self.temporary_copy = TemporaryLinklessCopy(self.source_path)
            path_to_open = self.temporary_copy.prepare()

        self.document = self.opener.open(
            path_to_open,
            detach_from_central=self.temporary_copy is not None)
        return self.document

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if self.document:
            try:
                self.document.Close(False)
            except Exception:
                pass
        if self.temporary_copy:
            self.temporary_copy.dispose()
