# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


__doc__ = """ Writes down Volume and Mass of all Plates to the Comments parameter
Записывает значение объёма и массы всех пластин в параметр Комментарии
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
    for param in collector:
        param_def = param.GetDefinition()
        if str(param_guid) == str(param.GuidValue):
            return True
        else:
            continue
    return False


categories = doc.Settings.Categories
n = categories.Size

catPlates = categories.get_Item(BuiltInCategory.OST_StructConnectionPlates)

elems = Autodesk.Revit.DB.FilteredElementCollector(doc).\
        OfCategory(BuiltInCategory.OST_StructConnectionPlates).\
        WhereElementIsNotElementType().ToElements()

t.Start("Plates Volume")
for elem in elems:
    params = elem.GetOrderedParameters()
    weight = elem.get_Parameter(Autodesk.Revit.DB.BuiltInParameter.STEEL_ELEM_PLATE_WEIGHT)
    mass = weight.AsValueString()
    volume = elem.get_Parameter(Autodesk.Revit.DB.BuiltInParameter.STEEL_ELEM_PLATE_VOLUME)
    doc.GetElement(elem.Id).get_Parameter(Autodesk.Revit.DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(str(volume.AsValueString())+" "+str(weight.AsValueString()))
t.Commit()
