# -*- coding: utf-8 -*-
"""Canonical creation and update logic for a Navisworks 3D view."""

import Autodesk.Revit.DB as DB
from System.Collections.Generic import List

from tools.navis.profiles import load_profiles
from tools.navis.settings import load as load_settings


class NavisworksViewService(object):
    def __init__(self, document, settings=None, profiles=None):
        self.document = document
        self.settings = settings or load_settings()
        self.profiles = profiles or load_profiles()

    def find(self):
        matches = self.find_exact()
        return matches[0] if matches else None

    def find_exact(self):
        return [view for view in self._views() if view.Name == self.settings.view_name]

    def find_navis_named(self):
        return [view for view in self._views() if "navis" in view.Name.lower()]

    def _views(self):
        return [
            view
            for view in DB.FilteredElementCollector(self.document).OfClass(DB.View3D)
            if not view.IsTemplate
        ]

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
        view_type = next(
            (
                item
                for item in DB.FilteredElementCollector(self.document).OfClass(
                    DB.ViewFamilyType
                )
                if item.ViewFamily == DB.ViewFamily.ThreeDimensional
            ),
            None,
        )
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

        hidden_categories = self.profiles.always_hidden_categories + list(
            self.profiles.hidden_categories(profile or self.settings.profile)
        )
        for built_in_category in hidden_categories:
            self._hide_category(view, built_in_category)
        for built_in_category in self.profiles.centerline_categories:
            self._hide_centerline(view, built_in_category)

        if self.settings.hide_revit_links:
            self._hide_revit_links(view)
        self._hide_worksets(view, hidden_worksets or [])

    def _category(self, built_in_category):
        try:
            return DB.Category.GetCategory(self.document, built_in_category)
        except Exception:
            return None

    @staticmethod
    def _hide(view, category_id):
        try:
            view.SetCategoryHidden(category_id, True)
        except Exception:
            pass

    def _hide_category(self, view, built_in_category):
        category = self._category(built_in_category)
        if category is not None:
            self._hide(view, category.Id)

    def _hide_centerline(self, view, built_in_category):
        names = self.profiles.centerline_subcategory_names
        category = self._category(built_in_category)
        if category is None or not names:
            return
        try:
            subcategories = list(category.SubCategories)
        except Exception:
            return
        for subcategory in subcategories:
            if subcategory.Name in names:
                self._hide(view, subcategory.Id)

    def _hide_revit_links(self, view):
        try:
            ids = List[DB.ElementId]()
            for link_type in DB.FilteredElementCollector(self.document).OfClass(
                DB.RevitLinkType
            ):
                ids.Add(link_type.Id)
            if ids.Count:
                view.HideElements(ids)
        except Exception:
            pass

    def _hide_worksets(self, view, keywords):
        keywords = [
            value.strip().lower() for value in keywords if len(value.strip()) >= 2
        ]
        if not keywords:
            return
        try:
            for workset in DB.FilteredWorksetCollector(self.document).OfKind(
                DB.WorksetKind.UserWorkset
            ):
                if any(value in workset.Name.lower() for value in keywords):
                    view.SetWorksetVisibility(workset.Id, DB.WorksetVisibility.Hidden)
        except Exception:
            pass
