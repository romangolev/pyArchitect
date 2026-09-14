# -*- coding: utf-8 -*-
"""Opening and inspecting Revit models addressed by path."""

from Autodesk.Revit.DB import (
    BasicFileInfo,
    DetachFromCentralOption,
    ModelPathUtils,
    OpenOptions,
    WorksetConfiguration,
    WorksetConfigurationOption,
)


def is_server_path(file_path):
    return file_path.strip().upper().startswith("RSN://")


def normalize_path(file_path):
    try:
        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
        return ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path).upper()
    except Exception:
        return file_path.replace("\\", "/").upper()


def build_open_options(detach_from_central=False, open_all_worksets=False):
    options = OpenOptions()
    options.DetachFromCentralOption = (
        DetachFromCentralOption.DetachAndPreserveWorksets
        if detach_from_central
        else DetachFromCentralOption.DoNotDetach
    )
    options.SetOpenWorksetsConfiguration(
        WorksetConfiguration(
            WorksetConfigurationOption.OpenAllWorksets
            if open_all_worksets
            else WorksetConfigurationOption.CloseAllWorksets
        )
    )
    return options


def get_file_info(file_path):
    if is_server_path(file_path):
        return None
    try:
        return BasicFileInfo.Extract(file_path)
    except Exception:
        return None


def get_file_flag(file_path, attribute):
    info = get_file_info(file_path)
    if not info:
        return False
    try:
        return bool(getattr(info, attribute))
    except Exception:
        return False


class RevitDocumentRepository(object):
    """Reuses already-open documents and opens the rest on demand."""

    def __init__(self, application):
        self.application = application

    def find_open(self, file_path):
        target = normalize_path(file_path)
        for document in self.application.Documents:
            if self._document_key(document) == target:
                return document
        return None

    def open(self, file_path):
        document = self.find_open(file_path)
        if document:
            return document, False

        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
        return (
            self.application.OpenDocumentFile(model_path, build_open_options()),
            True,
        )

    def requires_upgrade(self, file_path):
        return get_file_flag(file_path, "IsSavedInLaterVersion")

    def is_workshared(self, file_path):
        return get_file_flag(file_path, "IsWorkshared")

    def is_central(self, file_path):
        return get_file_flag(file_path, "IsCentral")

    @staticmethod
    def _document_key(document):
        try:
            central_path = document.GetWorksharingCentralModelPath()
            if central_path:
                return ModelPathUtils.ConvertModelPathToUserVisiblePath(
                    central_path
                ).upper()
            return document.PathName.replace("\\", "/").upper()
        except Exception:
            return None
