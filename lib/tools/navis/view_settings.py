# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import BuiltInCategory, ViewDetailLevel

from Autodesk.Revit.DB import *
from System.Collections.Generic import List

CENTERLINE_SUBCATEGORY = "Осевая линия"


STANDARD_HIDDEN_CATEGORIES = [
    BuiltInCategory.OST_Mass,
    BuiltInCategory.OST_Parts,
    BuiltInCategory.OST_Lines,
]


UNIVERSAL_HIDDEN_CATEGORIES = [
    BuiltInCategory.OST_Site,
    BuiltInCategory.OST_MEPSpaces,
    BuiltInCategory.OST_Wire,
]


CENTERLINE_CATEGORIES = [
    BuiltInCategory.OST_DuctCurves,
    BuiltInCategory.OST_FlexDuctCurves,
    BuiltInCategory.OST_PipeCurves,
    BuiltInCategory.OST_FlexPipeCurves,
    BuiltInCategory.OST_CableTray,
    BuiltInCategory.OST_Conduit,
    BuiltInCategory.OST_DuctFitting,
    BuiltInCategory.OST_PipeFitting,
    BuiltInCategory.OST_ConduitFitting,
    BuiltInCategory.OST_CableTrayFitting,
]


def apply_basic_view_settings(view):

    view.DetailLevel = ViewDetailLevel.Fine

    view.AreAnnotationCategoriesHidden = True

    view.AreAnalyticalModelCategoriesHidden = True

    view.AreImportCategoriesHidden = True

    view.ArePointCloudsHidden = True

    view.AreCoordinationModelHandlesHidden = True


def hide_standard_categories(doc, view):

    for bic in STANDARD_HIDDEN_CATEGORIES:
        try:
            cat = Category.GetCategory(doc, bic)

            if cat:
                view.SetCategoryHidden(cat.Id, True)

        except:
            pass


def hide_mass_form(doc, view):

    try:
        cat = Category.GetCategory(doc, BuiltInCategory.OST_MassForm)

        if cat:
            view.SetCategoryHidden(cat.Id, True)

    except:
        pass


def hide_revit_links(doc, view):

    try:
        ids = List[ElementId]()

        for lt in FilteredElementCollector(doc).OfClass(RevitLinkType):
            ids.Add(lt.Id)

        if ids.Count > 0:
            view.HideElements(ids)

    except:
        pass
