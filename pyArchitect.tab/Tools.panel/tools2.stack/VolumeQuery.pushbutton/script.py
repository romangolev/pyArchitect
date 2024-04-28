# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


__doc__ = "Returns element Volume for a selected elements. Calculate totals in square meters"
__author__ = 'Roman Golev'
__title__ = "Volume\nQuery"


from types import NoneType
import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI import Selection

import sys

clr.AddReference('System')
clr.AddReference('RevitAPIUI')
import pyrevit
from pyrevit import forms
from System.Collections.Generic import List
from core.selectionhelpers import CustomISelectionFilterByIdInclude, ID_WALLS
from Autodesk.Revit.UI.Selection import ObjectType


doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)

versionNumber = uiapp.Application.VersionNumber
if "2019" in versionNumber or "2020" in versionNumber:
        from Autodesk.Revit.DB import UnitUtils
elif "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
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
               selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilterByIdInclude(ID_WALLS), "Selection Objects")
          except:
               sys.exit()
     elif selobject.Count != 0:
          selection = selobject
     return selection


selobject = get_selection()
volumes = []

def get_host_volume(elem):
        vl = elem.get_Parameter(BuiltInParameter.HOST_VOLUME_COMPUTED).AsDouble()
        if "2019" in versionNumber or "2020" in versionNumber:
                return UnitUtils.ConvertToInternalUnits(vl, DisplayUnitType.DUT_CUBIC_METERS)
        if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber:
                return UnitUtils.ConvertFromInternalUnits(vl, UnitTypeId.CubicMeters)

def get_ifc_volume(el):
        geo = el.get_Geometry(Options())
        vl = 0
        for i in geo:
                if "Solid" in i.ToString():
                        if "2019" in versionNumber or "2020" in versionNumber:
                                vl += UnitUtils.ConvertToInternalUnits(i.Volume, DisplayUnitType.DUT_CUBIC_METERS)
                        if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber:
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