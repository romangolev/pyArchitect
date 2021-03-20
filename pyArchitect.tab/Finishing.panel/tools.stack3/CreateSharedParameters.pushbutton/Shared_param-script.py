# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects


__doc__ = """
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

import os.path as op
from rpw import  DB, UI, db, ui
from pyrevit import forms
from pyrevit import UI
from pyrevit.forms import WPFWindow
from collections import namedtuple
from collections import namedtuple

runtype = []

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
			runtype.append(1)
			self.Close()
			if self.checkbox2 == True:
				runtype.append(2)
				self.Close()
		elif self.checkbox2 == True:
			runtype.append(2)	
		else:
			forms.alert("You need to select at least one Parameter group")
		self.Close()

def create_shared_param(m_param_option, m_catset, m_parameters, m_group):
	#Determining whether the parameters are type or instance
	if m_param_option:
		bind = app.Create.NewInstanceBinding(m_catset)
	else : 
		bind = app.Create.NewTypeBinding(m_catset)
	#Adding the parameters to the project
	bindmap = doc.ParameterBindings
	for p in m_parameters:
		try:
			bindmap.Insert(p, bind, m_group)
		except:
			#print("Fail")
			continue

def run(m_set):
	with db.Transaction('*BA* Create Shared Params'):
		create_shared_param(m_set.t_param_option, m_set.t_catset, m_set.t_parameters, m_set.t_group)


# let's show the window (modal)
MyWindow('ui.xaml').ShowDialog()

#Read shared parameters file
file_location = op.dirname(__file__) + r"\BA_AI.txt"
app.SharedParametersFilename  = file_location
spfile = app.OpenSharedParameterFile()
gr = spfile.Groups

#Categories applied for shared params/ different sets for spicified params
cats1 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Walls),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Floors),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Ceilings),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Roofs)]
catset1 = app.Create.NewCategorySet()
[catset1.Insert(j) for j in cats1]

cats2 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Walls),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Floors),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Ceilings),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Roofs),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Rooms)]
catset2 = app.Create.NewCategorySet()
[catset2.Insert(i) for i in cats2]

cats3 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Rooms)]
catset3 = app.Create.NewCategorySet()
[catset3.Insert(i) for i in cats3]

cats4 = [Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Walls),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Floors),
	Autodesk.Revit.DB.Category.GetCategory(doc,Autodesk.Revit.DB.BuiltInCategory.OST_Roofs)]
catset4 = app.Create.NewCategorySet()
[catset4.Insert(i) for i in cats4]



defp = [g.Definitions for g in gr]
param = [x for l in defp for x in l]
defflatname = [x.Name for x in param]
grpname = [l.OwnerGroup.Name for l in param]
param_name = [pp.Name for pp in param]

param1 = [param[param_name.index('BA_AI_RoomName')], \
          param[param_name.index('BA_AI_FinishingType')], \
		  param[param_name.index('BA_AI_RoomNumber')]]
param2 = [param[param_name.index('BA_AI_RoomID')]]
param3 = [param[param_name.index('BA_AI_RoomFinishingArea-Floor')], \
		  param[param_name.index('BA_AI_RoomFinishingDescription-Ceiling')], \
		  param[param_name.index('BA_AI_RoomFinishingArea-Ceiling')], \
		  param[param_name.index('BA_AI_RoomFinishingDescription-Wall')], \
		  param[param_name.index('BA_AI_RoomFinishingArea-Wall')], \
		  param[param_name.index('BA_AI_RoomFinishingDescription-Floor')]]
param4 = [param[param_name.index('BA_AI_Structure')]]



# №96 — PG_TEXT Group
#Parameter groups
f = System.Enum.GetValues(BuiltInParameterGroup)[96]
try:
	group = [a for a in System.Enum.GetValues(BuiltInParameterGroup) if a == f][0]
except:
	group = [a for a in System.Enum.GetValues(BuiltInParameterGroup) if str(a) == f][0]

param_option = True


#print(param_option, catset, parameters, group)
Set = namedtuple('Param_settings', ['t_param_option','t_catset','t_parameters','t_group'])
param_set1 = Set(t_param_option = param_option, t_catset = catset1, t_parameters = param1, t_group = group)
param_set2 = Set(t_param_option = param_option, t_catset = catset2, t_parameters = param2, t_group = group)
param_set3 = Set(t_param_option = param_option, t_catset = catset3, t_parameters = param3, t_group = group)
param_set4 = Set(t_param_option = False, t_catset = catset4, t_parameters = param4, t_group = group)

if 1 and 2 in runtype:
	run(param_set1)
	run(param_set2)
	run(param_set3)
	run(param_set4)
elif 1 in runtype:
	run(param_set1)
	run(param_set2)
elif 2 in runtype:
	run(param_set3)
	run(param_set4)
else:
	pass