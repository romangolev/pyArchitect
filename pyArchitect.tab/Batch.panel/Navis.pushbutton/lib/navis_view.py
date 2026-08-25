# -*- coding: utf-8 -*-
"""Compatibility adapter for the shared pyArchitect Navisworks view service."""

from Autodesk.Revit.DB import Transaction

from statuses import CREATED, UPDATED
from profiles import PROFILE_CATEGORIES
from view_settings import (
    CENTERLINE_SUBCATEGORY,
    CENTERLINE_CATEGORIES,
    UNIVERSAL_HIDDEN_CATEGORIES)
from tools.navis.settings import load
from tools.navis.views import NavisworksViewService


def _service(document):
    return NavisworksViewService(
        document,
        load(),
        profile_categories=PROFILE_CATEGORIES,
        universal_hidden_categories=UNIVERSAL_HIDDEN_CATEGORIES,
        centerline_categories=CENTERLINE_CATEGORIES,
        centerline_name=CENTERLINE_SUBCATEGORY)


def get_navisworks_view(document):
    return _service(document).find()


def has_navisworks_view(document):
    return get_navisworks_view(document) is not None


def delete_navisworks_view(document):
    return _service(document).delete()


def create_navisworks_view(document, profile="UNIVERSAL", hidden_worksets=None):
    return _service(document).create(profile, hidden_worksets)


def update_navisworks_view(document, profile="UNIVERSAL", hidden_worksets=None):
    return _service(document).update(profile, hidden_worksets)


def create_or_replace_navisworks_view(document, profile, hidden_worksets=None,
                                      recreate=True):
    service = _service(document)
    updated = service.find() is not None
    transaction = Transaction(document, "Update Navisworks View")
    transaction.Start()
    try:
        _, operation = service.reconcile(profile, hidden_worksets, recreate)
        transaction.Commit()
    except Exception:
        transaction.RollBack()
        raise
    return UPDATED if operation == "UPDATED" else CREATED
