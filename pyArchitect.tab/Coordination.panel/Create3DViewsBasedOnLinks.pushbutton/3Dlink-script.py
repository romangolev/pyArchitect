# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

__doc__ = """Создаёт 3D виды на основе связанных файлов.\
/Create 3D views based on worksets."""
__author__ = 'Roman Golev'
__title__ = "Links\n3D Views"

import sys 
import clr
clr.AddReference("RevitAPI")
clr.AddReference("System")

import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB import AssemblyViewUtils
from Autodesk.Revit.DB import FilteredElementCollector

clr.AddReference('RevitAPIUI')
from pyrevit import forms
from collections import namedtuple

import System
from System.Collections.Generic import *

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)

def collect_links(doc):
    cl = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_RvtLinks) \
            .ToElements()
            # .OfClass(RevitLinkType) \
    return cl

def findlinks():
    links= collect_links(doc)
    if links.Count == 0:
        return False
    elif links.Count > 0: 
        return True

def get_viewFamTypeId(doc):
    collector3d = FilteredElementCollector(doc).\
    OfClass(Autodesk.Revit.DB.ViewFamilyType).ToElements()
    for el in collector3d:
        if el.ViewFamily == ViewFamily.ThreeDimensional:
            viewFamTypeId = el.Id
            return viewFamTypeId

def create3D(links):
    element_collection = (List[ElementId](li.Id for li in links))
    for l in links:
        print(l, l.Id)
        el = doc.GetElement(l.Id)
        if l.GetType().ToString() == "Autodesk.Revit.DB.RevitLinkInstance" :
            view3d = View3D.CreateIsometric(doc, get_viewFamTypeId(doc))
            view3d.Name = l.GetLinkDocument().Title
            print(element_collection)
            element_collection.Remove(l.GetTypeId())
            element_collection.Remove(l.Id)
            print(element_collection)
            view3d.HideElements(element_collection)
            element_collection.Add(l.GetTypeId())
            element_collection.Add(l.Id)

def main():
    if findlinks() == True:
        t.Start('Create 3D')
        create3D(collect_links(doc))
        t.Commit()
    else:
        forms.alert("There are no links in file")

if __name__ == '__main__':
    main()