# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

#TODO:Create Shared Parameter if there is no such parameter in project

__doc__ = """Создание отделки пола для выбранных помещений иструментом "Перекрытие"
------------------------------------
Принцип работы инструмента:
Шаг 1 — Выделить в проекте необходимые помещения
Шаг 2 — В сплывающем окне выбрать тип отделки и указать смещение от уровня

При создании пола, в новый пол записываются параметры номера, названия и ID помещения.
Функция "Вырезание отверстий" работает корректно только при выборе одного
помещения. Выбор множественных помещений может привести к ошибке.

"""
__author__ = 'Roman Golev'
__title__ = "Отделка\nПола"

import sys
import os
import Autodesk
from collections import namedtuple
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Document
from pyrevit import forms 

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)
tg = Autodesk.Revit.DB.TransactionGroup(doc)


from rpw import ui, DB

#Select Rooms
selection = ui.Selection()
selected_rooms = [e for e in selection.get_elements(wrapped=False) if isinstance(e, Room)]
if not selected_rooms:
    forms.alert('Создать отделку потолка', 'Необходимо выбрать помещение.')
    sys.exit()

def make_opening(nf,boundary):
    co_curves = DB.CurveArray()
    for bounds in boundary:
        co_curves.Append(bounds.GetCurve())
    co = doc.Create.NewOpening(nf, co_curves, False)

#Get floor_types
def collect_floors(doc):
    cl = FilteredElementCollector(doc) \
            .OfCategory(BuiltInCategory.OST_Floors) \
            .OfClass(FloorType) \
            .ToElements()
            
    return cl


floor_types = collect_floors(doc)
floor_type_options = []
for i in floor_types:
    floor_type_options.append(i.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())

res = dict(zip(floor_type_options,floor_types))
for key in floor_types:
    res[key] = key.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)

switches = ['Смещение из помещения', 'Floor or Ceiling']
cfgs = {'option1': { 'background': '0xFF55FF'}}
rops, rswitches = forms.CommandSwitchWindow.show(floor_type_options, message='Select Option',switches=switches,config=cfgs,)

if rops == None:
    sys.exit()

floor_type_id = res[rops].Id
room_boundary_options = DB.SpatialElementBoundaryOptions()

def make_floor(room):
    room_level_id = room.Level.Id
    room_offset1 = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
    room_offset2 = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
    room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
    room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
    room_id = room.Id
    room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
    floor_curves = DB.CurveArray()
    for boundary_segment in room_boundary:
        floor_curves.Append((boundary_segment).GetCurve())
    floorType = doc.GetElement(floor_type_id)
    level = doc.GetElement(room_level_id)
    normal_plane = DB.XYZ.BasisZ
    f = doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
    offset2 = doc.GetElement(floor_type_id).get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
    # Input parameter values from rooms
    if rswitches['Floor or Ceiling'] == False:
        if rswitches['Смещение из помещения'] == False:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1 + offset2)
        if rswitches['Смещение из помещения'] == True:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1)

    if  rswitches['Floor or Ceiling'] == True:
        if rswitches['Смещение из помещения'] == True:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)
        if rswitches['Смещение из помещения'] == False:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2 + offset2)
    # Here we can add parameters for floors and ceilings
    # try:
		# w.get_Parameter().Set()
	# except:
	# 	forms.alert('You need to add shared parameters for finishing')
    return f


tg.Start("Make Floor/Ceiling finishing")
for room in selected_rooms:
    # Create floor
    t.Start('Create Floor/Ceiling')
    new_floor = make_floor(room)
    all_boundaries = room.GetBoundarySegments(room_boundary_options)
    t.Commit()

    #Create floor opening if needed
    if len(all_boundaries) >1:
        t.Start('Create Opening(s)')
        i = 1
        while i < len(all_boundaries):
            make_opening(new_floor, all_boundaries[i])
            i += 1
        t.Commit()
    else:
        pass
tg.Assimilate()