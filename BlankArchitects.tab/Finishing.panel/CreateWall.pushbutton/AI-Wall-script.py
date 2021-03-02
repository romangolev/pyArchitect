# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

#TODO:Create Shared Parameter of there is no such parameter in project
#TODO:RU/EN Autoswitch depending on the Revit version used

__doc__ = 'Создаёт отделку стен для выбранного помещения. /Makes skirting board for selected rooms.'
__author__ = 'Roman Golev'
__title__ = "Отделка\nСтен"

#Load Revit API and system
import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import Room
import Autodesk
clr.AddReference("System.Xml")
import sys

#import revitpythonwrapper by guitalarico 
import rpw
from rpw import doc, uidoc, DB, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)

from collections import namedtuple

#import pyrevit modules
from pyrevit import forms

# Select rooms with rpw ui
selection = ui.Selection()
selected_rooms = [e for e in selection.get_elements(wrapped=False) if isinstance(e, Room)]
if not selected_rooms:
    UI.TaskDialog.Show('MakeWalls', 'You need to select at lest one Room.')
    sys.exit()

#Get wall_types
wall_types = rpw.db.Collector(of_category='OST_Walls', is_type=True).get_elements(wrapped=False)
#Select wall type
wall_type_options = {DB.Element.Name.GetValue(t): t for t in wall_types}
#Select wall types UI
components = [Label('Выберите тип отделки стен:'),
              ComboBox('wl_type', wall_type_options),
              Label('Введите высоту стены:'),
              TextBox('h_offset', wall_custom_height="50.0"),
              CheckBox('checkbox1', 'Брать высоту стены из помещений'),
              Button('Select')]
form = FlexForm('Создать отделку пола',components)
form.show()

#Get the ID of wall type
wall_type = form.values['wl_type']
wall_type_id = wall_type.Id

# Duplicating wall type creating the same layer set with double width
# to deal with the offset API issue
def duplicate_wall_type(type_of_wall):
	wall_type1 = wall_type.Duplicate('temp_wall_type')
	cs1 = wall_type1.GetCompoundStructure()
	layers1 = cs1.GetLayers()
	for layer in layers1:
		cs1.SetLayerWidth(layer.LayerId,2*cs1.GetLayerWidth(layer.LayerId))
	wall_type1.SetCompoundStructure(cs1)
	return wall_type1

#@rpw.db.Transaction.ensure('Make Wall')
def make_wall(new_wall, temp_type):
	wall_curves = new_wall.curve
	level = new_wall.level_id
	if new_wall.room_height > 0:
		wall_height = float(new_wall.room_height)/304.8
	else:
		wall_height = 1500/304.8	
	if new_wall.plug == 1:
		w = Wall.Create(doc, wall_curves, temp_type.Id, level, wall_height, 0.0, False, False)
		w.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
		try:
			db.Element(w).parameters['BA_AI_RoomName'].value = new_wall.room_name
			db.Element(w).parameters['BA_AI_RoomNumber'].value = new_wall.room_number
			db.Element(w).parameters['BA_AI_RoomID'].value = new_wall.room_id
			db.Element(w).parameters['BA_AI_FinishingType'].value = "Wall Finishing"
			db.Element(room).parameters['BA_AI_RoomID'].value = room.Id
		except:
			forms.alert('You need to add shared parameters for BA finishing')
		wallz.append(w)
	else:
		0
	return wallz


NewWall = namedtuple('NewWall', ['wall_type_id', 'wall_type', 'curve', 'level_id', 'room_name', 'room_number','room_id', 'plug', 'room_height', 'bound_walls'])
# plug variable defines if there a need if creating finishing 
# wall or not based on the line's lenght (line lenght filtering)
w = []
new_walls = []
room_boundary_options = DB.SpatialElementBoundaryOptions()
for room in selected_rooms:
	room_level_id = room.Level.Id
	# List of Boundary Segment comes in an array by itself.
	room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
	room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
	room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
	room_id = room.Id
	if form.values['checkbox1']==True:
		room_height = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()*304.8
	else:
		room_height = form.values['h_offset']

	plug = 1
	bound_walls =[]

	# Filtering by hostwall type
	for bound in room_boundary:
		try :
			if doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls":
				if doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
					bound_walls.append(doc.GetElement(bound.ElementId))
					plug = 1
				else:
					plug = 0
			else:
				plug = 0
		except:
			0
		
		line = bound.GetCurve()
		# Filtering small lines less than 10 mm Lenght
		if line.ApproximateLength < 10/304.8:
			plug = 0
		else:
			pass

		#Combining a data package for a new wall
		new_wall = NewWall(wall_type_id=wall_type_id, wall_type=wall_type, curve=line,
						 level_id=room_level_id, room_name=room_name, 
						 room_number=room_number, room_id=room_id, plug=plug,
						 room_height=room_height, bound_walls=bound_walls)
		new_walls.append(new_wall)


#Create wall
wallz = []
with db.Transaction('Create walls'):
	
	# Duplicating wall type
	tmp = duplicate_wall_type(new_wall.wall_type)
	
	# Creating wall
	for new_wall in new_walls:
   		make_wall(new_wall, tmp)
	
	# Changing wall type back
	for n in wallz:
		#changetype(n,new_wall.wall_type)
		n.ChangeTypeId(new_wall.wall_type.Id)
		n.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(3)

	# Deleting temp wall type
	doc.Delete(tmp.Id)
	#Joining finishing walls with it's host objects
	for	wall1 in new_wall.bound_walls:
		for wall2 in wallz:
			try:
				Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc,wall1,wall2)
			except:
				0