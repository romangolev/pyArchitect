# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import sys
import traceback
import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI.Selection import ObjectType
from core.selectionhelpers import CustomISelectionFilterByIdExclude, ID_MODEL_ELEMENTS
from core.transaction import WrappedTransaction, WrappedTransactionGroup

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
    except:
        sys.exit()

    if selection1.Count == 0 or selection2.Count == 0:
        print("No elements selected in one of the groups")
        print("Both selection groups should contain elements")
        sys.exit()

    with WrappedTransactionGroup(doc, "Join Elements"):
        with WrappedTransaction(doc, "Multiple Join", warning_suppressor=True):
            for A in selection1:
                for B in selection2:
                    try:
                        join = DB.JoinGeometryUtils.JoinGeometry(doc,
                                            doc.GetElement(A.ElementId),
                                            doc.GetElement(B.ElementId))
                    except Exception as error:
                        print(error)
        with WrappedTransaction(doc, "Unjoin", warning_suppressor=True):
            unjoin_notconnected_elements()

def unjoin_notconnected_elements():
    """Disconnect elements that do not intersect"""
    warning1_guid = "1b9dacf3-db22-45d5-b071-42516278ffb1" # 'Highlighted elements are joined but do not intersect.'
    joinedwarning = [w for w in doc.GetWarnings()\
                      if str(w.GetFailureDefinitionId().Guid) == warning1_guid]
    if joinedwarning:
            for i in joinedwarning:
                items = i.GetFailingElements()
                items = [doc.GetElement(i) for i in items]
                if items.Count == 2 :
                    try:
                        DB.JoinGeometryUtils.UnjoinGeometry(doc, items[0], items[1])
                    except:
                        print(traceback.format_exc())

if __name__ == '__main__':
    main()