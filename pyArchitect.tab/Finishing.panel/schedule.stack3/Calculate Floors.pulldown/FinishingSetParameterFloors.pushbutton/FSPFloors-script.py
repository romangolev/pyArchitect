# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Считает общую площадь по типу отделки и записывает параметры 

Берёт значение типа отделки и его площадь, записывает данные в помещения.
Для того, чтобы скрипт обработал помещения, необходимо чтобы были заполнены параметры для элементов отделки:
BA_AI_FinishingType => Floor Finishing
BA_AI_RoomID

В типоразмере отделки должен быть записан параметр BA_AI_Structure.
(Заполняется при помощи скрипта "Floor Layers")

Для работы скрипта необходимы следующие общие параметры проекта:
BA_AI_RoomFinishingDescription-Floor
BA_AI_RoomFinishingArea-Floor
"""

__author__ = 'Roman Golev'
__title__ = "Finishing Areas Floors"

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit import DB
import clr
clr.AddReference("System")
from collections import namedtuple
from rpw import db
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

floors = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Floors)
rooms = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rooms)
roomId = []
dataset = []


RoomData = namedtuple('FinFloors',['floorid','roomid','floortype','floorarea','roomname','roomnumber']) 

for room in rooms:
    roomId.append(room.Id.ToString())

for floor in floors:
    if floor.ToString() == "Autodesk.Revit.DB.Floor" and db.Element(floor).parameters['BA_AI_FinishingType'].value == 'Floor Finishing':
        finishing_id = db.Element(floor).parameters['BA_AI_RoomID'].value
        if roomId.count(finishing_id) > 0 :
            floorarea = float(floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble()/10.764)
            roomname = db.Element(floor).parameters['BA_AI_RoomName'].value
            roomnumber = db.Element(floor).parameters['BA_AI_RoomNumber'].value
            data = RoomData(floor.Id, finishing_id, floor.FloorType, floorarea, roomname, roomnumber)
            #print(floor.GetType())
            dataset.append(data)

for unit in dataset:
    area = unit.floorarea


operated_rooms = {}
for unit in dataset:
    operated_rooms[unit.roomid] = ""

for n in operated_rooms:
    rooms_data = {}
    for unit in dataset:
        if unit.roomid == n:
            rooms_data[str(db.Element(unit.floortype).parameters['BA_AI_Structure'].value)] = 0
        else:
            pass
    operated_rooms[n] = rooms_data

for n in operated_rooms:
    area = 0
    for unit in dataset:
        rooms_data = operated_rooms[n]
        for type in rooms_data:
            if type == str(db.Element(unit.floortype).parameters['BA_AI_Structure'].value) and unit.roomid == n:
                rooms_data[type] += unit.floorarea 
                #print('True')
            else:
                #print('False')
                pass

with db.Transaction('BA_FloorFinishing Parameters'):  
    for key in operated_rooms:
        a = operated_rooms[key]
        n = 1
        area_all = ''
        type_all = ''
        areatext = ''
        typetext = ''
        for k in a:   
            areatext = str(n) + ". "  + str(round(a[k],2)) + " м2 \r\n"
            typetext = str(n) + ". "  + str(k) + "\r\n"
            n += 1
            area_all += areatext
            type_all += typetext
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingDescription-Floor'].value = type_all
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingArea-Floor'].value = area_all
