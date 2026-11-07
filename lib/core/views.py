# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import Autodesk.Revit.DB as DB


def view_types(doc):
    """Return every view family type of the document."""
    return DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType) \
        .ToElements()


def view_type_3d(doc):
    """Return the first 3D view family type of the document, or None."""
    for view_type in view_types(doc):
        if view_type.ViewFamily == DB.ViewFamily.ThreeDimensional:
            return view_type
    return None
