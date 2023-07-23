# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO: Implement the procedure of checking if elements are joined or not before executing command.

__doc__ = """Joins multiple elements / Присоединяет множественные элементы 

First you need to choose the category of elements to join\
(script collects all elements of category). Then you need to choose \
an element or elements to be joined to with the previous selected set of elements by category.
---------------------------------------------------------------------------
Необходимо выбрать категорию элементов для множественного присоединения, \
затем выбирается элемент или элементы к которым данное присоединение \
необходимо применить. 
"""
__author__ = 'Roman Golev'
__title__ = "Batch Join\nBy Category"

import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
import sys
from core.catlistenum import get_catlist
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
transaction = Autodesk.Revit.DB.Transaction(doc)

def main():
	catlist = get_catlist(doc)
	ops = ['Columns', 'Walls', 'Floors', 'Roofs','Structural Columns', 'Structural Foundations', 'Structural Framing']
	choice1 = forms.CommandSwitchWindow.show(ops, message='Select First Category to join')
	try :
		elements1 = catlist[choice1].WhereElementIsNotElementType().ToElements() 
	except:
		sys.exit()
	ops.remove(choice1)
	choice2 = forms.CommandSwitchWindow.show(ops, message='Select Option')
	try :
		elements2 = catlist[choice2].WhereElementIsNotElementType().ToElements() 
	except:
		sys.exit()


	# TODO: Supress "Highlighted elements are joined but do not intersect." warning

	results = []
	transaction.Start('Multiple Join')
	for A in elements1:
		for B in elements2:
			try:
				result = Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc,A,B)
				results.append(result)
			except:
				pass

	transaction.Commit()

if __name__ == '__main__':
    main()