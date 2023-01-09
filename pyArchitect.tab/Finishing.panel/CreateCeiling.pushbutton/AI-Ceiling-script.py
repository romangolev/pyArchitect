# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


__doc__ = """Creates ceiling for selected rooms /
Создание отделки потолка для выбранных помещений
------------------------------------    
Follow the steps / Принцип работы инструмента:
Step 1 / Шаг 1 — Select rooms / Выделить помещения
Step 2 / Шаг 2 — Choose finishing type and select offset / Выбрать тип отделки и указать смещение

When 
При выборе функции "Из помещения" отделка потолка создаётся на основе верхней
высотной отметки помещения. Для корректной работы необходимо настроить 
высоту помещений.
"""

__author__ = 'Roman Golev'
__title__ = "Ceiling\nFinishing"

from email.mime import application
import sys
import os
from collections import namedtuple
import clr
import Autodesk
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Document
from pyrevit import forms 
from System import Guid
from System.Collections.Generic import List

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)
tg = Autodesk.Revit.DB.TransactionGroup(doc)


### Make ceiling finishing using ceiling (newer versions)
if app.VersionNumber == "2022" or app.VersionNumber == "2023":
    selobject = uidoc.Selection.GetElementIds()
    selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
    if not selected_rooms:
        forms.alert( 'Please select room','Create ceiling finishing')
        sys.exit()

    def make_opening(nf,boundary):
        co_curves = Autodesk.Revit.DB.CurveArray()
        for bounds in boundary:
            co_curves.Append(bounds.GetCurve())
        co = doc.Create.NewOpening(nf, co_curves, False)

    #Get floor_types
    def collect_ceilings(doc):
        cl = FilteredElementCollector(doc) \
                .OfCategory(BuiltInCategory.OST_Ceilings) \
                .OfClass(CeilingType) \
                .ToElements()
                
        return cl

    ceiling_types = collect_ceilings(doc)
    ceiling_type_options = []
    for i in ceiling_types:
        ceiling_type_options.append(i.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())



    res = dict(zip(ceiling_type_options,ceiling_types))
    for key in ceiling_types:
        res[key] = key.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)

    switches = ['Offset from room']
    cfgs = {'option1': { 'background': '0xFF55FF'}}
    rops, rswitches = forms.CommandSwitchWindow.show(ceiling_type_options, message='Select Option',switches=switches,config=cfgs,)

    if rops == None:
        sys.exit()

    ceiling_type_id = res[rops].Id
    room_boundary_options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()

    def make_ceiling(room):
        global notifications 
        notifications = 0
        room_level_id = room.Level.Id
        room_offset1 = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
        room_offset2 = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
        room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
        room_id = room.Id
        room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
        ceiling_curves_loop = Autodesk.Revit.DB.CurveLoop()
        ceiling_curves = List[Autodesk.Revit.DB.Curve]()
        for boundary_segment in room_boundary:
            ceiling_curves.Add((boundary_segment).GetCurve())

        ceiling_curves_loop = Autodesk.Revit.DB.CurveLoop.Create(ceiling_curves)
        curve_list = List[Autodesk.Revit.DB.CurveLoop]()
        #   curvelooplist = List[Autodesk.Revit.DB.CurveLoop](ceiling_curves)
        curve_list.Add(ceiling_curves_loop)
        
        ceilingType = doc.GetElement(ceiling_type_id)
        level = doc.GetElement(room_level_id)
        # normal_plane = Autodesk.Revit.DB.XYZ.BasisZ
        f = Autodesk.Revit.DB.Ceiling.Create(doc,
                                            curve_list,
                                            ceilingType.Id, 
                                            level.Id)
        # Input parameter values from rooms
        if rswitches['Offset from room'] == True:
            f.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)
        if rswitches['Offset from room'] == False:
            offset2 = doc.GetElement(ceiling_type_id).get_Parameter(BuiltInParameter.CEILING_THICKNESS).AsDouble()
            f.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(room_offset2 + offset2)
        # Here we can add custom parameters for floors or ceilings
        
        try:
            #set custom parameters here
            # f.get_Parameter(Guid("608a4305-6289-46d7-aa4c-d751919385f1")).Set(room_number)
            # f.get_Parameter(Guid("6a351a5d-c39f-4b49-8db0-af97260c32c0")).Set(room_name)
            f.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Ceiling Finishing')
        except:
            notifications += 1
            pass

        return f


    tg.Start("Make Ceiling(s)")
    for room in selected_rooms:
        # Create floor
        t.Start('Create Floor or Ceiling')
        new_ceiling = make_ceiling(room)
        all_boundaries = room.GetBoundarySegments(room_boundary_options)
        t.Commit()

        #Create floor opening if needed
        if len(all_boundaries) >1:
            t.Start('Create Opening(s)')
            i = 1
            while i < len(all_boundaries):
                make_opening(new_ceiling, all_boundaries[i])
                i += 1
            t.Commit()
        else:
            pass
    tg.Assimilate()


