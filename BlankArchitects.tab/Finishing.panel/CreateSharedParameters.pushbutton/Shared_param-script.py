# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects


__doc__ = """TEST MODE
Добавить общие параметры проекта /
Adds shared parameters used for interior finishing scheduling.
------------------------------------
Инструмент автоматически добавляет
общие параметры проекта,
необходимые для создания отделки."""

__author__ = 'Roman Golev'
__title__ = "Общие\nПараметры"



# Import RevitAPI
import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
import System
clr.AddReference('RevitAPIUI')
from Autodesk.Revit import Creation

import wpf
from System import Windows
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application

import sys
import os.path as op
import os
import rpw
from rpw import  DB, UI, db, ui

import pyrevit
from pyrevit import forms
from pyrevit import UI
from pyrevit import script
from pyrevit.forms import WPFWindow
from collections import namedtuple


#Read shared parameters file
file_location = op.dirname(__file__) + r"\BA_AI.txt"
app.SharedParametersFilename  = file_location
spfile = app.OpenSharedParameterFile()
gr = spfile.Groups


#Categories applied for shared params/ different sets for spicified params
catset1 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Walls),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Floors),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Ceilings),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Roofs)
	]



catset2 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Walls),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Floors),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Ceilings),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Roofs),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Rooms)
	]

cat = catset1



if isinstance(cat, list):
	category = [i for i in cat]
else:
	category= [cat]
#getting list of categories
try:
	categories = [doc.Settings.Categories.get_Item(System.Enum.ToObject(BuiltInCategory, i.Id)) for i in category]
except:
	categories = [i for i in category]
#creating category set
catset = app.Create.NewCategorySet()
[catset.Insert(j) for j in categories]


#NewParam = namedtuple('NewParam'['param_option','catset','parameters','group'])



defp = [g.Definitions for g in gr]
param = [x for l in defp for x in l]
defflatname = [x.Name for x in param]
grpname = [l.OwnerGroup.Name for l in param]

for pp in param:
	print(pp.Name)

"""
for name in grpname:
	if name == "set1":
		print("set1")


	elif name == "set2":
		print("set2")
	else:
		pass
"""

# №96 — PG_TEXT Group
#Parameter groups

f = System.Enum.GetValues(BuiltInParameterGroup)[96]
#set_number = 1

param_option = True



group = f






if isinstance(param, list):
	parameters = [i for i in param]
else:
	parameters = [param]
	
#try:
#	group = [a for a in System.Enum.GetValues(BuiltInParameterGroup) if a == f][0]
#except:
#	group = [a for a in System.Enum.GetValues(BuiltInParameterGroup) if str(a) == f][0]
#i = 0

#def csp()

def create_shared_param(param_option, catset, parameters, group):
	#Determining whether the parameters are type or instance
	if param_option:
		bind = app.Create.NewInstanceBinding(catset)
	else : 
		bind = app.Create.NewTypeBinding(catset)
	#Adding the parameters to the project
	bindmap = doc.ParameterBindings
	for p in parameters:
		print(bind)
		try:
			bindmap.Insert(p, bind, group)
		except:
			print("Fail")
			continue

"""
class MyWindow(WPFWindow):
    def __init__(self,xaml_file_name):
        WPFWindow.__init__(self, xaml_file_name)

    @property
    def checkbox1(self):
		return self.checkbox1_value.IsChecked

    @property
    def checkbox2(self):
		return self.checkbox2_value.IsChecked


    def click(self, sender, args):
		if self.checkbox1 == True:
			with db.Transaction('*BA* Create Shared (Finishing)'):
				create_shared_param()
			forms.alert("checkbox1 is true")
			if self.checkbox2 == True:
				with db.Transaction('*BA* Create Shared (Finishing)'):
					create_shared_param()
					forms.alert("checkbox2 is true")
		elif self.checkbox2 == True:

			forms.alert("checkbox2 is true")	
		else:
			forms.alert("You need to select at least one Parameter group")
		self.Close()
"""

# let's show the window (modal)
#MyWindow('ui.xaml').ShowDialog()
print(param_option, catset, parameters, group)
t = []
with db.Transaction('*BA* Create Shared Params'):
	p=create_shared_param(param_option, catset, parameters, group)
	t.append(p)
	print(t)
