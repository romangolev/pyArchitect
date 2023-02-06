# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


__doc__ = """Создаёт 3D виды на основе видимости рабочих наборов.\
 /Create 3D views based on worksets."""
__author__ = 'Roman Golev'
__title__ = "Worksets\n3D Views"

import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB import AssemblyViewUtils
from Autodesk.Revit.DB import FilteredWorksetCollector
import System
clr.AddReference('RevitAPIUI')
import pyrevit
from pyrevit import forms
from collections import namedtuple

import rpw
from rpw import db

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)

worksets = []

if doc.IsWorkshared == True:
    wsCollector = FilteredWorksetCollector(doc).ToWorksets()
    for workset in  wsCollector:
        if workset.Kind == Autodesk.Revit.DB.WorksetKind.UserWorkset:
            worksets.append(workset)
        else:
            pass
else:
    forms.alert("File is not workshared")

collector3d = FilteredElementCollector(doc).\
OfClass(Autodesk.Revit.DB.ViewFamilyType).ToElements()
for el in collector3d:
    if el.ViewFamily == ViewFamily.ThreeDimensional:
        viewFamTypeId = el.Id

views3d = []
def create3D(worksets):
    for ws in worksets:
        view3d = View3D.CreateIsometric(doc, viewFamTypeId)
        #views3d.append(view3d)
        try:
            view3d.Name = ws.Name
            for ws in worksets:
                if view3d.Name ==  ws.Name:
                    view3d.SetWorksetVisibility(ws.Id, WorksetVisibility.Visible)
                else:
                    view3d.SetWorksetVisibility(ws.Id, WorksetVisibility.Hidden)
        except:
            doc.Delete(view3d.Id)


def main():
    try:
        t.Start('Create 3D')
        create3D(worksets)
        t.Commit()
    except:
        t.RollBack()
        forms.alert("Error occured")


if __name__ == '__main__':
    main()