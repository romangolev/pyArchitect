# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev
import sys
import uuid
import Autodesk.Revit.DB as DB
from pyrevit import forms
from System.Collections.Generic import List, Dictionary
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS, ID_WALLS, ID_COLUMNS, ID_STRUCTURAL_COLUMNS, ID_SEPARATION_LINES
from core.collectror import UniversalProjectCollector as UPC

class FinishingRoom(object):
    def __init__(self, rvt_room_elem): 
        self.rvt_room_elem = rvt_room_elem  # type: DB.Element
        self.doc = rvt_room_elem.Document   # type: DB.Document
        self.new_walls = []                 # type: List[DB.Wall]
        self.new_walls_and_hosts = {}       # type: Dictionary[DB.Wall, DB.Element]

    @property
    def id(self):
        return self.rvt_room_elem.Id

    @property
    def level_id(self):
        return self.rvt_room_elem.Level.Id

    @property
    def room_number(self):
        return self.rvt_room_elem.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER).AsString()

    @property
    def room_name(self):
        return self.rvt_room_elem.get_Parameter(DB.BuiltInParameter.ROOM_NAME).AsString()

    @property
    def boundaries(self):
        # First boundlist always is the outer boundary
        return self.rvt_room_elem.GetBoundarySegments(DB.SpatialElementBoundaryOptions())

    @property
    def outer_boundaries(self):
        return self.boundaries[0]

    @property
    def inner_boundaries(self):
        return self.boundaries[1:]

    @property
    def boundary_count(self):
        return len(self.boundaries)
    
    def make_finishing_floor(self, floor_type, rswitches, app, mode="default"):
        room = self.rvt_room_elem
        room_offset1 = room.get_Parameter(DB.BuiltInParameter.ROOM_LOWER_OFFSET).AsDouble()
        room_offset2 = room.get_Parameter(DB.BuiltInParameter.ROOM_UPPER_OFFSET).AsDouble()
        level = self.doc.GetElement(self.level_id)

        if int(app.VersionNumber) <= 2022:

            if rswitches['Include Door Notches'] == False:
                floor_curves = DB.CurveArray()
                for boundary_segment in self.outer_boundaries:
                    floor_curves.Append((boundary_segment).GetCurve())

            elif rswitches['Include Door Notches'] == True:
                floor_curves = self.generate_floor_outline()
            
            new_floor = self.doc.Create.NewFloor(floor_curves,
                                                 floor_type,
                                                 level,
                                                 False,
                                                 DB.XYZ.BasisZ)
            
        elif int(app.VersionNumber) > 2022:
            if rswitches['Include Door Notches'] == False:
                floor_curves_loop = DB.CurveLoop()
                floor_curves = List[DB.Curve]()
                for boundary_segment in self.outer_boundaries:
                    floor_curves.Add((boundary_segment).GetCurve())
                floor_curves_loop = DB.CurveLoop.Create(floor_curves)
                curve_list = List[DB.CurveLoop]()
                curve_list.Add(floor_curves_loop)
            elif rswitches['Include Door Notches'] == True:
                floor_curves_loop = DB.CurveLoop()
                floor_curves = List[DB.Curve]()
                main_array = self.generate_floor_outline()
                for boundary_segment in main_array:
                    floor_curves.Add(boundary_segment)
                floor_curves_loop = DB.CurveLoop.Create(floor_curves)
                curve_list = List[DB.CurveLoop]()
                curve_list.Add(floor_curves_loop)

            new_floor = DB.Floor.Create(self.doc,
                                        curve_list,
                                        floor_type.Id,
                                        level.Id)
            
        # Input parameter values from rooms
        if rswitches['Consider Thickness'] == False:
            offset2 = floor_type\
                .get_Parameter(DB.BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM)\
                .AsDouble()
            new_floor.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)\
                .Set(room_offset1 + offset2 if mode == "default" else room_offset2 + offset2)
        if rswitches['Consider Thickness'] == True:
            new_floor.get_Parameter(DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)\
                .Set(room_offset1 if mode == "default" else room_offset2)

        # Here we can add custom parameters for floors or ceilings
        param_value = 'Floor Finishing : ' + 'Room {}'.format(self.room_number)\
              if mode == "default" else 'Ceiling Finishing : ' + 'Room {}'.format(self.room_number)
        new_floor.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(param_value)
        return new_floor

    def do_we_need_to_make_wall(self, bound, rswitches):
        try:
            # host of bound line is a basic wall
            condition1 = self.doc.GetElement(bound.ElementId).Category.Id.ToString() == str(ID_WALLS[0])     \
                and self.doc.GetElement(bound.ElementId).WallType.Kind.ToString() == "Basic"
        except:
            condition1 = False        
        try:
            # host of bound line is a column or a structural column
            condition2 = self.doc.GetElement(bound.ElementId).Category.Id.ToString() == str(ID_COLUMNS[0])  \
                or self.doc.GetElement(bound.ElementId).Category.Id.ToString() == str(ID_STRUCTURAL_COLUMNS[0])
        except:
            condition2 = False
        try:
            # host of bound line is a room separation line and the switch is on
            condition3 = rswitches['Include Room Separation Lines'] == True \
                and self.doc.GetElement(bound.ElementId).Category.Id.ToString() == str(ID_SEPARATION_LINES[0])
        except:
            condition3 = False

        return any([condition1, condition2, condition3])

    def make_finishing_walls_outer(self, temp_type, rswitches):
        # Filtering small lines less than 10 mm Lenght
        filtered_boundaries = [bound for bound in self.outer_boundaries if bound.GetCurve().Length > 10/304.8]
        self.boundwalls = [self.doc.GetElement(bound.ElementId) for bound in filtered_boundaries]
        for bound in filtered_boundaries:
            if self.do_we_need_to_make_wall(bound, rswitches):
                new_wall = self.make_finishing_wall_by_line(bound.GetCurve(), temp_type)
                self.new_walls_and_hosts[new_wall] = self.doc.GetElement(bound.ElementId)
                self.new_walls.append(new_wall)

    def make_finishing_walls_inner(self, temp_type, rswitches):
        for boundary in self.inner_boundaries:
            for bound in boundary:
                if self.do_we_need_to_make_wall(bound, rswitches):
                    try:
                        new_wall = self.make_finishing_wall_by_line(bound.GetCurve(), temp_type)
                        if hasattr(bound, 'ElementId'):
                            self.new_walls_and_hosts[new_wall] = self.doc.GetElement(bound.ElementId)
                        else:
                            self.new_walls_and_hosts[new_wall] = None
                        self.new_walls.append(new_wall)
                    except: 
                        import traceback
                        print(traceback.format_exc())
                        pass

    def make_finishing_wall_by_line(self, line, temp_type):
        room = self.rvt_room_elem
        room_height = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
        if room_height > 0:
            wall_height = float(room_height)
        else:
            wall_height = 1500/304.8

        new_wall = DB.Wall.Create(self.doc, line, temp_type.Id, self.level_id, wall_height, 0.0, False, False)
        new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
        new_wall.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set('Wall finishing')
        return new_wall

    def make_finishing_ceiling(self, ceiling_type, rswitches):
        room = self.rvt_room_elem
        room_offset2 = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
        room_boundary_options = DB.SpatialElementBoundaryOptions()
        room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
        ceiling_curves_loop = DB.CurveLoop()
        ceiling_curves = List[DB.Curve]()
        for boundary_segment in room_boundary:
            ceiling_curves.Add((boundary_segment).GetCurve())

        ceiling_curves_loop = DB.CurveLoop.Create(ceiling_curves)
        curve_list = List[DB.CurveLoop]()
        curve_list.Add(ceiling_curves_loop)
        
        level = self.doc.GetElement(self.level_id)
        new_ceiling = DB.Ceiling.Create(self.doc,
                                curve_list,
                                ceiling_type.Id,
                                level.Id)
        # Input parameter values from rooms
        if rswitches['Consider Thickness'] == False \
                and ceiling_type.FamilyName == 'Compound Ceiling':
            offset2 = self.doc.GetElement(ceiling_type)\
                .get_Parameter(DB.BuiltInParameter.CEILING_THICKNESS).AsDouble()
            new_ceiling.get_Parameter(DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM)\
                .Set(room_offset2 + offset2)
        else:
            new_ceiling.get_Parameter(DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM)\
                .Set(room_offset2)

        new_ceiling.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)\
            .Set('Ceiling Finishing')
        return new_ceiling

    def make_openings(self, nf):
        co_curves = DB.CurveArray()
        # Please GOD forgive me for using N^2 complexity ... Amen
        for boundary in self.inner_boundaries:
            for bounds in boundary:
                co_curves.Append(bounds.GetCurve())
        opening = self.doc.Create.NewOpening(nf, co_curves, False)

    def order_doors_by_proximity(self, main_line, doors):
        return sorted(doors, key=lambda door: self.doc.GetElement(door).Location.Point.DistanceTo(main_line.GetEndPoint(0)))

    @staticmethod
    def add_full_door_notch(curve_array, door, door_width, wall_width):
        """
        Modifies wall line by adding full door notch
        """
        if curve_array.Size == 0:
            raise ValueError("Curve array is empty")
        elif curve_array.Size == 1:
            line_to_modify = curve_array[curve_array.Size-1]
            curve_array = DB.CurveArray()
        else:
            line_to_modify = curve_array[curve_array.Size-1]
            newcurve_array = DB.CurveArray()
            for i in range(curve_array.Size-1):
                newcurve_array.Append(curve_array.Item[i])
            curve_array = newcurve_array

        point1 = door.Location.Point - DB.XYZ(door_width/2, 0, 0) + DB.XYZ(0, wall_width/2, 0)
        point2 = door.Location.Point + DB.XYZ(door_width/2, 0, 0) + DB.XYZ(0, wall_width/2, 0)
        point3 = door.Location.Point + DB.XYZ(door_width/2, 0, 0) - DB.XYZ(0, wall_width/2, 0)
        point4 = door.Location.Point - DB.XYZ(door_width/2, 0, 0) - DB.XYZ(0, wall_width/2, 0)

        rotationTransform = DB.Transform.CreateRotationAtPoint(DB.XYZ.BasisZ, door.Location.Rotation, door.Location.Point);

        line1 = DB.Line.CreateBound(point1, point2).CreateTransformed(rotationTransform);
        line2 = DB.Line.CreateBound(point2, point3).CreateTransformed(rotationTransform);
        line3 = DB.Line.CreateBound(point3, point4).CreateTransformed(rotationTransform);
        line4 = DB.Line.CreateBound(point4, point1).CreateTransformed(rotationTransform);

        # print(line_to_modify.Intersect(line2))
        # print(line_to_modify.Intersect(line4))

        main_line_start_point = line_to_modify.GetEndPoint(0)
        main_line_end_point = line_to_modify.GetEndPoint(1)
        line2_start_point = line2.GetEndPoint(0)
        line2_end_point = line2.GetEndPoint(1)
        line4_start_point = line4.GetEndPoint(0)
        line4_end_point = line4.GetEndPoint(1)
        new_line1 = DB.Line.CreateBound(main_line_start_point, line2_end_point)
        new_line2 = DB.Line.CreateBound(line2_end_point, line2_start_point)
        new_line3 = DB.Line.CreateBound(line2_start_point, line4_end_point)
        new_line4 = DB.Line.CreateBound(line4_end_point, line4_start_point)
        new_line5 = DB.Line.CreateBound(line4_start_point, main_line_end_point)
        curve_array.Append(new_line1)
        curve_array.Append(new_line2)
        curve_array.Append(new_line3)
        curve_array.Append(new_line4)
        curve_array.Append(new_line5)

        return curve_array, line2, line4

    def get_door_width(self, door): # type: (DB.FamilyInstance) -> DB.Double
        door_type = self.doc.GetElement(door.GetTypeId())

        door_width = None
        try:
            width_value = door_type.get_Parameter(DB.BuiltInParameter.FAMILY_WIDTH_PARAM).AsDouble()
            if width_value != 0.0:
                door_width = width_value
        except:
            pass

        if door_width == 0.0 or door_width == None:
            try:                            
                width_value = door_type.get_Parameter(DB.BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM).AsDouble()
                if width_value != 0.0:
                    door_width = width_value
            except:
                pass

        if door_width == 0.0 or door_width == None:
            try:                         
                width_value = door_type.get_Parameter(DB.BuiltInParameter.FURNITURE_WIDTH).AsDouble()
                if width_value != 0.0:
                    door_width = width_value
            except:
                pass

        if door_width == 0.0 or door_width == None:
            try:                         
                width_value = door_type.get_Parameter(DB.BuiltInParameter.DOOR_WIDTH).AsDouble()
                if width_value != 0.0:
                    door_width = width_value
            except:
                pass
        if door_width == 0.0 or door_width == None:
            try:                         
                width_value = door_type.get_Parameter(DB.BuiltInParameter.CASEWORK_WIDTH).AsDouble()
                if width_value != 0.0:
                    door_width = width_value
            except:
                pass
        if door_width == 0.0 or door_width == None:
            try:                         
                width_value = door_type.get_Parameter(DB.BuiltInParameter.GENERIC_WIDTH).AsDouble()
                if width_value != 0.0:
                    door_width = width_value
            except:
                pass
        
        if door_width == 0.0 or door_width == None:
            raise ValueError("Coudn't get door width. Build in parameters 'Width' and 'Rough Width' are 0.0")
        
        return door_width

    def generate_floor_outline(self):
        """
        Makes a floor outline with door notches
        """
        main_array = DB.CurveArray()
        phase = list(self.doc.Phases)[-1]
        for room_boundary in self.outer_boundaries:
            boundary_elem = self.doc.GetElement(room_boundary.ElementId)
            main_line = room_boundary.GetCurve()
            if boundary_elem.Category.Id.IntegerValue in ID_WALLS:
                wall_width = self.doc.GetElement(boundary_elem.GetTypeId())\
                    .get_Parameter(DB.BuiltInParameter.WALL_ATTR_WIDTH_PARAM).AsDouble()
                dependent_doors = boundary_elem.\
                    GetDependentElements(DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Doors))
                if dependent_doors.Count == 0:
                    main_array.Append(room_boundary.GetCurve())
                elif dependent_doors.Count >= 1:
                    ordered_doors = self.order_doors_by_proximity(main_line, dependent_doors)
                    dependent_doors = ordered_doors
                    ca = DB.CurveArray()
                    ca.Append(main_line)
                    for door in (dependent_doors):
                        door = self.doc.GetElement(door)
                        door_width = self.get_door_width(door)

                        if (door.FromRoom[phase] != None and door.FromRoom[phase].Id == self.rvt_room_elem.Id):

                            ca2, line2, line4 = self.add_full_door_notch(ca,
                                                    door,
                                                    door_width,
                                                    wall_width)
                            if main_line.Intersect(line2) == DB.SetComparisonResult.Overlap \
                                and main_line.Intersect(line4) == DB.SetComparisonResult.Overlap:
                                ca = ca2
                            else:
                                ca = ca
                        elif (door.ToRoom[phase] != None and door.ToRoom[phase].Id == self.rvt_room_elem.Id):
                            pass
                    for curve in ca:
                        main_array.Append(curve)
                else:
                    main_array.Append(room_boundary.GetCurve())
            else:
                main_array.Append(room_boundary.GetCurve())
        return main_array

