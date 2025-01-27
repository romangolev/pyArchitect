# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO: Implement the procedure of checking if elements are joined or not before executing command.

import sys
import Autodesk.Revit.DB as DB
from pyrevit import forms
from core.catlistenum import get_catlist
from core.transaction import WrappedTransaction

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
    with WrappedTransaction(doc, "Multiple Join", warning_suppressor=True):
        for A in elements1:
            for B in elements2:
                try:
                    result = DB.JoinGeometryUtils.JoinGeometry(doc, A, B)
                    results.append(result)
                except:
                    pass

if __name__ == '__main__':
    main()