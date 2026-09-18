# -*- coding: utf-8 -*-
"""Picking Revit Server models through Revit's own Open dialog.

The Revit API does not expose Revit Server's browser as a picker, but
``FileOpenDialog`` is documented as matching Revit's Open dialog and hands back
a ``ModelPath`` that can be a ``ServerPath``.  That is enough to let the user
browse the server the way they already know and read the route back out.
"""

from pyrevit import HOST_APP

from Autodesk.Revit.DB import ModelPathUtils
from Autodesk.Revit.UI import FileOpenDialog, ItemSelectionDialogResult


MODEL_FILTER = "Revit Models (*.rvt)|*.rvt"


def available_hosts():
    """Revit Server hosts the running Revit is configured to reach.

    Revit reads these from ``RSN.ini``; an empty list means its Open dialog has
    no server to offer.
    """
    try:
        return list(HOST_APP.available_servers)
    except Exception:
        return []


def pick_server_model(title="Select a Revit Server model"):
    """Show Revit's Open dialog and return the picked ``RSN://`` route.

    Returns None when the user cancels, and raises ValueError when they pick a
    model that is not on a Revit Server, so the caller can say where local
    models belong instead.
    """
    dialog = FileOpenDialog(MODEL_FILTER)
    model_path = None
    try:
        dialog.Title = title
        if dialog.Show() != ItemSelectionDialogResult.Confirmed:
            return None

        model_path = dialog.GetSelectedModelPath()
        if not model_path.ServerPath:
            raise ValueError(
                ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
            )
        return ModelPathUtils.ConvertModelPathToUserVisiblePath(model_path)
    finally:
        _dispose(model_path)
        _dispose(dialog)


def _dispose(disposable):
    if disposable is None:
        return
    try:
        disposable.Dispose()
    except Exception:
        pass