class FinishingTool(object):
    """
    FinishingTool class is a tool for creating finishing elements in Revit.
    """
    def __init__(self, uiapp):
        self.uiapp = uiapp                          # type: DB.UIApplication
        self.uidoc = uiapp.ActiveUIDocument         # type: DB.UIDocument
        self.doc = uiapp.ActiveUIDocument.Document  # type: DB.Document
        self.app = uiapp.Application                # type: DB.Application
        self.notifications = []

    def get_rooms(self):
        # select rooms
        selobject = get_selection_basic(self.uidoc, CustomISelectionFilterByIdInclude(ID_ROOMS))
        selected_rooms = [self.doc.GetElement(sel) for sel in selobject
                          if (self.doc.GetElement(sel).Category.Id.IntegerValue in ID_ROOMS)]
        if not selected_rooms:
            forms.alert('Please select room', 'Create floor finishing')
            sys.exit()
        return selected_rooms

    def pick_finishing_type_id(self, build_in_category, switches_options=None):
        """
        Using pyRevit ui to promt user to select finishing type and initial switches
        """
        finishing_type = UPC.collect_build_in_types(self.doc, build_in_category)
        if build_in_category == DB.BuiltInCategory.OST_Walls:
            finishing_type = [i for i in finishing_type if i.Kind.ToString() == "Basic"]
        finishing_type_options = [i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()\
                                                            for i in finishing_type]
        res = dict(zip(finishing_type_options, finishing_type))
        for key in finishing_type:
            res[key] = key.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
        switches = ['Consider Thickness'] if switches_options == None else switches_options
        cfgs = {'option1': { 'background': '0xFF55FF'}}
        rops, rswitches = forms.CommandSwitchWindow.show(finishing_type_options,
                                                         message='Select Option',
                                                         switches=switches,
                                                         config=cfgs)
        if rops == None:
            sys.exit()
        return res[rops], rswitches

    def duplicate_wall_type(self, type_of_wall):
        """
        Duplicating wall type creating the same layer set with double width
        to deal with the offset API issue
        """
        duplicated_wall_type = type_of_wall.Duplicate(str(uuid.uuid4()))
        cs1 = duplicated_wall_type.GetCompoundStructure()
        layers1 = cs1.GetLayers()
        for layer in layers1:
            cs1.SetLayerWidth(layer.LayerId, 2*cs1.GetLayerWidth(layer.LayerId))
        duplicated_wall_type.SetCompoundStructure(cs1)
        return duplicated_wall_type

    def create_floors(self):
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]
        switches = ['Consider Thickness', 'Include Door Notches']
        floor_type, rswitches = self.pick_finishing_type_id(DB.BuiltInCategory.OST_Floors,
                                                            switches)

        with WrappedTransactionGroup(self.doc, 'Create Floor'):
            for room in selected_rooms:
                # Create floor
                with WrappedTransaction(self.doc, 'Create Floor'):
                    new_floor = room.make_finishing_floor(floor_type,
                                                          rswitches,
                                                          self.app)

                # Create floor opening if needed
                if room.boundary_count > 1:
                    with WrappedTransaction(self.doc, 'Create Opening(s)'):
                        room.make_openings(new_floor)

    def create_walls(self):
        # Select rooms 
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]
        switches = ['Inside loops finishing', 'Include Room Separation Lines']
        wall_type, rswitches = self.pick_finishing_type_id(DB.BuiltInCategory.OST_Walls,
                                                           switches)

        with WrappedTransactionGroup(self.doc, 'Make wall finishings'):
            
            with WrappedTransaction(self.doc, 'Create Temp Type'):
                tmp = self.duplicate_wall_type(wall_type)

            with WrappedTransaction(self.doc, 'Create Finishing Walls', warning_suppressor=True):
                for room in selected_rooms: 
                    room.make_finishing_walls_outer(tmp, rswitches)
                    if rswitches['Inside loops finishing'] == True:
                        room.make_finishing_walls_inner(tmp, rswitches)

            new_walls_ids = List[DB.ElementId]([i.Id for i in room.new_walls])
            with WrappedTransaction(self.doc, 'Change type back to original'):
                DB.Element.ChangeTypeId(self.doc, new_walls_ids, wall_type.Id)

            with WrappedTransaction(self.doc, 'Join finishing Walls with hosts', warning_suppressor=True):
                for i, y in zip(room.new_walls, room.boundwalls):
                    try:
                        DB.JoinGeometryUtils.JoinGeometry(self.doc, i, y)
                    except Exception as e:
                        pass
            
            with WrappedTransaction(self.doc, "Join finishing Walls with it's next host", warning_suppressor=True):
                i = 0
                while i < len(room.new_walls):
                    try:
                        DB.JoinGeometryUtils.JoinGeometry(self.doc, room.new_walls[i], room.boundwalls[i+1])
                    except Exception as e:
                        pass
                    i += 1

            with WrappedTransaction(self.doc, 'Delete Temp Type'):
                self.doc.Delete(tmp.Id)

    def create_ceilings(self):
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]

        ### Make ceiling finishing using ceiling category (newer versions)
        if int(self.app.VersionNumber) > 2021 :
            ceiling_type, rswitches = self.pick_finishing_type_id(DB.BuiltInCategory.OST_Ceilings)
            with WrappedTransactionGroup(self.doc, 'Create Ceiling'):
                for room in selected_rooms:
                    # Create ceiling
                    with WrappedTransaction(self.doc, 'Create Ceiling'):
                        new_ceiling = room.make_finishing_ceiling(ceiling_type, rswitches)
                    #Create floor opening if needed
                    if room.boundary_count > 1:
                        with WrappedTransaction(self.doc, 'Create Opening(s)'):
                            room.make_openings(new_ceiling)

        ### Make Ceiling using floor category (older versions)
        elif int(self.app.VersionNumber) <= 2021:
            ceiling_type, rswitches = self.pick_finishing_type_id(DB.BuiltInCategory.OST_Floors)
            with WrappedTransactionGroup(self.doc, 'Create Floor'):
                for room in selected_rooms:
                    # Create floor
                    with WrappedTransaction(self.doc, 'Create Floor'):
                        new_floor = room.make_finishing_floor(ceiling_type, rswitches, self.app, mode="ceiling")

                    # Create floor opening if needed
                    if room.boundary_count > 1:
                        with WrappedTransaction(self.doc, 'Create Opening(s)'):
                            room.make_openings(new_floor)
