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

    all_windows = FilteredElementCollector(doc) \
        .WhereElementIsNotElementType() \
        .OfClass(FamilyInstance) \
        .OfCategory(BuiltInCategory.OST_Windows) \
        .ToElements()

    mirrored_windows = [w for w in all_windows if w.Mirrored]

    if mirrored_windows:
        uidoc.Selection.SetElementIds(List[ElementId]([w.Id for w in mirrored_windows]))
        print("Mirrored: {} of {} Windows".format(len(mirrored_windows), len(all_windows)))
    else:
        print("No mirrored windows found.")


if __name__ == '__main__':
    main()