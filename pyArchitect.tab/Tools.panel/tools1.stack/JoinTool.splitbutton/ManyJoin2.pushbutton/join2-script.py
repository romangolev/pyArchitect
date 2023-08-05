# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

__doc__ = """Joins multiple elements / Присоединяет множественные элементы 

First you need to choose host element or elements to be joined to.\
Then you need to choose a second group or element that should be connected to host.
--------------------------------------------------------------------------
Необходимо выбрать первую группу элементов для множественного присоединения, \
затем выбирается вторая группа элементов, к которым данное присоединение \
необходимо применить. 
"""
__author__ = 'Roman Golev'
__title__ = "Batch Join\nBy Selection"

import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import JoinGeometryUtils
from Autodesk.Revit.UI.Selection import ObjectType, ISelectionFilter
from Autodesk.Revit.Exceptions import OperationCanceledException
import sys
from core.selectionhelpers import CustomISelectionFilterByIdExclude, CustomISelectionFilterModelCats, ID_MODEL_ELEMENTS


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document
transaction = Autodesk.Revit.DB.Transaction(doc)

def main():
	obj_type = ObjectType.Element

	if __shiftclick__:
		# Procedural filter for model elements
		element_filter = CustomISelectionFilterModelCats(doc)
	else:
		# Non-Model Categories to hide
		element_filter = CustomISelectionFilterByIdExclude(ID_MODEL_ELEMENTS)
		
	try:
		selection1 = uidoc.Selection.PickObjects(obj_type, element_filter, "Selection Group 1")
	except:
		sys.exit()
	try:
		selection2 = uidoc.Selection.PickObjects(obj_type, "Selection Group 2")
	except:
		sys.exit()

	elementA = selection1
	elementB = selection2

	# TODO: Supress "Highlighted elements are joined but do not intersect." warning

	results = []
	transaction.Start('Multiple Join')
	for A in elementA:
		for B in elementB:
			try:
				join = JoinGeometryUtils.JoinGeometry(doc,doc.GetElement(A.ElementId),doc.GetElement(B.ElementId))
			except Exception as error:
				print(error)

	transaction.Commit()

if __name__ == '__main__':
    main()