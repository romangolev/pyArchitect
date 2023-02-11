# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


__doc__ = """ Plates Volume

"""
__author__ = 'Roman Golev'
__title__ = "Plates\nVolume"


import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

clr.AddReference('System')
clr.AddReference('RevitAPIUI')
import pyrevit
from pyrevit import forms
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)

def check_param(param_guid):
    spe = FilteredElementCollector(doc).OfClass(SharedParameterElement)
    for s in spe:
        if s.GuidValue.ToString() == param_guid:
            return s
        else:
            pass

def checkparamexist(param_guid):
    collector = FilteredElementCollector(doc).WhereElementIsNotElementType()\
        .OfClass(SharedParameterElement).ToElements()
    # print(collector)
    for param in collector:
        param_def = param.GetDefinition()
        # print(param_def.Name)
        # print(param.GuidValue)
        # print(param_guid)
        if str(param_guid) == str(param.GuidValue):
            # print("True")
            return True
        else:
            # print("Continue")
            continue
    return False


categories = doc.Settings.Categories
n = categories.Size
#print(n)

catPlates = categories.get_Item(BuiltInCategory.OST_StructConnectionPlates)

catStairs = categories.get_Item(BuiltInCategory.OST_Stairs)
catStairsSupports = categories.get_Item(BuiltInCategory.OST_StairsSupports)
catStairsRuns = categories.get_Item(BuiltInCategory.OST_StairsRuns)

#print(catSpeEquip,catSpeEquip.Name)

elems = Autodesk.Revit.DB.FilteredElementCollector(doc).\
        OfCategory(BuiltInCategory.OST_StructConnectionPlates).\
        WhereElementIsNotElementType().ToElements()

mass1_param_guid = "1a308e03-19a4-48cd-8b1b-2331db202134"
mass1_param = check_param(mass1_param_guid)

mass2_param_guid = "613f3f12-a626-41dc-9968-31392996ced1"
mass2_param = check_param(mass2_param_guid)


t.Start("Plates Volume")
for elem in elems:
     params = elem.GetOrderedParameters()
     weight = elem.get_Parameter(Autodesk.Revit.DB.BuiltInParameter.STEEL_ELEM_PLATE_WEIGHT)
     mass = weight.AsValueString()
     doc.GetElement(elem.Id).get_Parameter(mass1_param.GuidValue).Set(str(weight.AsValueString()))
     doc.GetElement(elem.Id).get_Parameter(mass2_param.GuidValue).Set(weight.AsDouble())
t.Commit()
