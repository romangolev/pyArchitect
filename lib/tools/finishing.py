# -*- coding: utf-8 -*-
import sys
from collections import OrderedDict
from contextlib import contextmanager
import Autodesk.Revit.DB as DB
from pyrevit import forms
from System.Collections.Generic import List, Dictionary
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from core.selectionhelpers import (
    get_selection_basic,
    CustomISelectionFilterByIdInclude,
    ID_ROOMS,
    ID_WALLS,
    ID_COLUMNS,
    ID_STRUCTURAL_COLUMNS,
    ID_SEPARATION_LINES,
)
from core.collectror import UniversalProjectCollector as UPC


class FinishingRoom(object):
    def __init__(self, rvt_room_elem):
        self.rvt_room_elem = rvt_room_elem
        self.doc = rvt_room_elem.Document
        self.new_walls = []
        self.new_walls_and_hosts = {}
        self.new_walls_and_corner_hosts = {}

    @property
    def id(self):
        return self.rvt_room_elem.Id

    @property
    def level_id(self):
        return self.rvt_room_elem.Level.Id

    @property
    def room_number(self):
        return self.rvt_room_elem.get_Parameter(
            DB.BuiltInParameter.ROOM_NUMBER
        ).AsString()

    @property
    def room_name(self):
        return self.rvt_room_elem.get_Parameter(
            DB.BuiltInParameter.ROOM_NAME
        ).AsString()

    @property
    def boundaries(self):
        return self.rvt_room_elem.GetBoundarySegments(
            DB.SpatialElementBoundaryOptions()
        )

    @property
    def outer_boundaries(self):
        return self.boundaries[0]

    @property
    def inner_boundaries(self):
        return self.boundaries[1:]

    @property
    def boundary_count(self):
        return len(self.boundaries)

    def make_finishing_floor(
        self, floor_type, rswitches, app, mode="default", room_parameter=None
    ):
        room = self.rvt_room_elem
        room_offset1 = room.get_Parameter(
            DB.BuiltInParameter.ROOM_LOWER_OFFSET
        ).AsDouble()
        room_offset2 = room.get_Parameter(
            DB.BuiltInParameter.ROOM_UPPER_OFFSET
        ).AsDouble()
        level = self.doc.GetElement(self.level_id)

        if int(app.VersionNumber) <= 2022:
            if rswitches["Include Door Notches"] == False:
                floor_curves = DB.CurveArray()
                for boundary_segment in self.outer_boundaries:
                    floor_curves.Append((boundary_segment).GetCurve())

            elif rswitches["Include Door Notches"] == True:
                floor_curves = self.generate_floor_outline()

            new_floor = self.doc.Create.NewFloor(
                floor_curves, floor_type, level, False, DB.XYZ.BasisZ
            )

        elif int(app.VersionNumber) > 2022:
            if rswitches["Include Door Notches"] == False:
                floor_curves_loop = DB.CurveLoop()
                floor_curves = List[DB.Curve]()
                for boundary_segment in self.outer_boundaries:
                    floor_curves.Add((boundary_segment).GetCurve())
                floor_curves_loop = DB.CurveLoop.Create(floor_curves)
                curve_list = List[DB.CurveLoop]()
                curve_list.Add(floor_curves_loop)
            elif rswitches["Include Door Notches"] == True:
                floor_curves_loop = DB.CurveLoop()
                floor_curves = List[DB.Curve]()
                main_array = self.generate_floor_outline()
                for boundary_segment in main_array:
                    floor_curves.Add(boundary_segment)
                floor_curves_loop = DB.CurveLoop.Create(floor_curves)
                curve_list = List[DB.CurveLoop]()
                curve_list.Add(floor_curves_loop)

            new_floor = DB.Floor.Create(self.doc, curve_list, floor_type.Id, level.Id)

        if rswitches["Consider Thickness"] == False:
            offset2 = floor_type.get_Parameter(
                DB.BuiltInParameter.FLOOR_ATTR_DEFAULT_THICKNESS_PARAM
            ).AsDouble()
            new_floor.get_Parameter(
                DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM
            ).Set(
                room_offset1 + offset2 if mode == "default" else room_offset2 + offset2
            )
        if rswitches["Consider Thickness"] == True:
            new_floor.get_Parameter(
                DB.BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM
            ).Set(room_offset1 if mode == "default" else room_offset2)

        param_value = (
            "Floor Finishing : " + "Room {}".format(self.room_number)
            if mode == "default"
            else "Ceiling Finishing : " + "Room {}".format(self.room_number)
        )
        new_floor.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(
            param_value
        )
        self.set_room_parameter(new_floor, room_parameter)
        return new_floor

    def do_we_need_to_make_wall(self, bound, rswitches):
        try:
            condition1 = (
                self.doc.GetElement(bound.ElementId).Category.Id.ToString()
                == str(ID_WALLS[0])
                and self.doc.GetElement(bound.ElementId).WallType.Kind.ToString()
                == "Basic"
            )
        except:
            condition1 = False
        try:
            condition2 = self.doc.GetElement(
                bound.ElementId
            ).Category.Id.ToString() == str(ID_COLUMNS[0]) or self.doc.GetElement(
                bound.ElementId
            ).Category.Id.ToString() == str(ID_STRUCTURAL_COLUMNS[0])
        except:
            condition2 = False
        try:
            condition3 = rswitches[
                "Include Room Separation Lines"
            ] == True and self.doc.GetElement(
                bound.ElementId
            ).Category.Id.ToString() == str(ID_SEPARATION_LINES[0])
        except:
            condition3 = False

        return any([condition1, condition2, condition3])

    def get_host_type_key(self, bound):
        """Return a key that keeps walls separate at different host types."""
        host = self.doc.GetElement(bound.ElementId)
        if host is None or host.Category is None:
            return None
        try:
            type_id = host.GetTypeId().IntegerValue
        except:
            type_id = host.Id.IntegerValue
        return (host.Category.Id.IntegerValue, type_id)

    @staticmethod
    def curves_can_be_merged(first_curve, second_curve):
        """Only merge connected, collinear line segments; arcs stay untouched."""
        if not isinstance(first_curve, DB.Line) or not isinstance(second_curve, DB.Line):
            return False
        tolerance = 1e-6
        if (
            first_curve.GetEndPoint(1).DistanceTo(second_curve.GetEndPoint(0))
            > tolerance
        ):
            return False
        return (
            abs(first_curve.Direction.CrossProduct(second_curve.Direction).Z)
            < tolerance
            and first_curve.Direction.DotProduct(second_curve.Direction) > 0
        )

    def get_merged_boundary_groups(self, boundaries, rswitches):
        """Combine adjacent fragments only when their host category and type match."""
        groups = []
        current = None
        for bound in boundaries:
            curve = bound.GetCurve()
            if (
                curve.Length <= 10 / 304.8
                or not self.do_we_need_to_make_wall(bound, rswitches)
            ):
                current = None
                continue

            host = self.doc.GetElement(bound.ElementId)
            host_key = self.get_host_type_key(bound)
            if (
                current is not None
                and current["host_key"] == host_key
                and self.curves_can_be_merged(current["curve"], curve)
            ):
                current["curve"] = DB.Line.CreateBound(
                    current["curve"].GetEndPoint(0), curve.GetEndPoint(1)
                )
                current["hosts"].append(host)
            else:
                current = {"curve": curve, "host_key": host_key, "hosts": [host]}
                groups.append(current)
        return groups

    @staticmethod
    def offset_into_room(curve, distance):
        """Room boundary loops keep the room on their left side."""
        return curve.CreateOffset(distance, DB.XYZ.BasisZ.Negate())

    @staticmethod
    def intersect_unbound_lines(first, second):
        p, r = first.GetEndPoint(0), first.Direction
        q, s = second.GetEndPoint(0), second.Direction
        denominator = r.X * s.Y - r.Y * s.X
        if abs(denominator) < 1e-9:
            return None
        t = ((q.X - p.X) * s.Y - (q.Y - p.Y) * s.X) / denominator
        return DB.XYZ(p.X + r.X * t, p.Y + r.Y * t, p.Z)

    @staticmethod
    def rebuild_line(line, start, end):
        if start.DistanceTo(end) < 1e-6:
            return None
        rebuilt = DB.Line.CreateBound(start, end)
        if rebuilt.Direction.DotProduct(line.Direction) <= 0:
            return None
        return rebuilt

    def get_finishing_curves(self, boundaries, rswitches, distance):
        """Offset merged groups into the room and make neighbours meet at corners.

        With wall joins at ends allowed, neighbours share an end point and Revit
        joins them. Otherwise the first wall runs through the corner and the
        second one butts into it.
        """
        groups = self.get_merged_boundary_groups(boundaries, rswitches)
        curves = [self.offset_into_room(group["curve"], distance) for group in groups]
        corner_hosts = [[] for _ in groups]
        joins_next = [False for _ in groups]
        count = len(groups)
        for index in range(count):
            following = (index + 1) % count
            if following == index:
                continue
            if (
                groups[index]["curve"].GetEndPoint(1).DistanceTo(
                    groups[following]["curve"].GetEndPoint(0)
                )
                > 1e-6
            ):
                continue
            corner_hosts[index].append(groups[following]["hosts"][0])
            corner_hosts[following].append(groups[index]["hosts"][-1])
            joins_next[index] = True
            first, second = curves[index], curves[following]
            if not isinstance(first, DB.Line) or not isinstance(second, DB.Line):
                continue
            corner = self.intersect_unbound_lines(first, second)
            if corner is None:
                continue
            first_end = second_start = corner
            if rswitches["Allow Wall Joins at Ends"] == False:
                first_end = corner + first.Direction.Multiply(distance)
                second_start = corner + second.Direction.Multiply(distance)
            new_first = self.rebuild_line(first, first.GetEndPoint(0), first_end)
            new_second = self.rebuild_line(second, second_start, second.GetEndPoint(1))
            if new_first is None or new_second is None:
                continue
            curves[index], curves[following] = new_first, new_second
        return [
            (curve, group["hosts"], neighbours, joined)
            for curve, group, neighbours, joined in zip(
                curves, groups, corner_hosts, joins_next
            )
        ]

    def link_corner_walls(self, walls, joins_next, rswitches):
        """Butted corners are not wall-joined, so let the join step clean them up."""
        if rswitches["Allow Wall Joins at Ends"] == True:
            return
        count = len(walls)
        for index in range(count):
            following = walls[(index + 1) % count]
            if not joins_next[index] or walls[index] is None or following is None:
                continue
            if walls[index].Id == following.Id:
                continue
            self.new_walls_and_corner_hosts[walls[index]].append(following)
            self.new_walls_and_corner_hosts[following].append(walls[index])

    @staticmethod
    def get_solids(element):
        solids = []
        geometry = element.get_Geometry(DB.Options())
        if geometry is None:
            return solids
        for item in geometry:
            items = (
                item.GetInstanceGeometry()
                if isinstance(item, DB.GeometryInstance)
                else [item]
            )
            for sub_item in items:
                if isinstance(sub_item, DB.Solid) and sub_item.Volume > 0:
                    solids.append(sub_item)
        return solids

    def shares_face_with(self, element, other, tolerance=1e-4):
        """A face contact puts at least three vertices of element on other."""
        other_faces = [face for solid in self.get_solids(other) for face in solid.Faces]
        vertices = {}
        for solid in self.get_solids(element):
            for edge in solid.Edges:
                for point in edge.Tessellate():
                    key = (round(point.X, 6), round(point.Y, 6), round(point.Z, 6))
                    vertices[key] = point
        touching = 0
        for point in vertices.values():
            for face in other_faces:
                projection = face.Project(point)
                if projection is not None and projection.Distance < tolerance:
                    touching += 1
                    break
        return touching >= 3

    def get_join_hosts(self, new_wall):
        """Own hosts plus perpendicular hosts the wall end actually rests on."""
        hosts = [host for host in self.new_walls_and_hosts[new_wall] if host is not None]
        host_ids = set(host.Id for host in hosts)
        for host in self.new_walls_and_corner_hosts.get(new_wall, []):
            if (
                host is not None
                and host.Id not in host_ids
                and self.shares_face_with(new_wall, host)
            ):
                hosts.append(host)
                host_ids.add(host.Id)
        return hosts

    def make_finishing_walls_outer(self, wall_type, rswitches, room_parameter=None):
        walls, joins_next = [], []
        for curve, hosts, neighbours, joined in self.get_finishing_curves(
            self.outer_boundaries, rswitches, wall_type.Width / 2
        ):
            new_wall = self.make_finishing_wall_by_line(
                curve, wall_type, rswitches, room_parameter
            )
            self.new_walls_and_hosts[new_wall] = hosts
            self.new_walls_and_corner_hosts[new_wall] = list(neighbours)
            self.new_walls.append(new_wall)
            walls.append(new_wall)
            joins_next.append(joined)
        self.link_corner_walls(walls, joins_next, rswitches)

    def make_finishing_walls_inner(self, wall_type, rswitches, room_parameter=None):
        for boundary in self.inner_boundaries:
            walls, joins_next = [], []
            for curve, hosts, neighbours, joined in self.get_finishing_curves(
                boundary, rswitches, wall_type.Width / 2
            ):
                new_wall = None
                try:
                    new_wall = self.make_finishing_wall_by_line(
                        curve, wall_type, rswitches, room_parameter
                    )
                    self.new_walls_and_hosts[new_wall] = hosts
                    self.new_walls_and_corner_hosts[new_wall] = list(neighbours)
                    self.new_walls.append(new_wall)
                except:
                    import traceback

                    print(traceback.format_exc())
                walls.append(new_wall)
                joins_next.append(joined)
            self.link_corner_walls(walls, joins_next, rswitches)

    def make_finishing_wall_by_line(
        self, line, wall_type, rswitches, room_parameter=None
    ):
        room = self.rvt_room_elem
        room_height = room.get_Parameter(DB.BuiltInParameter.ROOM_HEIGHT).AsDouble()
        if room_height > 0:
            wall_height = float(room_height)
        else:
            wall_height = 1500 / 304.8

        new_wall = DB.Wall.Create(
            self.doc, line, wall_type.Id, self.level_id, wall_height, 0.0, False, False
        )
        new_wall.get_Parameter(DB.BuiltInParameter.WALL_KEY_REF_PARAM).Set(2)
        new_wall.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(
            "Wall finishing"
        )
        new_wall.get_Parameter(DB.BuiltInParameter.WALL_ATTR_ROOM_BOUNDING).Set(0)
        if rswitches["Allow Wall Joins at Ends"] == False:
            DB.WallUtils.DisallowWallJoinAtEnd(new_wall, 0)
            DB.WallUtils.DisallowWallJoinAtEnd(new_wall, 1)
        self.set_room_parameter(new_wall, room_parameter)
        return new_wall

    def make_finishing_ceiling(self, ceiling_type, rswitches, room_parameter=None):
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
        new_ceiling = DB.Ceiling.Create(self.doc, curve_list, ceiling_type.Id, level.Id)
        if (
            rswitches["Consider Thickness"] == False
            and ceiling_type.FamilyName == "Compound Ceiling"
        ):
            offset2 = ceiling_type.get_Parameter(
                DB.BuiltInParameter.CEILING_THICKNESS
            ).AsDouble()
            new_ceiling.get_Parameter(
                DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM
            ).Set(room_offset2 + offset2)
        else:
            new_ceiling.get_Parameter(
                DB.BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM
            ).Set(room_offset2)

        new_ceiling.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(
            "Ceiling Finishing"
        )
        self.set_room_parameter(new_ceiling, room_parameter)
        return new_ceiling

    def set_room_parameter(self, element, room_parameter):
        """Write the selected room identity into a writable instance text parameter."""
        if room_parameter is None:
            return
        parameter_name, value_source = room_parameter
        value = self.room_number if value_source == "Room Number" else self.room_name
        for parameter in element.GetParameters(parameter_name):
            if (
                not parameter.IsReadOnly
                and parameter.StorageType == DB.StorageType.String
            ):
                parameter.Set(value or "")
                return

    def make_openings(self, nf):
        co_curves = DB.CurveArray()
        for boundary in self.inner_boundaries:
            for bounds in boundary:
                co_curves.Append(bounds.GetCurve())
        opening = self.doc.Create.NewOpening(nf, co_curves, False)

    def order_doors_by_proximity(self, main_line, doors):
        return sorted(
            doors,
            key=lambda door: self.doc.GetElement(door).Location.Point.DistanceTo(
                main_line.GetEndPoint(0)
            ),
        )

    @staticmethod
    def add_full_door_notch(curve_array, door, door_width, wall_width):
        """
        Modifies wall line by adding full door notch
        """
        if curve_array.Size == 0:
            raise ValueError("Curve array is empty")
        elif curve_array.Size == 1:
            line_to_modify = curve_array[curve_array.Size - 1]
            curve_array = DB.CurveArray()
        else:
            line_to_modify = curve_array[curve_array.Size - 1]
            newcurve_array = DB.CurveArray()
            for i in range(curve_array.Size - 1):
                newcurve_array.Append(curve_array.Item[i])
            curve_array = newcurve_array

        point1 = (
            door.Location.Point
            - DB.XYZ(door_width / 2, 0, 0)
            + DB.XYZ(0, wall_width / 2, 0)
        )
        point2 = (
            door.Location.Point
            + DB.XYZ(door_width / 2, 0, 0)
            + DB.XYZ(0, wall_width / 2, 0)
        )
        point3 = (
            door.Location.Point
            + DB.XYZ(door_width / 2, 0, 0)
            - DB.XYZ(0, wall_width / 2, 0)
        )
        point4 = (
            door.Location.Point
            - DB.XYZ(door_width / 2, 0, 0)
            - DB.XYZ(0, wall_width / 2, 0)
        )

        rotationTransform = DB.Transform.CreateRotationAtPoint(
            DB.XYZ.BasisZ, door.Location.Rotation, door.Location.Point
        )
        line1 = DB.Line.CreateBound(point1, point2).CreateTransformed(rotationTransform)
        line2 = DB.Line.CreateBound(point2, point3).CreateTransformed(rotationTransform)
        line3 = DB.Line.CreateBound(point3, point4).CreateTransformed(rotationTransform)
        line4 = DB.Line.CreateBound(point4, point1).CreateTransformed(rotationTransform)
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

    def get_door_width(self, door):
        door_type = self.doc.GetElement(door.GetTypeId())
        opening_width_parameters = [
            DB.BuiltInParameter.FAMILY_WIDTH_PARAM,
            DB.BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM,
        ]
        fallback_width_parameters = [
            DB.BuiltInParameter.FURNITURE_WIDTH,
            DB.BuiltInParameter.DOOR_WIDTH,
            DB.BuiltInParameter.CASEWORK_WIDTH,
            DB.BuiltInParameter.GENERIC_WIDTH,
        ]
        widths = []
        for element in [door, door_type]:
            for parameter_id in opening_width_parameters:
                try:
                    width = element.get_Parameter(parameter_id).AsDouble()
                    if width > 0.0:
                        widths.append(width)
                except:
                    pass

        # The floor must span the opening: choose the larger of Width and
        # Rough Width. Other standard width parameters support families that
        # do not expose either door-opening parameter.
        if widths:
            return max(widths)

        for element in [door, door_type]:
            for parameter_id in fallback_width_parameters:
                try:
                    width = element.get_Parameter(parameter_id).AsDouble()
                    if width > 0.0:
                        widths.append(width)
                except:
                    pass

        if not widths:
            raise ValueError(
                "Coudn't get door width. Build in parameters 'Width' and 'Rough Width' are 0.0"
            )

        return max(widths)

    def generate_floor_outline(self):
        """
        Makes a floor outline with door notches
        """
        main_array = DB.CurveArray()
        phase = list(self.doc.Phases)[-1]
        for room_boundary in self.outer_boundaries:
            main_line = room_boundary.GetCurve()
            try:
                boundary_elem = self.doc.GetElement(room_boundary.ElementId)
                cat = boundary_elem.Category.Id.IntegerValue
            except:
                cat = None
            try:
                host_type = self.doc.GetElement(boundary_elem.GetTypeId())
            except:
                host_type = None
            try:
                if cat in ID_WALLS and host_type != None:
                    wall_width = (
                        self.doc.GetElement(boundary_elem.GetTypeId())
                        .get_Parameter(DB.BuiltInParameter.WALL_ATTR_WIDTH_PARAM)
                        .AsDouble()
                    )
                    dependent_doors = boundary_elem.GetDependentElements(
                        DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Doors)
                    )
                    if dependent_doors.Count == 0:
                        main_array.Append(room_boundary.GetCurve())
                    elif dependent_doors.Count >= 1:
                        ordered_doors = self.order_doors_by_proximity(
                            main_line, dependent_doors
                        )
                        dependent_doors = ordered_doors
                        ca = DB.CurveArray()
                        ca.Append(main_line)
                        for door in dependent_doors:
                            door = self.doc.GetElement(door)
                            door_width = self.get_door_width(door)

                            if (
                                door.FromRoom[phase] != None
                                and door.FromRoom[phase].Id == self.rvt_room_elem.Id
                            ):
                                ca2, line2, line4 = self.add_full_door_notch(
                                    ca, door, door_width, wall_width
                                )
                                if (
                                    main_line.Intersect(line2)
                                    == DB.SetComparisonResult.Overlap
                                    and main_line.Intersect(line4)
                                    == DB.SetComparisonResult.Overlap
                                ):
                                    ca = ca2
                                else:
                                    ca = ca
                            elif (
                                door.ToRoom[phase] != None
                                and door.ToRoom[phase].Id == self.rvt_room_elem.Id
                            ):
                                pass
                        for curve in ca:
                            main_array.Append(curve)
                    else:
                        main_array.Append(room_boundary.GetCurve())
                else:
                    main_array.Append(room_boundary.GetCurve())
            except:
                main_array.Append(room_boundary.GetCurve())
        return main_array


