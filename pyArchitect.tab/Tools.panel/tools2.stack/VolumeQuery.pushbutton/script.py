# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys
import Autodesk.Revit.DB as DB
from core.selectionhelpers import CustomISelectionFilterByIdInclude, ID_WALLS
from Autodesk.Revit.UI.Selection import ObjectType

doc = __revit__.ActiveUIDocument.Document           # type: ignore
uidoc = __revit__.ActiveUIDocument                  # type: ignore
uiapp = __revit__                                   # type: ignore
app = uiapp.Application
t = DB.Transaction(doc)

versionNumber = uiapp.Application.VersionNumber
if int(versionNumber) < 2021:
    from Autodesk.Revit.DB import UnitUtils
elif int(versionNumber) >= 2021:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId
else:
        from Autodesk.Revit.DB import UnitUtils, UnitTypeId

categories = doc.Settings.Categories
n = categories.Size

# Get unput: selected by user elements
def get_selection():
    selobject = uidoc.Selection.GetElementIds()
    if selobject.Count == 0:
        try:
            selection = uidoc.Selection.PickObjects(ObjectType.Element,
                                                    CustomISelectionFilterByIdInclude(ID_WALLS),
                                                    "Selection Objects")
        except:
            sys.exit()
    elif selobject.Count != 0:
        selection = selobject
    return selection


selobject = get_selection()
volumes = []

def get_host_volume(elem):
    vl = elem.get_Parameter(DB.BuiltInParameter.HOST_VOLUME_COMPUTED).AsDouble()
    if int(versionNumber) < 2020 : 
        return UnitUtils.ConvertToInternalUnits(vl, DB.DisplayUnitType.DUT_CUBIC_METERS)
    if int(versionNumber) >= 2021: 
        return UnitUtils.ConvertFromInternalUnits(vl, UnitTypeId.CubicMeters)

def get_ifc_volume(el):
    geo = el.get_Geometry(DB.Options())
    vl = 0
    for i in geo:
        if "Solid" in i.ToString():
            if int(versionNumber) < 2020 : 
                vl += UnitUtils.ConvertToInternalUnits(i.Volume, DB.DisplayUnitType.DUT_CUBIC_METERS)
            if int(versionNumber) >= 2021: 
                vl += UnitUtils.ConvertFromInternalUnits(i.Volume, UnitTypeId.CubicMeters)
    return vl



if selobject.Count == 0:
    print('Nothing selected')
elif selobject.Count != 0:
    for element in selobject:
        el = doc.GetElement(element)
        try:
            vol = get_host_volume(el)
            if float(vol) == 0.0:
                raise ValueError
            volumes.append(vol)
            print(vol)
        except ValueError:
            try:
                vol = get_ifc_volume(el)
                print(vol)
                volumes.append(vol)
            except:
                print("Couldn't get the volume of element {}".format(el.Id))
        except:
            print("Couldn't get the volume of element {}".format(el.Id))


print("Summary : {}".format(sum(volumes)) + " m³")

#TODO: Add option to calculate volume in case if it is no Volume property in model
# Based on Geometry