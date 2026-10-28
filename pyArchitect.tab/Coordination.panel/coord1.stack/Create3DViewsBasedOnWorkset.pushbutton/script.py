# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")
import Autodesk
import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB import FilteredWorksetCollector
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument  # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application
t = DB.Transaction(doc)

worksets = []

if doc.IsWorkshared == True:
    wsCollector = FilteredWorksetCollector(doc).ToWorksets()
    for workset in  wsCollector:
        if workset.Kind == DB.WorksetKind.UserWorkset:
            worksets.append(workset)
        else:
            pass
else:
    forms.alert("File is not workshared")

collector3d = DB.FilteredElementCollector(doc).\
OfClass(Autodesk.Revit.DB.ViewFamilyType).ToElements()
for el in collector3d:
    if el.ViewFamily == DB.ViewFamily.ThreeDimensional:
        viewFamTypeId = el.Id

views3d = []
def create3D(worksets):
    for ws in worksets:
        view3d = DB.View3D.CreateIsometric(doc, viewFamTypeId)
        #views3d.append(view3d)
        try:
            view3d.Name = ws.Name
            for ws in worksets:
                if view3d.Name ==  ws.Name:
                    view3d.SetWorksetVisibility(ws.Id, DB.WorksetVisibility.Visible)
                else:
                    view3d.SetWorksetVisibility(ws.Id, DB.WorksetVisibility.Hidden)
        except:
            doc.Delete(view3d.Id)


def main():
    try:
        t.Start('Create 3D')
        create3D(worksets)
        t.Commit()
    except:
        t.RollBack()
        t.Dispose()
        forms.alert("Error occured")


if __name__ == '__main__':
    main()