class FinishingTool(object):
    """
    FinishingTool class is a tool for creating finishing elements in Revit.
    """

    def __init__(self, uiapp):
        self.uiapp = uiapp
        self.uidoc = uiapp.ActiveUIDocument
        self.doc = uiapp.ActiveUIDocument.Document
        self.app = uiapp.Application
        self.notifications = []

    def get_rooms(self):
        selobject = get_selection_basic(
            self.uidoc, CustomISelectionFilterByIdInclude(ID_ROOMS)
        )
        selected_rooms = [
            self.doc.GetElement(sel)
            for sel in selobject
            if (self.doc.GetElement(sel).Category.Id.IntegerValue in ID_ROOMS)
        ]
        if not selected_rooms:
            forms.alert("Please select room", "Create floor finishing")
            sys.exit()
        return selected_rooms

    def pick_finishing_type_id(self, build_in_category, switches_options=None):
        """
        Using pyRevit ui to promt user to select finishing type and initial switches
        """
        finishing_type = UPC.collect_build_in_types(self.doc, build_in_category)
        if build_in_category == DB.BuiltInCategory.OST_Walls:
            finishing_type = [i for i in finishing_type if i.Kind.ToString() == "Basic"]
        finishing_type_options = [
            i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            for i in finishing_type
        ]
        res = dict(zip(finishing_type_options, finishing_type))
        for key in finishing_type:
            res[key] = key.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME)
        switches = (
            ["Consider Thickness"] if switches_options == None else switches_options
        )
        cfgs = {"option1": {"background": "0xFF55FF"}}
        rops, rswitches = forms.CommandSwitchWindow.show(
            finishing_type_options,
            message="Select Option",
            switches=switches,
            config=cfgs,
        )
        if rops == None:
            sys.exit()
        return res[rops], rswitches

    @staticmethod
    def is_text_definition(definition):
        try:
            return definition.GetDataType() == DB.SpecTypeId.String.Text
        except AttributeError:
            return definition.ParameterType == DB.ParameterType.Text

    def get_bound_text_parameter_names(self, build_in_category):
        category = DB.Category.GetCategory(self.doc, build_in_category)
        names = []
        if category is None:
            return names
        iterator = self.doc.ParameterBindings.ForwardIterator()
        while iterator.MoveNext():
            binding = iterator.Current
            if not isinstance(binding, DB.InstanceBinding):
                continue
            if not binding.Categories.Contains(category):
                continue
            if self.is_text_definition(iterator.Key):
                names.append(iterator.Key.Name)
        return names

    def get_writable_text_parameter_names(self, build_in_category):
        """Return text instance parameters available to the requested category."""
        parameter_names = [
            DB.LabelUtils.GetLabelFor(DB.BuiltInParameter.ALL_MODEL_MARK),
            DB.LabelUtils.GetLabelFor(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS),
        ]
        parameter_names.extend(self.get_bound_text_parameter_names(build_in_category))
        element = (
            DB.FilteredElementCollector(self.doc)
            .OfCategory(build_in_category)
            .WhereElementIsNotElementType()
            .FirstElement()
        )
        if element is not None:
            for parameter in element.Parameters:
                if (
                    parameter.Definition is not None
                    and not parameter.IsReadOnly
                    and parameter.StorageType == DB.StorageType.String
                ):
                    parameter_names.append(parameter.Definition.Name)
        return sorted(set(parameter_names))

    def pick_room_parameter_assignment(self, build_in_category):
        parameter_names = self.get_writable_text_parameter_names(build_in_category)
        parameter_name = forms.SelectFromList.show(
            parameter_names,
            title="Room parameter assignment",
            button_name="Use parameter",
        )
        if not parameter_name:
            sys.exit()

        value_source = forms.SelectFromList.show(
            ["Room Number", "Room Name"],
            title="Room parameter assignment",
            button_name="Write value",
        )
        if not value_source:
            sys.exit()
        return (parameter_name, value_source)

    @staticmethod
    def is_finishing_wall(element):
        if not isinstance(element, DB.Wall):
            return False
        comments = element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        return comments is not None and comments.AsString() == "Wall finishing"

    @staticmethod
    def set_room_bounding(walls, value):
        for wall in walls:
            parameter = wall.get_Parameter(DB.BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)
            if parameter is not None and not parameter.IsReadOnly:
                parameter.Set(value)

    def get_bounding_finishing_walls(self, rooms):
        walls = {}
        for room in rooms:
            for loop in room.boundaries:
                for segment in loop:
                    element = self.doc.GetElement(segment.ElementId)
                    if self.is_finishing_wall(element):
                        walls[str(element.Id)] = element
        return walls

    def release_finishing_boundaries(self, rooms):
        released = {}
        while True:
            walls = [
                wall
                for key, wall in self.get_bounding_finishing_walls(rooms).items()
                if key not in released
            ]
            if not walls:
                return list(released.values())
            self.set_room_bounding(walls, 0)
            self.doc.Regenerate()
            for wall in walls:
                released[str(wall.Id)] = wall

    @contextmanager
    def finishing_walls_ignored(self, rooms):
        with WrappedTransaction(self.doc, "Ignore wall finishing boundaries"):
            released = self.release_finishing_boundaries(rooms)
        try:
            yield
        finally:
            if released:
                with WrappedTransaction(self.doc, "Restore wall finishing boundaries"):
                    self.set_room_bounding(released, 1)

    def create_floors(self):
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]
        switches = [
            "Consider Thickness",
            "Include Door Notches",
            "Write Room Data to Text Parameter",
        ]
        floor_type, rswitches = self.pick_finishing_type_id(
            DB.BuiltInCategory.OST_Floors, switches
        )
        room_parameter = None
        if rswitches["Write Room Data to Text Parameter"]:
            room_parameter = self.pick_room_parameter_assignment(
                DB.BuiltInCategory.OST_Floors
            )

        with WrappedTransactionGroup(self.doc, "Create Floor"):
            with self.finishing_walls_ignored(selected_rooms):
                for room in selected_rooms:
                    with WrappedTransaction(self.doc, "Create Floor"):
                        new_floor = room.make_finishing_floor(
                            floor_type,
                            rswitches,
                            self.app,
                            room_parameter=room_parameter,
                        )

                    if room.boundary_count > 1:
                        with WrappedTransaction(self.doc, "Create Opening(s)"):
                            room.make_openings(new_floor)

    def create_walls(self):
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]
        switches = OrderedDict(
            [
                ("Inside loops finishing", False),
                ("Include Room Separation Lines", False),
                ("Join Geometry with Host Walls", True),
                ("Allow Wall Joins at Ends", False),
                ("Write Room Data to Text Parameter", False),
            ]
        )
        wall_type, rswitches = self.pick_finishing_type_id(
            DB.BuiltInCategory.OST_Walls, switches
        )
        room_parameter = None
        if rswitches["Write Room Data to Text Parameter"]:
            room_parameter = self.pick_room_parameter_assignment(
                DB.BuiltInCategory.OST_Walls
            )

        with WrappedTransactionGroup(self.doc, "Make wall finishings"):
            with WrappedTransaction(
                self.doc, "Create Finishing Walls", warning_suppressor=True
            ):
                for room in selected_rooms:
                    room.make_finishing_walls_outer(
                        wall_type, rswitches, room_parameter
                    )
                    if rswitches["Inside loops finishing"] == True:
                        room.make_finishing_walls_inner(
                            wall_type, rswitches, room_parameter
                        )

            if rswitches["Join Geometry with Host Walls"]:
                with WrappedTransaction(
                    self.doc, "Join finishing Walls with hosts", warning_suppressor=True
                ):
                    for room in selected_rooms:
                        for new_wall in room.new_walls:
                            for host in room.get_join_hosts(new_wall):
                                try:
                                    if not DB.JoinGeometryUtils.AreElementsJoined(
                                        self.doc, new_wall, host
                                    ):
                                        DB.JoinGeometryUtils.JoinGeometry(
                                            self.doc, new_wall, host
                                        )
                                except Exception:
                                    pass

    def create_ceilings(self):
        selected_rooms = self.get_rooms()
        selected_rooms = [FinishingRoom(room) for room in selected_rooms]

        if int(self.app.VersionNumber) > 2021:
            ceiling_type, rswitches = self.pick_finishing_type_id(
                DB.BuiltInCategory.OST_Ceilings,
                ["Consider Thickness", "Write Room Data to Text Parameter"],
            )
            room_parameter = None
            if rswitches["Write Room Data to Text Parameter"]:
                room_parameter = self.pick_room_parameter_assignment(
                    DB.BuiltInCategory.OST_Ceilings
                )
            with WrappedTransactionGroup(self.doc, "Create Ceiling"):
                with self.finishing_walls_ignored(selected_rooms):
                    for room in selected_rooms:
                        with WrappedTransaction(self.doc, "Create Ceiling"):
                            new_ceiling = room.make_finishing_ceiling(
                                ceiling_type, rswitches, room_parameter
                            )
                        if room.boundary_count > 1:
                            with WrappedTransaction(self.doc, "Create Opening(s)"):
                                room.make_openings(new_ceiling)

        elif int(self.app.VersionNumber) <= 2021:
            ceiling_type, rswitches = self.pick_finishing_type_id(
                DB.BuiltInCategory.OST_Floors,
                ["Consider Thickness", "Write Room Data to Text Parameter"],
            )
            room_parameter = None
            if rswitches["Write Room Data to Text Parameter"]:
                room_parameter = self.pick_room_parameter_assignment(
                    DB.BuiltInCategory.OST_Floors
                )
            with WrappedTransactionGroup(self.doc, "Create Floor"):
                with self.finishing_walls_ignored(selected_rooms):
                    for room in selected_rooms:
                        with WrappedTransaction(self.doc, "Create Floor"):
                            new_floor = room.make_finishing_floor(
                                ceiling_type,
                                rswitches,
                                self.app,
                                mode="ceiling",
                                room_parameter=room_parameter,
                            )

                        if room.boundary_count > 1:
                            with WrappedTransaction(self.doc, "Create Opening(s)"):
                                room.make_openings(new_floor)
