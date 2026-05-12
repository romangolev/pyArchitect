# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")
clr.AddReference('System')

from Autodesk.Revit.DB import FilteredElementCollector, ElementId, FamilyInstance, BuiltInCategory
from System.Collections.Generic import List


def main():
    doc = __revit__.ActiveUIDocument.Document
    uidoc = __revit__.ActiveUIDocument

    all_doors = FilteredElementCollector(doc) \
        .WhereElementIsNotElementType() \
        .OfClass(FamilyInstance) \
        .OfCategory(BuiltInCategory.OST_Doors) \
        .ToElements()

    mirrored_doors = [d for d in all_doors if d.Mirrored]

    if mirrored_doors:
        uidoc.Selection.SetElementIds(List[ElementId]([d.Id for d in mirrored_doors]))
        print("Mirrored: {} of {} Doors".format(len(mirrored_doors), len(all_doors)))
    else:
        print("No mirrored doors found.")


if __name__ == '__main__':
    main()