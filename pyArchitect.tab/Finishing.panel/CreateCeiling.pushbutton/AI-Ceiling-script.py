# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Создание отделки потолка для выбранных помещений иструментом Крыша
------------------------------------    
Принцип работы инструмента:
Шаг 1 — Выделить в проекте необходимые помещения
Шаг 2 — В сплывающем окне выбрать тип отделки и указать смещение от уровня


При выборе функции "Из помещения" отделка потолка создаётся на основе верхней
высотной отметки помещения. Для корректной работы необходимо настроить 
высоту помещений.

Используются параметры / Shared parameters used:
BA_AI_RoomName
BA_AI_RoomNumber
BA_AI_RoomID
BA_AI_FinishingType
"""
"""
При создании потолка, в новый элемент записываются параметры номера, названия и ID помещения.
Функция "Вырезание отверстий" работает корректно только при выборе одного
помещения. Выбор множественных помещений может привести к ошибке.
"""

__author__ = 'Roman Golev'
__title__ = "Отделка\nПотолка"

import sys
import os
from collections import namedtuple
import clr
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Document
import rpw
from rpw import doc, uidoc, DB, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)
from pyrevit import forms 

selection = ui.Selection()
selected_rooms = [e for e in selection.get_elements(wrapped=False) if isinstance(e, Room)]
if not selected_rooms:
    UI.TaskDialog.Show('Создать отделку потолка', 'Необходимо выбрать помещение.')
    sys.exit()



#Get ceiling_types
ceiling_types = rpw.db.Collector(of_category='OST_Roofs', is_type=True).get_elements(wrapped=False)
#Select ceiling type
ceiling_type_options = {DB.Element.Name.GetValue(t): t for t in ceiling_types}
#Select ceiling types UI

components = [Label('Выберите тип потолка:'),
              ComboBox('cl_type', ceiling_type_options),
              Label('Введите привязку потолка к уровню :'),
              TextBox('h_offset', ceiling_offset="50.0"),
              CheckBox('checkbox1', 'Из помещения'),
              Button('Select')]
form = FlexForm('Создать отделку потолка',components)
win = form.show()

if win == False:
    sys.exit()

#Get the ID of ceiling ( NewFootPrintRoof )
ceiling_type_id = form.values['cl_type'].Id
if form.values['h_offset'] != "":
    offset3 = float(form.values['h_offset'])
else:
    offset3 = 2000

f = []

@rpw.db.Transaction.ensure('Создать отделку потолка')
def make_ceiling(new_ceiling):
    ceiling_curves = DB.CurveArray()
    for boundary_segment in new_ceiling.boundary:
        try:
            ceiling_curves.Append(boundary_segment.Curve)       # 2015, dep 2016
        except AttributeError:
            ceiling_curves.Append(boundary_segment.GetCurve())  # 2017
    ceilingType = doc.GetElement(new_ceiling.ceiling_type_id)
    ceil_thick = ceilingType.get_Parameter(BuiltInParameter.ROOF_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
    level = doc.GetElement(new_ceiling.level_id)
    f = doc.Create.NewFootPrintRoof(ceiling_curves, level, ceilingType, clr.StrongBox[ModelCurveArray](ModelCurveArray()))
    if form.values['checkbox1'] == True :
        db.Element(f).parameters.builtins['ROOF_LEVEL_OFFSET_PARAM'].value = float(new_ceiling.room_offset - ceil_thick)
    else:
        db.Element(f).parameters.builtins['ROOF_LEVEL_OFFSET_PARAM'].value = float(offset3/304.8)
    try:
        db.Element(f).parameters['BA_AI_RoomName'].value = new_ceiling.room_name
        db.Element(f).parameters['BA_AI_RoomNumber'].value = new_ceiling.room_number
        db.Element(f).parameters['BA_AI_RoomID'].value = new_ceiling.room_id
        db.Element(f).parameters['BA_AI_FinishingType'].value = "Ceiling Finishing"
        db.Element(room).parameters['BA_AI_RoomID'].value = room.Id
    except:
        forms.toaster.send_toast('You need to add shared parameters for BA finishing')
        #forms.alert('You need to add shared parameters for BA finishing')
        pass


def make_opening(new_floor):
    co_curves = DB.CurveArray()
    for bounds in i:
        co_curves.Append(bounds.GetCurve())
    co = doc.Create.NewOpening(fls[new_floor.count-1], co_curves, False)

NewCeiling = namedtuple('NewCeiling', ['ceiling_type_id', 'boundary', 'level_id','count', 'opening_boundary', 'openings',
                                    'room_offset', 'room_name', 'room_number', 'room_id'])

new_ceilings = []
room_boundary_options = DB.SpatialElementBoundaryOptions()
all_boundaries = []
all_boundaries1 = []
r = 0

for room in selected_rooms:
    room_level_id = room.Level.Id
    room_offset = room.get_Parameter(BuiltInParameter.ROOM_HEIGHT).AsDouble()
    room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
    room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
    room_id = room.Id
    # List of Boundary Segment comes in an array by itself.
    room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
    all_boundaries = room.GetBoundarySegments(room_boundary_options)
    n = 0
    for bound_set in all_boundaries:
        all_boundaries1.append(room.GetBoundarySegments(room_boundary_options)[n])
        n += 1
    all_boundaries1.pop(0)
    new_ceiling = NewCeiling(ceiling_type_id=ceiling_type_id, boundary=room_boundary,
                         level_id=room_level_id, count = r, opening_boundary = all_boundaries1,
                         openings = n-1, room_offset = room_offset,
                         room_name = room_name, room_number = room_number, room_id = room_id)
    new_ceilings.append(new_ceiling)

#Create ceiling
for new_ceiling in new_ceilings:
    make_ceiling(new_ceiling)
    #forms.toaster.send_toast("Hello World")