# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


import sys
import os
import Autodesk
from collections import namedtuple
from Autodesk.Revit.DB.Architecture import Room
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import Document
from pyrevit import forms 
from System import Guid
from System.Collections.Generic import List
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)
tg = Autodesk.Revit.DB.TransactionGroup(doc)

def main():
    notifications = 0
    #Select Rooms

    selobject = get_selection_basic(uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
    selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
    if not selected_rooms:
        forms.alert('Please select room','Create floor finishing')
        sys.exit()

    def make_opening(nf,boundary):
        co_curves = Autodesk.Revit.DB.CurveArray()
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

    switches = ['Consider Thickness']
    cfgs = {'option1': { 'background': '0xFF55FF'}}
    rops, rswitches = forms.CommandSwitchWindow.show(floor_type_options, message='Select Option',switches=switches,config=cfgs,)

    if rops == None:
        sys.exit()

    floor_type_id = res[rops].Id
    room_boundary_options = Autodesk.Revit.DB.SpatialElementBoundaryOptions()

    def make_floor(room):
        room_level_id = room.Level.Id
        room_offset1 = room.get_Parameter(BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
        room_offset2 = room.get_Parameter(BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
        room_name = room.get_Parameter(BuiltInParameter.ROOM_NAME).AsString()
        room_number = room.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
        room_id = room.Id
        room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
        floorType = doc.GetElement(floor_type_id)
        level = doc.GetElement(room_level_id)
        if app.VersionNumber == "2022" or app.VersionNumber == "2021" or app.VersionNumber == "2020" or app.VersionNumber == "2019":
            floor_curves = Autodesk.Revit.DB.CurveArray()
            for boundary_segment in room_boundary:
                floor_curves.Append((boundary_segment).GetCurve())

            normal_plane = Autodesk.Revit.DB.XYZ.BasisZ
            f = doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
        elif app.VersionNumber == "2023" or app.VersionNumber == "2024" or app.VersionNumber == "2025":
            floor_curves_loop = Autodesk.Revit.DB.CurveLoop()
            floor_curves = List[Autodesk.Revit.DB.Curve]()
            for boundary_segment in room_boundary:
                floor_curves.Add((boundary_segment).GetCurve())
            floor_curves_loop = Autodesk.Revit.DB.CurveLoop.Create(floor_curves)
            curve_list = List[Autodesk.Revit.DB.CurveLoop]()
            curve_list.Add(floor_curves_loop)
            f = Autodesk.Revit.DB.Floor.Create(doc,
                                                curve_list,
                                                floorType.Id, 
                                                level.Id)
        # Input parameter values from rooms
        if rswitches['Consider Thickness'] == False:
            offset2 = doc.GetElement(floor_type_id).get_Parameter(BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1 + offset2)
        if rswitches['Consider Thickness'] == True:
            f.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1)

        global notifications
        # Here we can add custom parameters for floors or ceilings
        try:
            f.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Floor Finishing')

        except:
            notifications += 1

        return f


    tg.Start("Make Floor finishing")
    for room in selected_rooms:
        # Create floor
        t.Start('Create Floor')
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

    if notifications > 0:
        forms.toaster.send_toast('You need to add shared parameters for finishing', \
                title=None, appid=None, icon=None, click=None, actions=None)

if __name__ == '__main__':
    main()