# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


__doc__ = """Удаляет выбранный общий параметр польностью из проекта / Completely removes shared parameter from project"""
__author__ = 'Roman Golev'
__title__ = "Delete\nShared Parameter"

import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
import sys

clr.AddReference('System')
clr.AddReference('RevitAPIUI')
import pyrevit
from pyrevit import forms
from System.Collections.Generic import List
from System import Guid

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)

dict = {}

def check_param(param_guid):
    spe = FilteredElementCollector(doc).OfClass(SharedParameterElement)
    for s in spe:
        if s.GuidValue.ToString() == param_guid:
            return s
        else:
            pass

collector = FilteredElementCollector(doc).WhereElementIsNotElementType()\
        .OfClass(SharedParameterElement).ToElements()


for param in collector:
    dict[param.Name] = param.GuidValue

choose = forms.CommandSwitchWindow.show(dict.keys(), message='Select Option')

if choose is None:
    sys.exit()
else:
    sParamElement = SharedParameterElement.Lookup(doc, dict[choose])
    t.Start("Delete WBS Parameter")
    doc.Delete(sParamElement.Id)
    t.Commit()