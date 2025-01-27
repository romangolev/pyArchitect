# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import sys
import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from core.selectionhelpers import CustomISelectionFilterByIdExclude, CustomISelectionFilterModelCats, ID_MODEL_ELEMENTS
from core.transaction import WrappedTransaction

uidoc = __revit__.ActiveUIDocument                      # type: ignore
doc = __revit__.ActiveUIDocument.Document                # type: ignore

    #TODO: Exclude from second selection elements that are in first selection

def main():
    obj_type = ObjectType.Element

    if __shiftclick__:                                     # type: ignore
        # Procedural filter for model elements
        element_filter = CustomISelectionFilterModelCats(doc)
    else:
        # Non-Model Categories to hide
        element_filter = CustomISelectionFilterByIdExclude(ID_MODEL_ELEMENTS)
        
    try:
        selection1 = uidoc.Selection.PickObjects(obj_type, element_filter, "Selection Group 1")
        selection2 = uidoc.Selection.PickObjects(obj_type, "Selection Group 2")
    except:
        sys.exit()

    elementA = selection1
    elementB = selection2
    with WrappedTransaction(doc, "Multiple Join", warning_suppressor=True):
        for A in elementA:
            for B in elementB:
                try:
                    join = DB.JoinGeometryUtils.JoinGeometry(doc,
                                        doc.GetElement(A.ElementId),
                                        doc.GetElement(B.ElementId))
                except Exception as error:
                    print(error)

if __name__ == '__main__':
    main()