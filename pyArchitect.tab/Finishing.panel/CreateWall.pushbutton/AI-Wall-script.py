# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO:RU/EN Autoswitch depending on the Revit version used

__doc__ = """Создаёт отделку стен для выбранного помещения. /Makes skirting board for selected rooms.
------------------------------------
Принцип работы инструмента:
Шаг 1 — Выделить в проекте необходимые помещения
Шаг 2 — В сплывающем окне выбрать тип отделки и указать смещение от уровня


При выборе функции "Из помещения" отделка потолка создаётся на основе верхней
высотной отметки помещения. Для корректной работы необходимо настроить 
высоту помещений.

"""
__author__ = 'Roman Golev'
__title__ = "Отделка\nСтен"

#Load Revit API and system
from hashlib import new
import Autodesk
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
import Autodesk
clr.AddReference("System.Xml")
import sys
clr.AddReference("System")
from System.Collections.Generic import List
import uuid

#import revitpythonwrapper by guitalarico 
import rpw
from rpw import ui

from collections import namedtuple

#import pyrevit modules
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)
tg = Autodesk.Revit.DB.TransactionGroup(doc)

# Select rooms with rpw ui
selection = ui.Selection()
selected_rooms = [e for e in selection.get_elements(wrapped=False) if isinstance(e, Room)]
if not selected_rooms:
    forms.alert('MakeWalls', 'You need to select at lest one Room.')
    sys.exit()

#Get floor_types
def collect_walls(doc):
    cl = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_Walls) \
            .OfClass(WallType) \
            .ToElements()
            
    return cl

wall_types = [i for i in collect_walls(doc) if i.FamilyName != "Curtain Wall"]
wall_type_options =[]
for i in wall_types:
	wall_type_options.append(i.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())


res = dict(zip(wall_type_options,wall_types))

switches = ['Inside loops finishing']
rops, rswitches = forms.CommandSwitchWindow.show(wall_type_options, message='Select Option',switches=switches)

if rops == None:
    sys.exit()

wall_type = res[rops]
wall_type_id = wall_type.Id


# Duplicating wall type creating the same layer set with double width
# to deal with the offset API issue
def duplicate_wall_type(type_of_wall):
	wall_type1 = type_of_wall.Duplicate(str(uuid.uuid4()))
	cs1 = wall_type1.GetCompoundStructure()
	layers1 = cs1.GetLayers()
	for layer in layers1:
		cs1.SetLayerWidth(layer.LayerId,2*cs1.GetLayerWidth(layer.LayerId))
	wall_type1.SetCompoundStructure(cs1)
	return wall_type1
 
room_boundary_options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()
w = []

def make_wall(room, temp_type, line):
	room_level_id = room.Level.Id
	# List of Boundary Segment comes in an array by itself.
	room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
	room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
	room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
	room_id = room.Id
	room_height = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()
	level = room_level_id
	if room_height > 0:
		wall_height = float(room_height)
	else:
		wall_height = 1500/304.8	

	w = Wall.Create(doc, line, temp_type.Id, level, wall_height, 0.0, False, False)
	w.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
	# Here we can add parameter values for wall finishing
	# try:
		# w.get_Parameter().Set()
	# except:
	# 	forms.alert('You need to add shared parameters for finishing')
	return w

#Create wall
tg.Start("Make wall finishing")

t.Start('Create Temp Type')
tmp = duplicate_wall_type(wall_type)
t.Commit()

t.Start('Create Finishing Walls')
wallz = []
bound_walls =[]
wallzz = []
for room in selected_rooms:
	room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
	plug = 1
	# Filtering by hostwall type

	for bound in room_boundary:
		try :
			if doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" or \
			   doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
			   doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns":
				if doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
					# Filtering small lines less than 10 mm Lenght
					if bound.GetCurve().Length > 10/304.8:
						bound_walls.append(doc.GetElement(bound.ElementId))
						new_wall = make_wall(room, tmp,bound.GetCurve())
						wallzz.append(new_wall)
						wallz.append(new_wall.Id)
						new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
				else:
					pass
			else:
				pass
		except :
			0

	if rswitches['Inside loops finishing'] == True:
		# t.Start('Create Finishing Walls for Openings')
		for room in selected_rooms:
			room_boundary2 = room.GetBoundarySegments(room_boundary_options)
			i = 1
			while i < len(room_boundary2):
				for bound in room_boundary2[i]:
					try :
						if doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" or \
						   doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
						   doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns" :
							# if doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
								# Filtering small lines less than 10 mm Lenght
							if bound.GetCurve().Length > 10/304.8:
								bound_walls.append(doc.GetElement(bound.ElementId))
								new_wall = make_wall(room, tmp,bound.GetCurve())
								wallzz.append(new_wall)
								wallz.append(new_wall.Id)
								new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
							# else:
							# 	pass
						else:
							pass
					except :
						pass
				i += 1
		# t.Commit()
	elif rswitches['Inside loops finishing'] == False:
		pass
t.Commit()
#TODO: Supress warning with win32api 
# https://thebuildingcoder.typepad.com/blog/2018/01/gathering-and-returning-failure-information.html


res = dict(zip(bound_walls,wallzz))
t.Start('Change Type and Join Walls with hosts')
col1 = List[ElementId](wallz)
Autodesk.Revit.DB.Element.ChangeTypeId(doc,col1,wall_type_id)
t.Commit()


t.Start('Join Walls with hosts')
for i in res:
	Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc, i, res[i])
t.Commit()



t.Start('Delete Temp Type')
doc.Delete(tmp.Id)
t.Commit()

tg.Assimilate()