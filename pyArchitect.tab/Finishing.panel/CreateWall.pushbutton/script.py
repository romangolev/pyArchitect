# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import sys
import uuid
import Autodesk
import Autodesk.Revit.DB as DB
from System.Collections.Generic import List
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application
transaction = Autodesk.Revit.DB.Transaction(doc)
transaction_group = Autodesk.Revit.DB.TransactionGroup(doc)

def main():
	# Select rooms 
	selobject = get_selection_basic(uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
	selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
	if not selected_rooms:
		forms.alert('MakeWalls', 'You need to select at lest one Room.')
		sys.exit()

	#Get floor_types
	def collect_walls(doc):
		return DB.FilteredElementCollector(doc) \
				.OfCategory(DB.BuiltInCategory.OST_Walls) \
				.OfClass(DB.WallType) \
				.ToElements()

	wall_types = [i for i in collect_walls(doc) if i.FamilyName != "Curtain Wall"]
	wall_type_options = [i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() for i in wall_types]
	# for i in wall_types:
	# 	wall_type_options.append(i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())


	res = dict(zip(wall_type_options,wall_types))

	switches = ['Inside loops finishing', 'Include Room Separation Lines']
	rops, rswitches = forms.CommandSwitchWindow.show( wall_type_options, 
											message='Select Option',
											switches=switches)

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
		room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
		room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()
		room_id = room.Id
		room_height = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
		level = room_level_id
		if room_height > 0:
			wall_height = float(room_height)
		else:
			wall_height = 1500/304.8	

		w = DB.Wall.Create(doc, line, temp_type.Id, level, wall_height, 0.0, False, False)
		w.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
		global notifications
		try:
			w.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Отделка стен')
		except:
			notifications += 1
		# Here we can add parameter values for wall finishing
		# try:
			# w.get_Parameter().Set()
		# except:
		# 	forms.alert('You need to add shared parameters for finishing')
		return w

	#Create wall
	transaction_group.Start("Make wall finishing")

	transaction.Start('Create Temp Type')
	tmp = duplicate_wall_type(wall_type)
	transaction.Commit()

	transaction.Start('Create Finishing Walls')
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
						#new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
						new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

				elif doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
					doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns" :
					# Filtering small lines less than 10 mm Lenght
					if bound.GetCurve().Length > 10/304.8:
						bound_walls.append(doc.GetElement(bound.ElementId))
						new_wall = make_wall(room, tmp,bound.GetCurve())
						wallzz.append(new_wall)
						wallz.append(new_wall.Id)
						#new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
						new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

				elif rswitches['Include Room Separation Lines'] == True and \
					doc.GetElement(bound.ElementId).Category.Name.ToString() == "<Room Separation>":
					# Filtering small lines less than 10 mm Lenght
					if bound.GetCurve().Length > 10/304.8:
						bound_walls.append(doc.GetElement(bound.ElementId))
						new_wall = make_wall(room, tmp,bound.GetCurve())
						wallzz.append(new_wall)
						wallz.append(new_wall.Id)
						#new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
						new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
				else:
					pass
			except :
				0

		if rswitches['Inside loops finishing'] == True:
			# transaction.Start('Create Finishing Walls for Openings')
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
									#new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
									new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

							elif doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
							doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns":
								# Filtering small lines less than 10 mm Lenght
								if bound.GetCurve().Length > 10/304.8:
									bound_walls.append(doc.GetElement(bound.ElementId))
									new_wall = make_wall(room, tmp,bound.GetCurve())
									wallzz.append(new_wall)
									wallz.append(new_wall.Id)
									#new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
									new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
							else:
								pass
						except :
							pass
					i += 1
			# transaction.Commit()
		elif rswitches['Inside loops finishing'] == False:
			pass
	transaction.Commit()



	#TODO: Supress warning with win32api 
	# https://thebuildingcoder.typepad.com/blog/2018/01/gathering-and-returning-failure-information.html


	res = dict(zip(bound_walls,wallzz))
	transaction.Start('Change Type and Join Walls with hosts')
	col1 = List[DB.ElementId](wallz)
	Autodesk.Revit.DB.Element.ChangeTypeId(doc,col1,wall_type_id)
	transaction.Commit()


	transaction.Start('Join Walls with hosts')
	for i in res:
		try:
			Autodesk.Revit.DB.JoinGeometryUtils.JoinGeometry(doc, i, res[i])
		except:
			pass
	transaction.Commit()



	transaction.Start('Delete Temp Type')
	doc.Delete(tmp.Id)
	transaction.Commit()

	transaction_group.Assimilate()


	if notifications > 0:
		forms.toaster.send_toast('You need to add shared parameters for finishing', \
				title=None, appid=None, icon=None, click=None, actions=None)

if __name__ == '__main__':
    main()