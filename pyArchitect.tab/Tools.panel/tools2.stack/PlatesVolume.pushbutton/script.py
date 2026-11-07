# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev


import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *

clr.AddReference('System')
from core.transaction import WrappedTransaction
from core.unitsconverter import UnitConverter
from System.Windows import MessageBox

doc = __revit__.ActiveUIDocument.Document
uiapp = __revit__


def main(mode):
    # Get all plates from document
    elems = FilteredElementCollector(doc) \
        .OfCategory(BuiltInCategory.OST_StructConnectionPlates) \
        .WhereElementIsNotElementType().ToElements()
    

    with WrappedTransaction(doc, "Plates Volume"):
        for elem in elems:
            write_volume_and_mass(elem, mode)


def write_volume_and_mass(elem, mode):
    volume = elem.get_Parameter(BuiltInParameter.STEEL_ELEM_PLATE_VOLUME)
    volume_m3 = UnitConverter.convertDoubleToM3(uiapp, volume.AsDouble())
    weight = elem.get_Parameter(BuiltInParameter.STEEL_ELEM_PLATE_WEIGHT)

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
    elem.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) \
        .Set(volume_str + " " + mass)


if __name__ == '__main__':
    main(__shiftclick__)
    MessageBox.Show("Values had been written to 'Comments' parameter", 'Completed')