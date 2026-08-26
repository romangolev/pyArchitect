# -*- coding: utf-8 -*-
import os

from Autodesk.Revit.DB import (

    BasicFileInfo,

    OpenOptions,

    WorksetConfiguration,

    WorksetConfigurationOption,

    DetachFromCentralOption,

    ModelPathUtils

)

# ==========================================================
# SERVER PATH
# ==========================================================

def is_server_path(file_path):

    return (
        file_path
        .strip()
        .upper()
        .startswith("RSN://")
    )


# ==========================================================
# FILE INFO
# ==========================================================

def get_file_info(file_path):

    # BasicFileInfo работает
    # только с локальными RVT

    if is_server_path(file_path):

        return None

    try:

        return BasicFileInfo.Extract(
            file_path
        )

    except:

        return None

# ==========================================================
# MODEL TYPE
# ==========================================================

def is_workshared(file_path):

    info = get_file_info(
        file_path
    )

    if not info:

        return False

    try:

        return info.IsWorkshared

    except:

        return False


def is_central(file_path):

    info = get_file_info(
        file_path
    )

    if not info:

        return False

    try:

        return info.IsCentral

    except:

        return False


# ==========================================================
# OPEN OPTIONS
# ==========================================================

def create_open_options():

    options = OpenOptions()

    options.DetachFromCentralOption = \
        DetachFromCentralOption.DoNotDetach

    ws_config = WorksetConfiguration(

        WorksetConfigurationOption.CloseAllWorksets

    )

    options.SetOpenWorksetsConfiguration(
        ws_config
    )

    return options


# ==========================================================
# OPENED DOCUMENT
# ==========================================================

def get_open_document(app, file_path):

    try:
        target = ModelPathUtils.ConvertUserVisiblePathToModelPath(file_path)
        target = ModelPathUtils.ConvertModelPathToUserVisiblePath(target).upper()
    except:
        target = file_path.replace("\\", "/").upper()

    for doc in app.Documents:

        try:
            current = doc.GetWorksharingCentralModelPath()

            if current:
                current = ModelPathUtils.ConvertModelPathToUserVisiblePath(current).upper()
            else:
                current = doc.PathName.replace("\\", "/").upper()

            if current == target:
                return doc

        except:
            pass

    return None

# ==========================================================
# OPEN DOCUMENT
# ==========================================================

def open_document(
        app,
        file_path):

    doc = get_open_document(
        app,
        file_path
    )

    if doc:

        return doc, False

    options = create_open_options()

    model_path = \
        ModelPathUtils.ConvertUserVisiblePathToModelPath(
            file_path
        )

    doc = app.OpenDocumentFile(
        model_path,
        options
    )

    return doc, True

# ==========================================================
# UPGRADE
# ==========================================================

def requires_upgrade(file_path):

    if is_server_path(file_path):

        return False

    info = get_file_info(
        file_path
    )

    if not info:

        return False

    try:

        return info.IsSavedInLaterVersion

    except:

        return False
