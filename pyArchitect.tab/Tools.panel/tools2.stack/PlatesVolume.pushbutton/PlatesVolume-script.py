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
from pyrevit import forms
from System.Collections.Generic import List
from core.unitsconverter import convertDoubleToM3
from System.Windows import MessageBox

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
        if str(param_guid) == str(param.GuidValue):
            return True
        else:
            continue
    return False



def main(mode):
    # Get all plates from document
    elems = Autodesk.Revit.DB.FilteredElementCollector(doc).\
            OfCategory(BuiltInCategory.OST_StructConnectionPlates).\
            WhereElementIsNotElementType().ToElements()
    

    t.Start("Plates Volume")

    # Loop elements
    for elem in elems:

        volume = elem.get_Parameter(Autodesk.Revit.DB.BuiltInParameter.STEEL_ELEM_PLATE_VOLUME)
        volume_m3 = convertDoubleToM3(uiapp, volume.AsDouble())
        weight = elem.get_Parameter(Autodesk.Revit.DB.BuiltInParameter.STEEL_ELEM_PLATE_WEIGHT)

        if mode:
            # Calculating volume from parameter value
            volume_str = str(volume.AsValueString())
            # Calculating volume from parameter value (If mass equals zero, calculating manually for steel)
            mass = str(weight.AsValueString())
            if weight.AsDouble() == 0:
                mass = str(round(volume_m3 * 7900, 3)) + " kg"
        else:
            # Calculating volume from double
            volume_str = str(round(volume_m3, 3)) + " m³"
            mass = str(round(volume_m3 * 7900, 3)) + " kg"
        # Write parameter values to comment
        doc.GetElement(elem.Id).\
            get_Parameter(Autodesk.Revit.DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).\
                Set(volume_str + " " + mass)
        
    t.Commit()


if __name__ == '__main__':
    if __shiftclick__:
        mode = True
    else :
        mode = False
    main(mode)
    MessageBox.Show("Values had been written to 'Comments' parameter", 'Completed')