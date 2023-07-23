# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.DB import CategoryType

class CustomISelectionFilterByIdInclude(ISelectionFilter):
    def __init__(self, category_ids=None):
        if category_ids is None:
            self.allowed_categories = None
        else:
            self.allowed_categories = category_ids

    def AllowElement(self, element):
        if self.allowed_categories is None:
            return True
        elif element.Category.Id.IntegerValue in self.allowed_categories:
            return True
        else:
            return False

    def AllowReference(self, reference, point):
        return True

class CustomISelectionFilterByIdExclude(ISelectionFilter):
    def __init__(self, category_ids=None):
        if category_ids is None:
            self.allowed_categories = None
        else:
            self.allowed_categories = category_ids

    def AllowElement(self, element):
        if self.allowed_categories is None:
            return False
        elif element.Category.Id.IntegerValue in self.allowed_categories:
            return False
        else:
            return True

    def AllowReference(self, reference, point):
        return True

class CustomISelectionFilterByNameInclude(ISelectionFilter):
    def __init__(self, nom_categorie):
        self.nom_categorie = nom_categorie
    def AllowElement(self, e):
        if e.Category.Name == self.nom_categorie:
            return True
        else:
            return False
    def AllowReference(self, ref, point):
        return True
    

class CustomISelectionFilterModelCats(ISelectionFilter):
    def __init__(self, doc):
        self.doc = doc
        self.allcategories = self.doc.Settings.Categories

    def AllowElement(self, e):
        if e.CategoryType == CategoryType.Model in self.allcategories:
            return True
        else:
            return False
        
    def AllowReference(self, ref, point):
        return True