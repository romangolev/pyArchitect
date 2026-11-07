# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys
import clr
clr.AddReference("System")
from Autodesk.Revit.DB import ElementId
from System.Collections.Generic import List
from pyrevit import forms
from core.catlistenum import category_names, collect_category

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

choose = forms.CommandSwitchWindow.show(
	category_names(),
	message='Select Option',
	title='Select Category'
)
if choose is None:
	sys.exit()

elid = [el.Id for el in collect_category(doc, choose).ToElements()]
uidoc.Selection.SetElementIds(List[ElementId](elid))
