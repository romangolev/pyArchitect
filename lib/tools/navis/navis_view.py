# -*- coding: utf-8 -*-
"""Compatibility API for batch Navisworks view processing.

The batch processor uses these function names while the implementation lives
in :mod:`views` as ``NavisworksViewService``.
"""

from Autodesk.Revit.DB import Transaction

from tools.navis.profiles import PROFILE_CATEGORIES
from tools.navis.settings import load
from tools.navis.view_settings import (
    CENTERLINE_CATEGORIES,
    CENTERLINE_SUBCATEGORY,
    UNIVERSAL_HIDDEN_CATEGORIES,
)
from tools.navis.views import NavisworksViewService


def _get_service(document):
    return NavisworksViewService(
        document,
        load(),
        PROFILE_CATEGORIES,
        UNIVERSAL_HIDDEN_CATEGORIES,
        CENTERLINE_CATEGORIES,
        CENTERLINE_SUBCATEGORY,
    )


def has_navisworks_view(document):
    """Return whether the configured Navisworks view already exists."""
    return _get_service(document).find() is not None


def create_or_replace_navisworks_view(
    document, profile, hidden_worksets, recreate=False
):
    """Create or update the configured Navisworks view in one transaction."""
    transaction = Transaction(document, "Create or update Navisworks view")
    started = False

    try:
        transaction.Start()
        started = True

        _, status = _get_service(document).reconcile(profile, hidden_worksets, recreate)

        transaction.Commit()
        return status

    except:
        if started:
            try:
                transaction.RollBack()
            except:
                pass
        raise
