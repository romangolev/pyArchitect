# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys
from pyrevit import forms
from core.catlistenum import collect_category
from core.transaction import WrappedTransaction
from tools.joining import join_intersecting

doc = __revit__.ActiveUIDocument.Document          # type: ignore

def main():
    ops = ['Columns', 'Walls', 'Floors', 'Roofs','Structural Columns', 'Structural Foundations', 'Structural Framing']
    choice1 = forms.CommandSwitchWindow.show(ops, message='Select First Category to join')
    choice2 = forms.CommandSwitchWindow.show(ops, message='Select Second Category to join')
    if choice1 is None or choice2 is None:
        sys.exit()
    elements1 = collect_category(doc, choice1).ToElements()
    elements2 = collect_category(doc, choice2).ToElements()

    with WrappedTransaction(doc, "Join Elements", warning_suppressor=True):
        join_intersecting(doc, elements1, elements2)


if __name__ == '__main__':
    main()
