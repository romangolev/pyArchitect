# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO:RU/EN Autoswitch depending on the Revit version used

__doc__ = """Creates wall finishing for selected rooms / Создаёт отделку стены для выбранного помещения
------------------------------------
Follow the steps / Принцип работы инструмента:
Step 1 / Шаг 1 — Select room(s) / Выделить помещение(я)
Step 2 / Шаг 2 — Select offset option and choose finishing type / Выбрать опцию смещения и тип отделки


"""
__author__ = 'Roman Golev'
__title__ = "Wall\nFinishing"

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
from System import Guid

from collections import namedtuple

#import pyrevit modules
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)
tg = Autodesk.Revit.DB.TransactionGroup(doc)

# Select rooms 
selobject = uidoc.Selection.GetElementIds()
selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
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

switches = ['Inside loops finishing', 'Include Room Separation Lines']
rops, rswitches = forms.CommandSwitchWindow.show(wall_type_options, message='Select Option',switches=switches)

if rops == None:
    sys.exit()

wall_type = res[rops]
wall_type_id = wall_type.Id
notifications = 0

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
	global notifications
	try:
		w.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Отделка стен')
	except:
		notifications += 1
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
			if doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" \
				and doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
				# Filtering small lines less than 10 mm Lenght
				if bound.GetCurve().Length > 10/304.8:
					bound_walls.append(doc.GetElement(bound.ElementId))
					new_wall = make_wall(room, tmp,bound.GetCurve())
					wallzz.append(new_wall)
					wallz.append(new_wall.Id)
					new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)

			elif doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
			     doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns" :
				# Filtering small lines less than 10 mm Lenght
				if bound.GetCurve().Length > 10/304.8:
					bound_walls.append(doc.GetElement(bound.ElementId))
					new_wall = make_wall(room, tmp,bound.GetCurve())
					wallzz.append(new_wall)
					wallz.append(new_wall.Id)
					new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
					
			elif rswitches['Include Room Separation Lines'] == True and \
				doc.GetElement(bound.ElementId).Category.Name.ToString() == "<Room Separation>":
				# Filtering small lines less than 10 mm Lenght
				if bound.GetCurve().Length > 10/304.8:
					bound_walls.append(doc.GetElement(bound.ElementId))
					new_wall = make_wall(room, tmp,bound.GetCurve())
					wallzz.append(new_wall)
					wallz.append(new_wall.Id)
					new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
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
						if doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" \
							and doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
							# Filtering small lines less than 10 mm Lenght
							if bound.GetCurve().Length > 10/304.8:
								bound_walls.append(doc.GetElement(bound.ElementId))
								new_wall = make_wall(room, tmp,bound.GetCurve())
								wallzz.append(new_wall)
								wallz.append(new_wall.Id)
								new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)

						elif doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
						doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns":
							# Filtering small lines less than 10 mm Lenght
							if bound.GetCurve().Length > 10/304.8:
								bound_walls.append(doc.GetElement(bound.ElementId))
								new_wall = make_wall(room, tmp,bound.GetCurve())
								wallzz.append(new_wall)
								wallz.append(new_wall.Id)
								new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
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
	try:
		Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc, i, res[i])
	except:
		pass
t.Commit()



t.Start('Delete Temp Type')
doc.Delete(tmp.Id)
t.Commit()

tg.Assimilate()


if notifications > 0:
    forms.toaster.send_toast('You need to add shared parameters for finishing', \
            title=None, appid=None, icon=None, click=None, actions=None)