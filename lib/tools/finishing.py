# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
import sys
import uuid
import Autodesk.Revit.DB as DB
from pyrevit import forms
from System.Collections.Generic import List
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS

class FinishingRoom(object):
    def __init__(self, rvt_elem): 
        self.rvt_elem = rvt_elem # type: DB.Element

class FinishingTool(object):
    """ """
    def __init__(self, uiapp):
        # assert mode in ["floor", "wall", "ceiling"] else raise("Invalid mode")
        self.uiapp = uiapp # type: DB.UIApplication
        self.uidoc = uiapp.ActiveUIDocument # type: DB.UIDocument
        self.doc = uiapp.ActiveUIDocument.Document # type: DB.Document
        self.app = uiapp.Application # type: DB.Application


    def create_floors(self):
        transaction = DB.Transaction(self.doc)
        transaction_group = DB.TransactionGroup(self.doc)

        notifications = 0
        #Select Rooms

        selobject = get_selection_basic(self.uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
        selected_rooms = [self.doc.GetElement(sel) for sel in selobject if self.doc.GetElement(sel).Category.Name == "Rooms"]
        if not selected_rooms:
            forms.alert('Please select room','Create floor finishing')
            sys.exit()

        def make_opening(nf,boundary):
            co_curves = DB.CurveArray()
            for bounds in boundary:
                co_curves.Append(bounds.GetCurve())
            co = self.doc.Create.NewOpening(nf, co_curves, False)

        #Get floor_types
        def collect_floors(doc):
            cl = DB.FilteredElementCollector(doc) \
                    .OfCategory(DB.BuiltInCategory.OST_Floors) \
                    .OfClass(DB.FloorType) \
                    .ToElements()
                    
            return cl


        floor_types = collect_floors(self.doc)
        floor_type_options = []
        for i in floor_types:
            floor_type_options.append(i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())

        res = dict(zip(floor_type_options, floor_types))
        for key in floor_types:
            res[key] = key.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)

        switches = ['Consider Thickness']
        cfgs = {'option1': { 'background': '0xFF55FF'}}
        rops, rswitches = forms.CommandSwitchWindow.show(floor_type_options, message='Select Option',switches=switches,config=cfgs,)

        if rops == None:
            sys.exit()

        floor_type_id = res[rops].Id
        room_boundary_options = DB.SpatialElementBoundaryOptions()

        def make_floor(room):
            room_level_id = room.Level.Id
            room_offset1 = room.get_Parameter(DB.BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
            room_offset2 = room.get_Parameter(DB.BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
            room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()
            room_id = room.Id
            room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
            floorType = self.doc.GetElement(floor_type_id)
            level = self.doc.GetElement(room_level_id)
            if self.app.VersionNumber == "2022" or self.app.VersionNumber == "2021" or self.app.VersionNumber == "2020" or self.app.VersionNumber == "2019":
                floor_curves = DB.CurveArray()
                for boundary_segment in room_boundary:
                    floor_curves.Append((boundary_segment).GetCurve())

                normal_plane = DB.XYZ.BasisZ
                f = self.doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
            elif self.app.VersionNumber == "2023" or self.app.VersionNumber == "2024" or self.app.VersionNumber == "2025":
                floor_curves_loop = DB.CurveLoop()
                floor_curves = List[DB.Curve]()
                for boundary_segment in room_boundary:
                    floor_curves.Add((boundary_segment).GetCurve())
                floor_curves_loop = DB.CurveLoop.Create(floor_curves)
                curve_list = List[DB.CurveLoop]()
                curve_list.Add(floor_curves_loop)
                f = DB.Floor.Create(self.doc,
                                                    curve_list,
                                                    floorType.Id, 
                                                    level.Id)
            # Input parameter values from rooms
            if rswitches['Consider Thickness'] == False:
                offset2 = self.doc.GetElement(floor_type_id).get_Parameter(DB.BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
                f.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1 + offset2)
            if rswitches['Consider Thickness'] == True:
                f.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset1)

            global notifications
            # Here we can add custom parameters for floors or ceilings
            try:
                f.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Floor Finishing')

            except:
                notifications += 1

            return f


        transaction_group.Start("Make Floor finishing")
        for room in selected_rooms:
            # Create floor
            transaction.Start('Create Floor')
            new_floor = make_floor(room)
            all_boundaries = room.GetBoundarySegments(room_boundary_options)
            transaction.Commit()

            #Create floor opening if needed
            if len(all_boundaries) >1:
                transaction.Start('Create Opening(s)')
                i = 1
                while i < len(all_boundaries):
                    make_opening(new_floor, all_boundaries[i])
                    i += 1
                transaction.Commit()
            else:
                pass
        transaction_group.Assimilate()

        if notifications > 0:
            forms.toaster.send_toast('You need to add shared parameters for finishing', \
                    title=None, appid=None, icon=None, click=None, actions=None)

    def create_walls(self):
        transaction = DB.Transaction(self.doc)
        transaction_group = DB.TransactionGroup(self.doc)
        # Select rooms 
        selobject = get_selection_basic(self.uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
        selected_rooms = [self.doc.GetElement(sel) for sel in selobject if self.doc.GetElement(sel).Category.Name == "Rooms"]
        if not selected_rooms:
            forms.alert('MakeWalls', 'You need to select at lest one Room.')
            sys.exit()

        #Get floor_types
        def collect_walls(doc):
            return DB.FilteredElementCollector(doc) \
                    .OfCategory(DB.BuiltInCategory.OST_Walls) \
                    .OfClass(DB.WallType) \
                    .ToElements()

        wall_types = [i for i in collect_walls(self.doc) if i.FamilyName != "Curtain Wall"]
        wall_type_options = [i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() for i in wall_types]
        # for i in wall_types:
        # 	wall_type_options.append(i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())


        res = dict(zip(wall_type_options,wall_types))

        switches = ['Inside loops finishing', 'Include Room Separation Lines']
        rops, rswitches = forms.CommandSwitchWindow.show( wall_type_options, 
                                                message='Select Option',
                                                switches=switches)

        if rops == None:
            sys.exit()

        wall_type = res[rops]
        wall_type_id = wall_type.Id
        notifications = 0

        # Duplicating wall type creating the same layer set with double width
        # to deal with the offset API issue
        def duplicate_wall_type(type_of_wall):
            wall_type1 = type_of_wall.Duplicate(str(uuid.uuid4()))
            cs1 = wall_type1.GetCompoundStructure()
            layers1 = cs1.GetLayers()
            for layer in layers1:
                cs1.SetLayerWidth(layer.LayerId,2*cs1.GetLayerWidth(layer.LayerId))
            wall_type1.SetCompoundStructure(cs1)
            return wall_type1
        
        room_boundary_options = DB.SpatialElementBoundaryOptions()
        w = []

        def make_wall(room, temp_type, line):
            room_level_id = room.Level.Id
            # List of Boundary Segment comes in an array by itself.
            room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
            room_name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()
            room_number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()
            room_id = room.Id
            room_height = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
            level = room_level_id
            if room_height > 0:
                wall_height = float(room_height)
            else:
                wall_height = 1500/304.8	

            w = DB.Wall.Create(self.doc, line, temp_type.Id, level, wall_height, 0.0, False, False)
            w.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
            global notifications
            try:
                w.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Отделка стен')
            except:
                notifications += 1
            # Here we can add parameter values for wall finishing
            # try:
                # w.get_Parameter().Set()
            # except:
            # 	forms.alert('You need to add shared parameters for finishing')
            return w

        #Create wall
        transaction_group.Start("Make wall finishing")

        transaction.Start('Create Temp Type')
        tmp = duplicate_wall_type(wall_type)
        transaction.Commit()

        transaction.Start('Create Finishing Walls')
        wallz = []
        bound_walls =[]
        wallzz = []
        for room in selected_rooms:
            room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
            plug = 1
            # Filtering by hostwall type

            for bound in room_boundary:
                try :
                    if self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" \
                        and self.doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
                        # Filtering small lines less than 10 mm Lenght
                        if bound.GetCurve().Length > 10/304.8:
                            bound_walls.append(self.doc.GetElement(bound.ElementId))
                            new_wall = make_wall(room, tmp,bound.GetCurve())
                            wallzz.append(new_wall)
                            wallz.append(new_wall.Id)
                            #new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
                            new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

                    elif self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
                        self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns" :
                        # Filtering small lines less than 10 mm Lenght
                        if bound.GetCurve().Length > 10/304.8:
                            bound_walls.append(self.doc.GetElement(bound.ElementId))
                            new_wall = make_wall(room, tmp,bound.GetCurve())
                            wallzz.append(new_wall)
                            wallz.append(new_wall.Id)
                            #new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
                            new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

                    elif rswitches['Include Room Separation Lines'] == True and \
                        self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "<Room Separation>":
                        # Filtering small lines less than 10 mm Lenght
                        if bound.GetCurve().Length > 10/304.8:
                            bound_walls.append(self.doc.GetElement(bound.ElementId))
                            new_wall = make_wall(room, tmp,bound.GetCurve())
                            wallzz.append(new_wall)
                            wallz.append(new_wall.Id)
                            #new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
                            new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
                    else:
                        pass
                except :
                    0

            if rswitches['Inside loops finishing'] == True:
                # transaction.Start('Create Finishing Walls for Openings')
                for room in selected_rooms:
                    room_boundary2 = room.GetBoundarySegments(room_boundary_options)
                    i = 1
                    while i < len(room_boundary2):
                        for bound in room_boundary2[i]:
                            try :
                                if self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Walls" \
                                    and self.doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic":
                                    # Filtering small lines less than 10 mm Lenght
                                    if bound.GetCurve().Length > 10/304.8:
                                        bound_walls.append(self.doc.GetElement(bound.ElementId))
                                        new_wall = make_wall(room, tmp,bound.GetCurve())
                                        wallzz.append(new_wall)
                                        wallz.append(new_wall.Id)
                                        #new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
                                        new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)

                                elif self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Structural Columns" or \
                                self.doc.GetElement(bound.ElementId).Category.Name.ToString() == "Columns":
                                    # Filtering small lines less than 10 mm Lenght
                                    if bound.GetCurve().Length > 10/304.8:
                                        bound_walls.append(doc.GetElement(bound.ElementId))
                                        new_wall = make_wall(room, tmp,bound.GetCurve())
                                        wallzz.append(new_wall)
                                        wallz.append(new_wall.Id)
                                        #new_wall.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(4)
                                        new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
                                else:
                                    pass
                            except :
                                pass
                        i += 1
                # transaction.Commit()
            elif rswitches['Inside loops finishing'] == False:
                pass
        transaction.Commit()



        #TODO: Supress warning with win32api 
        # https://thebuildingcoder.typepad.com/blog/2018/01/gathering-and-returning-failure-information.html


        res = dict(zip(bound_walls,wallzz))
        transaction.Start('Change Type and Join Walls with hosts')
        col1 = List[DB.ElementId](wallz)
        DB.Element.ChangeTypeId(self.doc, col1, wall_type_id)
        transaction.Commit()


        transaction.Start('Join Walls with hosts')
        for i in res:
            try:
                DB.JoinGeometryUtils.JoinGeometry(self.doc, i, res[i])
            except:
                pass
        transaction.Commit()



        transaction.Start('Delete Temp Type')
        self.doc.Delete(tmp.Id)
        transaction.Commit()

        transaction_group.Assimilate()


        if notifications > 0:
            forms.toaster.send_toast('You need to add shared parameters for finishing', \
                    title=None, appid=None, icon=None, click=None, actions=None)

    def create_ceilings(self):
        transaction = DB.Transaction(self.doc)
        transaction_group = DB.TransactionGroup(self.doc)
        
        ### Make ceiling finishing using ceiling (newer versions)
        if "2022" in self.app.VersionNumber or "2023" in self.app.VersionNumber or "2024" in self.app.VersionNumber or "2025" in self.app.VersionNumber :
            selobject = get_selection_basic(self.uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
            selected_rooms = [self.doc.GetElement(sel) for sel in selobject if self.doc.GetElement(sel).Category.Name == "Rooms"]
            if not selected_rooms:
                forms.alert( 'Please select room(s)','Create ceiling finishing')
                sys.exit()

            def make_opening(nf,boundary):
                co_curves = DB.CurveArray()
                for bounds in boundary:
                    co_curves.Append(bounds.GetCurve())
                co = self.doc.Create.NewOpening(nf, co_curves, False)

            #Get floor_types
            def collect_ceilings(doc):
                cl = DB.FilteredElementCollector(doc) \
                        .OfCategory(DB.BuiltInCategory.OST_Ceilings) \
                        .OfClass(DB.CeilingType) \
                        .ToElements()
                        
                return cl

            ceiling_types = collect_ceilings(self.doc)
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
            room_boundary_options = DB.SpatialElementBoundaryOptions()

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
                ceiling_curves_loop = DB.CurveLoop()
                ceiling_curves = List[DB.Curve]()
                for boundary_segment in room_boundary:
                    ceiling_curves.Add((boundary_segment).GetCurve())

                ceiling_curves_loop = DB.CurveLoop.Create(ceiling_curves)
                curve_list = List[DB.CurveLoop]()
                #   curvelooplist = List[DB.CurveLoop](ceiling_curves)
                curve_list.Add(ceiling_curves_loop)
                
                ceilingType = self.doc.GetElement(ceiling_type_id)
                level = self.doc.GetElement(room_level_id)
                # normal_plane = DB.XYZ.BasisZ
                f = DB.Ceiling.Create(self.doc,
                                                    curve_list,
                                                    ceilingType.Id, 
                                                    level.Id)
                # Input parameter values from rooms
                if rswitches['Consider Thickness'] == False and self.doc.GetElement(ceiling_type_id).FamilyName == 'Compound Ceiling':
                    offset2 = self.doc.GetElement(ceiling_type_id).get_Parameter(DB.BuiltInParameter.CEILING_THICKNESS).AsDouble()
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

        elif self.app.VersionNumber == "2021" or self.app.VersionNumber == "2020" or self.app.VersionNumber == "2019": 
            selobject = get_selection_basic(self.uidoc,CustomISelectionFilterByIdInclude(ID_ROOMS))
            selected_rooms = [self.doc.GetElement(sel) for sel in selobject if self.doc.GetElement(sel).Category.Name == "Rooms"]
            if not selected_rooms:
                forms.alert( 'Please select room','Create ceiling finishing')
                sys.exit()

            def make_opening(nf,boundary):
                co_curves = DB.CurveArray()
                for bounds in boundary:
                    co_curves.Append(bounds.GetCurve())
                co = self.doc.Create.NewOpening(nf, co_curves, False)

            #Get floor_types
            def collect_ceilings(doc):
                cl = DB.FilteredElementCollector(doc) \
                        .OfCategory(DB.BuiltInCategory.OST_Floors) \
                        .OfClass(DB.FloorType) \
                        .ToElements()    
                return cl

            ceiling_types = collect_ceilings(self.doc)
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
            room_boundary_options = DB.SpatialElementBoundaryOptions()

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
                floor_curves = DB.CurveArray()
                for boundary_segment in room_boundary:
                    floor_curves.Append((boundary_segment).GetCurve())
                floorType = self.doc.GetElement(ceiling_type_id)
                level = self.doc.GetElement(room_level_id)
                normal_plane = DB.XYZ.BasisZ
                f = self.doc.Create.NewFloor(floor_curves, floorType, level, False, normal_plane)
                # Input parameter values from rooms
                if rswitches['Consider Thickness'] == True:
                    f.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(room_offset2)
                if rswitches['Consider Thickness'] == False:
                    offset2 = self.doc.GetElement(ceiling_type_id).get_Parameter(DB.BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM).AsDouble()
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