# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


__doc__ = """Считает общую площадь по типу отделки и записывает параметры 

Берёт значение типа отделки и его площадь, записывает данные в помещения.
Для того, чтобы скрипт обработал помещения, необходимо чтобы были заполнены параметры для элементов отделки:
BA_AI_FinishingType => Ceiling Finishing
BA_AI_RoomID

В типоразмере отделки должен быть записан параметр BA_AI_Structure.
(Заполняется при помощи скрипта "Ceiling Layers")

Для работы скрипта необходимы следующие общие параметры проекта:
BA_AI_RoomFinishingDescription-Ceiling
BA_AI_RoomFinishingArea-Ceiling
"""
__author__ = 'Roman Golev'
__title__ = "Finishing Areas Ceiling"

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit import DB
import clr
clr.AddReference("System")
from collections import namedtuple
from rpw import db
from pyrevit import forms
import sys

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

roofs = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Roofs)
rooms = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rooms)
roomId = []
dataset = []


RoomData = namedtuple('FinRoofs',['roofid','roomid','rooftype','roofarea','roomname','roomnumber']) 

for room in rooms:
    roomId.append(room.Id.ToString())

for roof in roofs:
    if roof.ToString() == "Autodesk.Revit.DB.FootPrintRoof" and db.Element(roof).parameters['BA_AI_FinishingType'].value == 'Ceiling Finishing':
        finishing_id = db.Element(roof).parameters['BA_AI_RoomID'].value
        #print(roomId.count(finishing_id))
        if roomId.count(finishing_id) > 0 :
            roofarea = float(roof.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED).AsDouble()/10.764)
            roomname = db.Element(roof).parameters['BA_AI_RoomName'].value
            roomnumber = db.Element(roof).parameters['BA_AI_RoomNumber'].value
            #print(roof.GetType)
            data = RoomData(roof.Id, finishing_id, roof.RoofType, roofarea, roomname, roomnumber)
            dataset.append(data)
        else:
            forms.alert("No Ceiling Finishing in project!1")
            sys.exit()
    else:
        pass
            

for unit in dataset:
    area = unit.roofarea

operated_rooms = {}
for unit in dataset:
    operated_rooms[unit.roomid] = ""

for n in operated_rooms:
    rooms_data = {}
    for unit in dataset:
        if unit.roomid == n:
            try:
                rooms_data[str(db.Element(unit.rooftype).parameters['BA_AI_Structure'].value)] = 0
            except:
                forms.alert("You need to add GOST Scheduling parameters")
                sys.exit()
        else:
            pass
    operated_rooms[n] = rooms_data

for n in operated_rooms:
    area = 0
    for unit in dataset:
        rooms_data = operated_rooms[n]
        for type in rooms_data:
            if type == str(db.Element(unit.rooftype).parameters['BA_AI_Structure'].value) and unit.roomid == n:
                rooms_data[type] += unit.roofarea 
                #print('True')
            else:
                #print('False')
                pass

with db.Transaction('BA_CeilingFinishing Parameters'):  
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
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingDescription-Ceiling'].value = type_all
        db.Element(doc.GetElement(ElementId(int(key)))).parameters['BA_AI_RoomFinishingArea-Ceiling'].value = area_all
