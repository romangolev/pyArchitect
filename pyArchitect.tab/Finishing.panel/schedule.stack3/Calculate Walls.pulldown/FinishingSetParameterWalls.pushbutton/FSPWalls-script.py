# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


__doc__ = """Считает общую площадь по типу отделки и записывает параметры 

Берёт значение типа отделки и его площадь, записывает данные в помещения.
Для того, чтобы скрипт обработал помещения, необходимо чтобы были заполнены параметры для элементов отделки:
BA_AI_FinishingType => Wall Finishing
BA_AI_RoomID

В типоразмере отделки должен быть записан параметр BA_AI_Structure.
(Заполняется при помощи скрипта "Wall Layers")

Для работы скрипта необходимы следующие общие параметры проекта:
BA_AI_RoomFinishingDescription-Wall
BA_AI_RoomFinishingArea-Wall
"""

__author__ = 'Roman Golev'
__title__ = "Finishing Areas Walls"

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit import DB
import clr
clr.AddReference("System")
from collections import namedtuple
import rpw
from rpw import db
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

walls = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls)
rooms = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rooms)
roomId = []
dataset = []


RoomData = namedtuple('FinWalls',['wallid','roomid','walltype','wallarea','roomname','roomnumber']) 

for room in rooms:
    roomId.append(room.Id.ToString())

for wall in walls:
    if wall.ToString() == "Autodesk.Revit.DB.Wall" and db.Element(wall).parameters['BA_AI_FinishingType'].value == 'Wall Finishing':
        finishing_id = db.Element(wall).parameters['BA_AI_RoomID'].value
        if roomId.count(finishing_id) > 0 :
            wallarea = float(wall.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble()/10.764)
            roomname = db.Element(wall).parameters['BA_AI_RoomName'].value
            roomnumber = db.Element(wall).parameters['BA_AI_RoomNumber'].value
            data = RoomData(wall.Id, finishing_id, wall.WallType, wallarea, roomname, roomnumber)
            dataset.append(data)

for unit in dataset:
    area = unit.wallarea


operated_rooms = {}
for unit in dataset:
    operated_rooms[unit.roomid] = ""

for n in operated_rooms:
    rooms_data = {}
    for unit in dataset:
        if unit.roomid == n:
            rooms_data[str(db.Element(unit.walltype).parameters['BA_AI_Structure'].value)] = 0
        else:
            pass
    operated_rooms[n] = rooms_data

for n in operated_rooms:
    area = 0
    for unit in dataset:
        rooms_data = operated_rooms[n]
        for type in rooms_data:
            if type == str(db.Element(unit.walltype).parameters['BA_AI_Structure'].value) and unit.roomid == n:
                rooms_data[type] += unit.wallarea 
                #print('True')
            else:
                #print('False')
                pass

with db.Transaction('BA_WallFinishing Parameters'):  
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
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingDescription-Wall'].value = type_all
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingArea-Wall'].value = area_all
