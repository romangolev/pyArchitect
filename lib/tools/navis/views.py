# -*- coding: utf-8 -*-
"""Canonical creation and update logic for a Navisworks 3D view."""

import Autodesk.Revit.DB as DB
from System.Collections.Generic import List


class NavisworksViewService(object):
    def __init__(self, document, settings, profile_categories=None,
                 universal_hidden_categories=None, centerline_categories=None,
                 centerline_name=None):
        self.document = document
        self.settings = settings
        self.profile_categories = profile_categories or {}
        self.universal_hidden_categories = universal_hidden_categories or []
        self.centerline_categories = centerline_categories or []
        self.centerline_name = centerline_name

    def find(self):
        matches = self.find_exact()
        return matches[0] if matches else None

    def find_exact(self):
        return [view for view in self._views()
                if view.Name == self.settings.view_name]

    def find_navis_named(self):
        return [view for view in self._views()
                if "navis" in view.Name.lower()]

    def _views(self):
        return [view for view in DB.FilteredElementCollector(self.document).OfClass(DB.View3D)
                if not view.IsTemplate]

    def reconcile(self, profile=None, hidden_worksets=None, recreate=False):
        """Keep one exact view; remove duplicates or obsolete Navis-named views.

        Must be called inside an open Revit transaction.
        """
        exact_matches = self.find_exact()
        if exact_matches and not recreate:
            keeper = exact_matches[0]
            for duplicate in exact_matches[1:]:
                self.document.Delete(duplicate.Id)
            self.configure(keeper, profile, hidden_worksets)
            return keeper, "UPDATED"

        targets = self.find_navis_named()
        for view in targets:
            self.document.Delete(view.Id)
        return self.create(profile, hidden_worksets), "CREATED"

    def create(self, profile=None, hidden_worksets=None):
        view_type = next((item for item in DB.FilteredElementCollector(self.document)
                          .OfClass(DB.ViewFamilyType)
                          if item.ViewFamily == DB.ViewFamily.ThreeDimensional), None)
        if view_type is None:
            raise Exception("3D ViewFamilyType not found")
        view = DB.View3D.CreateIsometric(self.document, view_type.Id)
        view.Name = self.settings.view_name
        self.configure(view, profile, hidden_worksets)
        return view

    def update(self, profile=None, hidden_worksets=None):
        view = self.find()
        if view is None:
            return False
        self.configure(view, profile, hidden_worksets)
        return True

    def delete(self):
        view = self.find()
        if view is None:
            return False
        self.document.Delete(view.Id)
        return True

    def configure(self, view, profile=None, hidden_worksets=None):
        view.DetailLevel = DB.ViewDetailLevel.Fine
        view.AreAnnotationCategoriesHidden = True
        view.AreAnalyticalModelCategoriesHidden = True
        view.AreImportCategoriesHidden = True
        view.ArePointCloudsHidden = True
        view.AreCoordinationModelHandlesHidden = True
        for bic in [DB.BuiltInCategory.OST_Mass, DB.BuiltInCategory.OST_Parts,
                    DB.BuiltInCategory.OST_Lines, DB.BuiltInCategory.OST_MassForm] + \
                self.universal_hidden_categories + self.profile_categories.get(
                profile or self.settings.profile, []):
            self._hide_category(view, bic)
        for bic in self.centerline_categories:
            self._hide_centerline(view, bic)
        if self.settings.hide_revit_links:
            self._hide_revit_links(view)
        self._hide_worksets(view, hidden_worksets or [])

    def _hide_category(self, view, bic):
        try:
            category = DB.Category.GetCategory(self.document, bic)
            if category:
                view.SetCategoryHidden(category.Id, True)
        except Exception:
            pass

    def _hide_centerline(self, view, bic):
        if not self.centerline_name:
            return
        try:
            category = DB.Category.GetCategory(self.document, bic)
            if category:
                for subcategory in category.SubCategories:
                    if subcategory.Name == self.centerline_name:
                        view.SetCategoryHidden(subcategory.Id, True)
        except Exception:
            pass

    def _hide_revit_links(self, view):
        try:
            ids = List[DB.ElementId]()
            for link_type in DB.FilteredElementCollector(self.document).OfClass(DB.RevitLinkType):
                ids.Add(link_type.Id)
            if ids.Count:
                view.HideElements(ids)
        except Exception:
            pass

    def _hide_worksets(self, view, keywords):
        keywords = [value.strip().lower() for value in keywords if len(value.strip()) >= 2]
        try:
            for workset in DB.FilteredWorksetCollector(self.document).OfKind(DB.WorksetKind.UserWorkset):
                if any(value in workset.Name.lower() for value in keywords):
                    view.SetWorksetVisibility(workset.Id, DB.WorksetVisibility.Hidden)
        except Exception:
            pass
