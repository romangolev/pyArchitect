# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys
from Autodesk.Revit.UI.Selection import ObjectType
from core.selectionhelpers import CustomISelectionFilterByIdExclude, ID_MODEL_ELEMENTS
from core.transaction import WrappedTransaction
from tools.joining import join_intersecting

uidoc = __revit__.ActiveUIDocument                       # type: ignore
doc = __revit__.ActiveUIDocument.Document                # type: ignore

def main():
    # Non-Model Categories to hide
    element_filter = CustomISelectionFilterByIdExclude(ID_MODEL_ELEMENTS)
    try:
        selection1 = uidoc.Selection.PickObjects(ObjectType.Element,
                                                  element_filter,
                                                    "Selection Group 1")
        selecetion1_elements_ids = [i.ElementId.ToString() for i in selection1]

        element_filter2 = CustomISelectionFilterByIdExclude(category_ids=ID_MODEL_ELEMENTS, element_ids=selecetion1_elements_ids)
        selection2 = uidoc.Selection.PickObjects(ObjectType.Element,
                                                  element_filter2,
                                                    "Selection Group 2")
    except Exception:
        sys.exit()

    if selection1.Count == 0 or selection2.Count == 0:
        print("No elements selected in one of the groups")
        print("Both selection groups should contain elements")
        sys.exit()

    elements1 = [doc.GetElement(ref.ElementId) for ref in selection1]
    elements2 = [doc.GetElement(ref.ElementId) for ref in selection2]
    with WrappedTransaction(doc, "Join Elements", warning_suppressor=True):
        join_intersecting(doc, elements1, elements2)

if __name__ == '__main__':
    main()