### Make Ceiling using floor (for older versions)

elif app.VersionNumber == "2021" or app.VersionNumber == "2020" or app.VersionNumber == "2019": 
    selobject = uidoc.Selection.GetElementIds()
    selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
    if not selected_rooms:
        forms.alert( 'Please select room','Create ceiling finishing')
        sys.exit()

    def make_opening(nf,boundary):
        co_curves = Autodesk.Revit.DB.CurveArray()
        for bounds in boundary:
            co_curves.Append(bounds.GetCurve())
        co = doc.Create.NewOpening(nf, co_curves, False)

    #Get floor_types
    def collect_ceilings(doc):
        cl = FilteredElementCollector(doc) \
                .OfCategory(BuiltInCategory.OST_Floors) \
                .OfClass(FloorType) \
                .ToElements()
                
        return cl

    ceiling_types = collect_ceilings(doc)
    ceiling_type_options = []
    for i in ceiling_types:
        ceiling_type_options.append(i.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())



    res = dict(zip(ceiling_type_options,ceiling_types))
    for key in ceiling_types:
        res[key] = key.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)

    switches = ['Offset from room']
    cfgs = {'option1': { 'background': '0xFF55FF'}}
    rops, rswitches = forms.CommandSwitchWindow.show(ceiling_type_options, message='Select Option',switches=switches,config=cfgs,)

    if rops == None:
        sys.exit()

    ceiling_type_id = res[rops].Id
    room_boundary_options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()

    def make_ceiling(room):
        global notifications 
        notifications = 0
        room_level_id = room.Level.Id
        room_offset1 = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
        room_offset2 = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
        room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
        room_id = room.Id
        room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
        floor_curves = Autodesk.Revit.DB.CurveArray()
        for boundary_segment in room_boundary:
            floor_curves.Append((boundary_segment).GetCurve())
        floorType = doc.GetElement(ceiling_type_id)
        level = doc.GetElement(room_level_id)
        normal_plane = Autodesk.Revit.DB.XYZ.BasisZ
        f = doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
        # Input parameter values from rooms
        if rswitches['Offset from room'] == True:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)
        if rswitches['Offset from room'] == False:
            offset2 = doc.GetElement(ceiling_type_id).get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2 + offset2)
        # Here we can add custom parameters for floors or ceilings
        
        try:
            #set custom parameters here
            # f.get_Parameter(Guid("608a4305-6289-46d7-aa4c-d751919385f1")).Set(room_number)
            # f.get_Parameter(Guid("6a351a5d-c39f-4b49-8db0-af97260c32c0")).Set(room_name)
            f.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Ceiling Finishing')
        except:
            notifications += 1
            pass

        return f


    tg.Start("Make Ceiling finishing")
    for room in selected_rooms:
        # Create floor
        t.Start('Create Floor/Ceiling')
        new_ceiling = make_ceiling(room)
        all_boundaries = room.GetBoundarySegments(room_boundary_options)
        t.Commit()

        #Create floor opening if needed
        if len(all_boundaries) >1:
            t.Start('Create Opening(s)')
            i = 1
            while i < len(all_boundaries):
                make_opening(new_ceiling, all_boundaries[i])
                i += 1
            t.Commit()
        else:
            pass
    tg.Assimilate()    




if notifications > 0:
    forms.toaster.send_toast('You need to add custom shared parameters', \
            title=None, appid=None, icon=None, click=None, actions=None)