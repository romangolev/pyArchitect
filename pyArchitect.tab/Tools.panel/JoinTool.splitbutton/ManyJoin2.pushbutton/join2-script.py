# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

__doc__ = """Joins multiple elements / Присоединяет множественные элементы 

First you need to choose host element or elements to be joined to.\
Then you need to choose a second group or element that should be connected to host.
		/
Необходимо выбрать первую группу элементов для множественного присоединения, \
затем выбирается вторая группа элементов, к которым данное присоединение \
необходимо применить. 
"""
__author__ = 'Roman Golev'
__title__ = "Multiple\nJoinSelect"

import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
import sys

#import revitpythonwrapper by guitalarico 
import rpw
from rpw import DB, UI, db, ui

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

obj_type = ObjectType.Element
selection1 = ui.Selection().PickObjects(obj_type,"Choose elements to join")
selection2 = ui.Selection().PickObjects(obj_type,"Choose elements to join")

elementA = selection1
elementB = selection2

results = []
with db.Transaction('Multiple join'):
	for A in elementA:
		for B in elementB:
			try:
				Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc,doc.GetElement(A.ElementId),doc.GetElement(B.ElementId))
			except:
				pass
