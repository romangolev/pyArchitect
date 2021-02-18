# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects
#TODO: Implement the procedure of checking if elements are joined or not before executing command.

__doc__ = """Joins multiple elements / Присоединяет множественные элементы 

First you need to choose the category of elements to join\
(script collects all elements of category). Then you need to choose \
an element or elements to be joined to with the previous selected set of elements by category.
		/
Необходимо выбрать категорию элементов для множественного присоединения, \
затем выбирается элемент или элементы к которым данное присоединение \
необходимо применить. 
"""
__author__ = 'Roman Golev'
__title__ = "Multiple\nJoinByCat"

import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
import sys

#import revitpythonwrapper by guitalarico 
import rpw
from rpw import DB, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)



uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

wall_cat = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_Walls) \
			.WhereElementIsNotElementType() \
			.ToElements() 
floor_cat = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_Floors) \
			.WhereElementIsNotElementType() \
			.ToElements() 		
roof_cat = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_Roofs) \
			.WhereElementIsNotElementType() \
			.ToElements() 		
ceil_cat = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_Ceilings) \
			.WhereElementIsNotElementType() \
			.ToElements() 		
gen_cat = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_GenericModel) \
			.WhereElementIsNotElementType() \
			.ToElements() 	


#db.Collector(of_class)
cats = {"Walls":wall_cat,
	"Floors":floor_cat,
	"Roofs":roof_cat,
	"Ceilings":ceil_cat,
	"Generic Models":gen_cat}
components = [Label('Выберите категорию элементов для присоединения:'),
              ComboBox('categories', cats),
              Button('Select')]
form = FlexForm('Choose element category ',components)
form.show()

if form == False:
    sys.exit()
else:
	selected_cat = form.values['categories']

obj_type = ObjectType.Element
selection = ui.Selection().PickObjects(obj_type,"Choose elements to join")

results = []
with db.Transaction('Multiple join'):
	for A in selected_cat:
		#print(A)
		for B in selection:
			#print(doc.GetElement(B.ElementId))
			try:
				result = Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc,A,doc.GetElement(B.ElementId))
				results.append(result)
			except:
				pass