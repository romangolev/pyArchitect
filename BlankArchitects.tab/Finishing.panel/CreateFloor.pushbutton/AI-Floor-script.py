# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

#TODO:Create Shared Parameter if there is no such parameter in project

__doc__ = """Создание отделки пола для выбранных помещений иструментом Перекрытие
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
from collections import namedtuple
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Document

import rpw
from rpw import doc, uidoc, DB, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)
from pyrevit import forms 

#Select Rooms
selection = ui.Selection()
selected_rooms = [e for e in selection.get_elements(wrapped=False) if isinstance(e, Room)]
if not selected_rooms:
    UI.TaskDialog.Show('Создать отделку потолка', 'Необходимо выбрать помещение.')
    sys.exit()


#Get floor_types
floor_types = rpw.db.Collector(of_category='OST_Floors', is_type=True).get_elements(wrapped=False)
#Select floor type
floor_type_options = {DB.Element.Name.GetValue(t): t for t in floor_types}
#Select floor types UI

floor_type_id = ""

components = [Label('Выберите тип отделки:'),
              ComboBox('fl_type', floor_type_options),
              Label('Введите привязку пола к уровню :'),
              TextBox('h_offset', base_offset="50.0"),
              CheckBox('checkbox1', 'Брать смещение пола из свойств помещения'),
              CheckBox('checkbox2', 'Вырезать отверстия'),
              Label('Вырезание отверстий работает корректно'),
              Label('при выборе только одного помещения'),
              Button('Select')]
form = FlexForm('Создать отделку пола', components)
win = form.show()

if win == False:
    sys.exit()

#Get the ID of floor type
floor_type_id = form.values['fl_type'].Id
if form.values['h_offset'] != "":
    offset3 = float(form.values['h_offset'])
else:
    offset3 = 0

f ,fls = [], []
co = []

#@rpw.db.Transaction.ensure('Создание отделки пола')
def make_floor(new_floor):
    floor_curves = DB.CurveArray()
    for boundary_segment in new_floor.boundary:
        floor_curves.Append((boundary_segment).GetCurve())
    floorType = doc.GetElement(new_floor.floor_type_id)
    level = doc.GetElement(new_floor.level_id)
    normal_plane = DB.XYZ.BasisZ
    f = doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
    fls.append(f)

    # Input parameter values from rooms
    if form.values['checkbox1'] == True :
        db.Element(f).parameters.builtins['FLOOR_HEIGHTABOVELEVEL_PARAM'].value = float(new_floor.room_offset1)
    else:
        db.Element(f).parameters.builtins['FLOOR_HEIGHTABOVELEVEL_PARAM'].value = float(offset3/304.8)
    try:
        db.Element(f).parameters['BA_AI_RoomName'].value = new_floor.room_name
        db.Element(f).parameters['BA_AI_RoomNumber'].value = new_floor.room_number
        db.Element(f).parameters['BA_AI_RoomID'].value = new_floor.room_id
        db.Element(f).parameters['BA_AI_FinishingType'].value = "Floor Finishing"
        db.Element(room).parameters['BA_AI_RoomID'].value = room.Id
    except:
        forms.alert('You need to add shared parameters for BA finishing')
        pass


def make_opening(new_floor):
    co_curves = DB.CurveArray()
    for bounds in i:
        co_curves.Append(bounds.GetCurve())
    co = doc.Create.NewOpening(fls[new_floor.count-1], co_curves, False)



NewFloor = namedtuple('NewFloor', ['floor_type_id', 'boundary', 'level_id', 'count', 'opening_boundary', 'openings',
                                    'room_offset1','room_offset2', 'room_name', 'room_number', 'room_id'])


new_floors = []
room_boundary_options = DB.SpatialElementBoundaryOptions()
opening_boundary = []
all_boundaries = []
all_boundaries1 = []
r = 0

for room in selected_rooms:
    room_level_id = room.Level.Id
    room_offset1 = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
    room_offset2 = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
    room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
    room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
    room_id = room.Id
    # List of Boundary Segment comes in an array by itself.
    r += 1
    #opening_boundary = room.GetBoundarySegments(room_boundary_options)[1]
    room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
    all_boundaries = room.GetBoundarySegments(room_boundary_options)
    n = 0
    for bound_set in all_boundaries:
        all_boundaries1.append(room.GetBoundarySegments(room_boundary_options)[n])
        n += 1
    all_boundaries1.pop(0)
    new_floor = NewFloor(floor_type_id = floor_type_id, boundary = room_boundary,
                         level_id = room_level_id, count = r, opening_boundary = all_boundaries1,
                         openings = n-1, room_offset1 = room_offset1, room_offset2 = room_offset2, room_name = room_name,
                         room_number = room_number, room_id = room_id)
    new_floors.append(new_floor)



c = 0
#Create floor
for new_floor in new_floors:
    with db.Transaction('Create Floor'):
        make_floor(new_floor)
        c += 1
    if form.values['checkbox2'] and new_floor.openings != 0 :
        for i in new_floor.opening_boundary:
            with db.Transaction('Create Openeing'):
                make_opening(new_floor)