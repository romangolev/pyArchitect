# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")

from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInCategory
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document


def main():
    rooms = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType().ToElements()
    print("Total rooms: {}".format(len(rooms)))

    unplaced = []
    for r in rooms:
        if r.Location is None:
            unplaced.append(r)

    print("Unplaced rooms: {}".format(len(unplaced)))

    if not unplaced:
        forms.alert("No unplaced rooms found.", title="Delete Unplaced Rooms")
        return

    print("Showing dialog...")
    result = forms.alert("Delete {} unplaced room(s)?".format(len(unplaced)), yes=True, no=True, title="Delete Unplaced Rooms")
    print("Dialog result: {}".format(result))

    if result:
        print("Starting transaction...")
        t = Transaction(doc, "Delete Unplaced Rooms")
        t.Start()
        for r in unplaced:
            doc.Delete(r.Id)
        t.Commit()
        print("Done. Deleted {} room(s).".format(len(unplaced)))
    else:
        print("Cancelled by user.")


if __name__ == '__main__':
    main()