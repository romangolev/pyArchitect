# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

__doc__ = """Создаёт 3D виды на основе связанных файлов.\
/Create 3D views based on worksets."""
__author__ = 'Roman Golev'
__title__ = "Links\n3D Views"

import clr
clr.AddReference("System")

import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import ElementId
from pyrevit import forms
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument  # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application

# TODO: Scan for views which already exist in a project

class LinksError(Exception):
    def __init__(self, msg):
        self.msg = msg

def collect_links(doc):
    cl = DB.FilteredElementCollector(doc) \
            .OfCategory(DB.BuiltInCategory.OST_RvtLinks) \
            .ToElements()
            # .OfClass(RevitLinkType) \
    return cl

def findlinks():
    links = collect_links(doc)
    if links.Count == 0:
        return False
    elif links.Count > 0: 
        return True

def get_viewFamTypeId(doc):
    collector3d = DB.FilteredElementCollector(doc).\
    OfClass(DB.ViewFamilyType).ToElements()
    for el in collector3d:
        if el.ViewFamily == DB.ViewFamily.ThreeDimensional:
            viewFamTypeId = el.Id
            return viewFamTypeId

def create3D(links):
    element_collection = (List[ElementId](li.Id for li in links)) # type: ignore
    for l in links:
        el = doc.GetElement(l.Id)
        if l.GetType().ToString() == "Autodesk.Revit.DB.RevitLinkInstance" :
            view3d = DB.View3D.CreateIsometric(doc, get_viewFamTypeId(doc))
            try:
                view3d.Name = l.GetLinkDocument().Title
            except:
                raise LinksError("Project already have a view of the name of a link. Please delete all the names that correspond with rvt imports and run again.")
            element_collection.Remove(l.GetTypeId())
            element_collection.Remove(l.Id)
            if (element_collection.Count != 0):
                view3d.HideElements(element_collection)
            element_collection.Add(l.GetTypeId())
            element_collection.Add(l.Id)

def main():

    if findlinks() == True:
        t = DB.Transaction(doc)
        t.Start('Create 3D')
        try:
            create3D(collect_links(doc))
            t.Commit()
        except LinksError as e:
            t.RollBack()
            t.Dispose()
            forms.alert(e.msg)
        except:
            t.RollBack()
            t.Dispose()
    else:
        forms.alert("There are no links in file")

if __name__ == '__main__':
    main()