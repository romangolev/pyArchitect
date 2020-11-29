# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

#TODO:Create Shared Parameter if there is no such parameter in project

__doc__ = """Создание отделки потолка для выбранных помещений иструментом Крыша
------------------------------------    
Принцип работы инструмента:
Шаг 1 — Выделить в проекте необходимые помещения
Шаг 2 — В сплывающем окне выбрать тип отделки и указать смещение от уровня

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
              CheckBox('checkbox1', 'Учитывать привязку потолка к уровню'),
              Button('Select')]
form = FlexForm('Создать отделку потолка',components)
win = form.show()

if win == False:
    sys.exit()


#Get the ID of ceiling ( NewFootPrintRoof )
ceiling_type_id = form.values['cl_type'].Id
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
    level = doc.GetElement(new_ceiling.level_id)
    normal_plane = DB.XYZ.BasisZ
    f = doc.Create.NewFootPrintRoof(ceiling_curves, level, ceilingType, clr.StrongBox[ModelCurveArray](ModelCurveArray()))
    db.Element(f).parameters['BA_AI_RoomName'].value = room_name[c]
    db.Element(f).parameters['BA_AI_RoomNumber'].value = room_number[c]
    db.Element(f).parameters['BA_AI_RoomID'].value = room_id[c]
    if form.values['checkbox1'] == True :
        db.Element(f).parameters.builtins['ROOF_LEVEL_OFFSET_PARAM'].value = float(float(form.values['h_offset'])/304.8)
    else:
        db.Element(f).parameters.builtins['ROOF_LEVEL_OFFSET_PARAM'].value = float(float(form.values['h_offset'])/304.8)


def make_opening(new_floor):
    co_curves = DB.CurveArray()
    for bounds in i:
        co_curves.Append(bounds.GetCurve())
    co = doc.Create.NewOpening(fls[new_floor.count-1], co_curves, False)



NewCeiling = namedtuple('NewCeiling', ['ceiling_type_id', 'boundary', 'level_id'])
new_ceilings = []
room_name  = []
room_number = []
room_id = []
room_boundary_options = DB.SpatialElementBoundaryOptions()

for room in selected_rooms:
    room_level_id = room.Level.Id
    # List of Boundary Segment comes in an array by itself.
    room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
    new_ceiling = NewCeiling(ceiling_type_id=ceiling_type_id, boundary=room_boundary,
                         level_id=room_level_id)
    new_ceilings.append(new_ceiling)
    room_name.append(room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString())
    room_number.append(room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString())
    room_id.append(room.Id)
    room_height.append(rrom)


c = 0
#Create ceiling
for new_ceiling in new_ceilings:
    make_ceiling(new_ceiling)
    c += 1