# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import sys
import Autodesk
from Autodesk.Revit import DB
from pyrevit import forms 
from System.Collections.Generic import List
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application
transaction = Autodesk.Revit.DB.Transaction(doc)
transaction_group = Autodesk.Revit.DB.TransactionGroup(doc)

def main():
    ### Make ceiling finishing using ceiling (newer versions)
    if "2022" in app.VersionNumber or "2023" in app.VersionNumber or "2024" in app.VersionNumber or "2025" in app.VersionNumber :
        selobject = get_selection_basic(uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
        selected_rooms = [doc.GetElement(sel) for sel in selobject if doc.GetElement(sel).Category.Name == "Rooms"]
        if not selected_rooms:
            forms.alert( 'Please select room(s)','Create ceiling finishing')
            sys.exit()

        def make_opening(nf,boundary):
            co_curves = Autodesk.Revit.DB.CurveArray()
            for bounds in boundary:
                co_curves.Append(bounds.GetCurve())
            co = doc.Create.NewOpening(nf, co_curves, False)

        #Get floor_types
        def collect_ceilings(doc):
            cl = DB.FilteredElementCollector(doc) \
                    .OfCategory(DB.BuiltInCategory.OST_Ceilings) \
                    .OfClass(DB.CeilingType) \
                    .ToElements()
                    
            return cl

        ceiling_types = collect_ceilings(doc)
        ceiling_type_options = []
        for i in ceiling_types:
            ceiling_type_options.append(i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())



        res = dict(zip(ceiling_type_options,ceiling_types))
        for key in ceiling_types:
            res[key] = key.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)

        switches = ['Consider Thickness']
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
            room_offset1 = room.get_Parameter(DB.BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
            room_offset2 = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
            room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()
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
            if rswitches['Consider Thickness'] == False and doc.GetElement(ceiling_type_id).FamilyName == 'Compound Ceiling':
                offset2 = doc.GetElement(ceiling_type_id).get_Parameter(DB.BuiltInParameter.CEILING_THICKNESS).AsDouble()
                f.get_Parameter(DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(room_offset2 + offset2)
            else:
                f.get_Parameter(DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)

            try:
                #set custom parameters here
                f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Ceiling Finishing')
            except:
                notifications += 1
                pass

            return f


        transaction_group.Start("Make Ceiling(s)")
        for room in selected_rooms:
            # Create floor
            transaction.Start('Create Floor or Ceiling')
            new_ceiling = make_ceiling(room)
            all_boundaries = room.GetBoundarySegments(room_boundary_options)
            transaction.Commit()

            #Create floor opening if needed
            if len(all_boundaries) >1:
                transaction.Start('Create Opening(s)')
                i = 1
                while i < len(all_boundaries):
                    make_opening(new_ceiling, all_boundaries[i])
                    i += 1
                transaction.Commit()
            else:
                pass
        transaction_group.Assimilate()


    ### Make Ceiling using floor (for older versions)

    elif app.VersionNumber == "2021" or app.VersionNumber == "2020" or app.VersionNumber == "2019": 
        selobject = get_selection_basic(uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
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
            cl = DB.FilteredElementCollector(doc) \
                    .OfCategory(DB.BuiltInCategory.OST_Floors) \
                    .OfClass(DB.FloorType) \
                    .ToElements()    
            return cl

        ceiling_types = collect_ceilings(doc)
        ceiling_type_options = []
        for i in ceiling_types:
            ceiling_type_options.append(i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())

        res = dict(zip(ceiling_type_options,ceiling_types))
        for key in ceiling_types:
            res[key] = key.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)

        switches = ['Consider Thickness']
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
            room_offset1 = room.get_Parameter(DB.BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
            room_offset2 = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
            room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()
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
            if rswitches['Consider Thickness'] == True:
                f.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)
            if rswitches['Consider Thickness'] == False:
                offset2 = doc.GetElement(ceiling_type_id).get_Parameter(DB.BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
                f.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2 + offset2)       
            try:
                #set custom parameters here
                f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Ceiling Finishing')
            except:
                notifications += 1
                pass
            return f

        transaction_group.Start("Make Ceiling finishing")
        for room in selected_rooms:
            # Create floor
            transaction.Start('Create Floor/Ceiling')
            new_ceiling = make_ceiling(room)
            all_boundaries = room.GetBoundarySegments(room_boundary_options)
            transaction.Commit()

            #Create floor opening if needed
            if len(all_boundaries) >1:
                transaction.Start('Create Opening(s)')
                i = 1
                while i < len(all_boundaries):
                    make_opening(new_ceiling, all_boundaries[i])
                    i += 1
                transaction.Commit()
            else:
                pass
        transaction_group.Assimilate()    

    if notifications > 0:
        forms.toaster.send_toast('You need to add custom shared parameters', \
                title=None, appid=None, icon=None, click=None, actions=None)
        
if __name__ == '__main__':
    main()