# -*- coding: utf-8 -*-
"""Canonical creation and update logic for a Navisworks 3D view."""

import Autodesk.Revit.DB as DB
from System.Collections.Generic import List

from tools.navis.profiles import load_profiles
from tools.navis.settings import load as load_settings


# The legacy Navis command used Fine category overrides for components that
# would otherwise lose fittings, insulation or device geometry at Medium view
# detail.  Resolve the category names at runtime so one unavailable category
# does not prevent the rest of the view from being configured.
FINE_DETAIL_CATEGORIES = (
    "OST_PipeCurves",
    "OST_PlaceHolderPipes",
    "OST_PipeInsulations",
    "OST_PipeFitting",
    "OST_PipeAccessory",
    "OST_MechanicalEquipment",
    "OST_DuctTerminal",
    "OST_PlumbingFixtures",
    "OST_DuctAccessory",
    "OST_FlexPipeCurves",
    "OST_FlexDuctCurves",
    "OST_LightingFixtures",
    "OST_LightingDevices",
    "OST_Conduit",
    "OST_ConduitFitting",
)
TRANSPARENT_CATEGORIES = ("OST_Walls", "OST_CurtainWallPanels")
STRUCTURAL_SYMBOL_SUBCATEGORY_NAMES = (
    "Symbol",
    u"\u041e\u0431\u043e\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435",
)


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
        """Keep one exact configured view without touching other Navis views.

        Must be called inside an open Revit transaction.
        """
        exact_matches = self.find_exact()
        if exact_matches and not recreate:
            keeper = exact_matches[0]
            for duplicate in exact_matches[1:]:
                self.document.Delete(duplicate.Id)
            self.configure(keeper, profile, hidden_worksets)
            return keeper, "UPDATED"

        # Recreating is intentionally limited to the configured canonical name.
        # Other views may include "Navis" in their name but belong to users or
        # other workflows and must not be deleted by this batch operation.
        for view in exact_matches:
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
        # A template controls view properties and makes Revit ignore or reject
        # changes such as detail level and display style.  Clear it first when
        # the setting requests a self-contained Navis view.
        if self.settings.remove_view_template:
            self._remove_view_template(view)

        self._set_enum_property(
            view, "DetailLevel", DB.ViewDetailLevel, self.settings.detail_level
        )
        self._set_enum_property(
            view, "DisplayStyle", DB.DisplayStyle, self.settings.display_style
        )
        self._set_property(
            view, "AreAnnotationCategoriesHidden", self.settings.hide_annotations
        )
        self._set_property(
            view,
            "AreAnalyticalModelCategoriesHidden",
            self.settings.hide_analytical_models,
        )
        self._set_property(view, "AreImportCategoriesHidden", self.settings.hide_imports)
        self._set_property(
            view, "ArePointCloudsHidden", self.settings.hide_point_clouds
        )
        self._set_property(
            view,
            "AreCoordinationModelHandlesHidden",
            self.settings.hide_coordination_models,
        )

        if self.settings.apply_fine_mep_detail:
            self._set_fine_mep_detail(view)
        self._set_surface_transparency(view, self.settings.surface_transparency)

        hidden_categories = self.profiles.always_hidden_categories + list(
            self.profiles.hidden_categories(profile or self.settings.profile)
        )
        for built_in_category in hidden_categories:
            self._hide_category(view, built_in_category)
        if self.settings.hide_centerlines:
            for built_in_category in self.profiles.centerline_categories:
                self._hide_centerline(view, built_in_category)
        if self.settings.hide_structural_connection_symbols:
            self._hide_named_subcategories(
                view,
                getattr(DB.BuiltInCategory, "OST_StructConnections", None),
                STRUCTURAL_SYMBOL_SUBCATEGORY_NAMES,
            )

        if self.settings.hide_revit_links:
            self._hide_revit_links(view)
        self._hide_worksets(view, hidden_worksets or [])

    @staticmethod
    def _set_property(view, name, value):
        """Set a version-dependent Revit view property without aborting a run."""
        try:
            setattr(view, name, value)
        except Exception:
            pass

    @staticmethod
    def _set_enum_property(view, property_name, enum_type, enum_name):
        try:
            setattr(view, property_name, getattr(enum_type, enum_name))
        except Exception:
            pass

    @staticmethod
    def _remove_view_template(view):
        try:
            parameter = view.get_Parameter(DB.BuiltInParameter.VIEW_TEMPLATE)
            if parameter is not None and not parameter.IsReadOnly:
                parameter.Set(DB.ElementId.InvalidElementId)
        except Exception:
            pass

    def _set_fine_mep_detail(self, view):
        for category_name in FINE_DETAIL_CATEGORIES:
            category = self._category_by_name(category_name)
            if category is None:
                continue
            try:
                override = DB.OverrideGraphicSettings()
                override.SetDetailLevel(DB.ViewDetailLevel.Fine)
                view.SetCategoryOverrides(category.Id, override)
            except Exception:
                pass

    def _set_surface_transparency(self, view, transparency):
        try:
            transparency = max(0, min(100, int(transparency)))
        except (TypeError, ValueError):
            return
        for category_name in TRANSPARENT_CATEGORIES:
            category = self._category_by_name(category_name)
            if category is None:
                continue
            try:
                override = DB.OverrideGraphicSettings()
                override.SetSurfaceTransparency(transparency)
                view.SetCategoryOverrides(category.Id, override)
            except Exception:
                pass

    def _category(self, built_in_category):
        try:
            return DB.Category.GetCategory(self.document, built_in_category)
        except Exception:
            return None

    def _category_by_name(self, category_name):
        try:
            built_in_category = getattr(DB.BuiltInCategory, category_name)
        except Exception:
            return None
        return self._category(built_in_category)

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
        self._hide_named_subcategories(
            view, built_in_category, self.profiles.centerline_subcategory_names
        )

    def _hide_named_subcategories(self, view, built_in_category, names):
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
