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
from core.selectionhelpers import CustomISelectionFilterByIdExclude, CustomISelectionFilterModelCats


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
		id_filter = [-2000270, -2001017, -2008155, -2000095, -2009639, -2005009, -2005111, -2008082, -2009653, -2001042, -2005002, -2000547, -2009642, -2005006, -2008056, -2008080, -2000450, -2000944, -2008194, -2001051, -2008151, -2005028, -2000083, -2008185, -2005015, -2001001, -2000301, -2009056, -2006045, -2008084, -2009057, -2000536, -2006211, -2005008, -2000268, -2008003, -2000987, -2009020, -2000460, -2001007, -2005255, -2006060, -2008204, -2005022, -2006210, -2009641, -2001269, -2005012, -2009657, -2006222, -2000573, -2003410, -2009063, -2009636, -2008115, -2006178, -2000530, -2008131, -2000970, -2000193, -2005014, -2008061, -2005007, -2000538, -2009064, -2001355, -2005001, -2005011, -2008127, -2005204, -2001045, -2008153, -2009055, -2009015, -2000267, -2005210, -2000942, -2005030, -2009656, -2000191, -2000986, -2006276, -2008014, -2006264, -2006090, -2005110, -2000201, -2000400, -2008059, -2008088, -2005026, -2008100, -2006000, -2005251, -2000302, -2009010, -2000941, -2008213, -2009633, -2000223, -2008154, -2008004, -2009655, -2009643, -2009021, -2006176, -2000940, -2008078, -2005252, -2000150, -2005020, -2006209, -2000983, -2000197, -2009651, -2001057, -2006100, -2008129, -2005018, -2006208, -2009649, -2000900, -2006040, -2000200, -2000480, -2005023, -2001061, -2005200, -2006080, -2008017, -2000265, -2005029, -2000485, -2001012, -2006173, -2009025, -2008058, -2000107, -2000220, -2008086, -2005021, -2000537, -2000570, -2005004, -2008076, -2005025, -2001048, -2005254, -2009028, -2006175, -2003405, -2000956, -2006273, -2001267, -2009011, -2000539, -2009005, -2000350, -2006230, -2000710, -2001054, -2005100, -2005032, -2005253, -2009654, -2008048, -2000501, -2000535, -2009652, -2009040, -2009061, -2006266, -2006020, -2001221, -2007004, -2009630, -2006171, -2000834, -2000240, -2006110, -2000133, -2005019, -2008057, -2005016, -2008047, -2009059, -2000955, -2000264, -2000510, -2006170, -2000280, -2009058, -2006226, -2005010, -2006172, -2008060, -2008005, -2000938, -2008209, -2005033, -2006243, -2000266, -2000279, -2008133, -2005250, -2008186, -2009022, -2005027, -2000515, -2005017, -2005130, -2001015, -2009650, -2001016, -2005003, -2005013, -2009640, -2001038, -2000300, -2000263, -2009645, -2005301, -2000550, -2006220, -2000260, -2000278]
		element_filter = CustomISelectionFilterByIdExclude(id_filter)
		
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