# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO: Implement the procedure of checking if elements are joined or not before executing command.

import sys
import traceback
import Autodesk.Revit.DB as DB
from pyrevit import forms
from core.catlistenum import get_catlist
from core.transaction import WrappedTransaction, WrappedTransactionGroup

uidoc = __revit__.ActiveUIDocument                 # type: ignore
doc = __revit__.ActiveUIDocument.Document          # type: ignore

def main():
    catlist = get_catlist(doc)
    ops = ['Columns', 'Walls', 'Floors', 'Roofs','Structural Columns', 'Structural Foundations', 'Structural Framing']
    choice1 = forms.CommandSwitchWindow.show(ops, message='Select First Category to join')
    choice2 = forms.CommandSwitchWindow.show(ops, message='Select Second Category to join')
    try :
        elements1 = catlist[choice1].WhereElementIsNotElementType().ToElements()
        elements2 = catlist[choice2].WhereElementIsNotElementType().ToElements() 
    except:
        sys.exit()

    results = []
    with WrappedTransactionGroup(doc, "Join Elements"):
        with WrappedTransaction(doc, "Multiple Join", warning_suppressor=True):
            for A in elements1:
                for B in elements2:
                    try:
                        result = DB.JoinGeometryUtils.JoinGeometry(doc, A, B)
                        results.append(result)
                    except:
                        pass
        with WrappedTransaction(doc, "Unjoin", warning_suppressor=True):
            unjoin_notconnected_elements()
    # print( len(results), "elements joined")


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
                        pass
                        # print(traceback.format_exc())

if __name__ == '__main__':
    main()