# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import traceback
from tools.finishing import FinishingTool
import sys
import uuid
import Autodesk.Revit
import Autodesk.Revit.DB as DB
from pyrevit import forms
from System.Collections.Generic import List, Dictionary
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from core.selectionhelpers import get_selection_basic, CustomISelectionFilterByIdInclude, ID_ROOMS, ID_WALLS
from core.collectror import UniversalProjectCollector as UPC
import Autodesk.Revit.DB as DB

uiapp = __revit__                      # type: ignore
uidoc = uiapp.ActiveUIDocument         # type: DB.UIDocument
doc = uiapp.ActiveUIDocument.Document  # type: DB.Document
app = uiapp.Application      

def get_rooms():
    # select rooms
    selobject = get_selection_basic(uidoc, CustomISelectionFilterByIdInclude(ID_ROOMS))
    selected_rooms = [doc.GetElement(sel) for sel in selobject
                        if (doc.GetElement(sel).Category.Id.IntegerValue in ID_ROOMS)]
    if not selected_rooms:
        forms.alert('Please select room', 'Create floor finishing')
        sys.exit()
    return selected_rooms

def order_doors_by_proximity(main_line, doors):
    return sorted(doors, key=lambda door: doc.GetElement(door).Location.Point.DistanceTo(main_line.GetEndPoint(0)))

def add_full_door_notch(curve_array, door, door_width, wall_width):
    print(curve_array.Size)
    if curve_array.Size == 0:
        raise ValueError("Curve array is empty")
    elif curve_array.Size == 1:
        line_to_modify = curve_array[curve_array.Size-1]
        curve_array = DB.CurveArray()
    else:
        line_to_modify = curve_array[curve_array.Size-1]
        print("Moving the whole array to a new CurveArray")
        print(curve_array.Size)
        newcurve_array = DB.CurveArray()
        print(newcurve_array.Size)
        for i in range(curve_array.Size-1):
            newcurve_array.Append(curve_array.Item[i])
        print(newcurve_array.Size)
        curve_array = newcurve_array
        print("Moving the whole array to a new CurveArray")

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


def main():
    rooms = get_rooms()
    phase = list(doc.Phases)[-1]
    with WrappedTransaction(doc, "Create floor finishing"):
        for room in rooms:
            sketch = DB.SketchPlane.Create(doc, room.Level.Id)
            room_boundaries = room.GetBoundarySegments(DB.SpatialElementBoundaryOptions())[0]
            for room_boundary in room_boundaries:
                print(room_boundary.GetCurve())
                boundary_elem = doc.GetElement(room_boundary.ElementId)
                main_line = room_boundary.GetCurve()
                if boundary_elem.Category.Id.IntegerValue in ID_WALLS:
                    wall_width = doc.GetElement(boundary_elem.GetTypeId()).get_Parameter(DB.BuiltInParameter.WALL_ATTR_WIDTH_PARAM).AsDouble()
                    dependent_doors = boundary_elem.GetDependentElements(DB.ElementCategoryFilter(DB.BuiltInCategory.OST_Doors))
                    #TODO: if there is more than one door, they need to be ordered by their proximity to the start point of the line
                    if dependent_doors.Count == 0:
                        doc.Create.NewModelCurve(room_boundary.GetCurve(), sketch)
                    elif dependent_doors.Count == 1:
                        door = doc.GetElement(dependent_doors[0])
                        door_width = door.get_Parameter(DB.BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM).AsDouble()
                        
                        if (door.FromRoom[phase] != None and door.FromRoom[phase].Id == room.Id):
                            ca = DB.CurveArray()
                            ca.Append(main_line)
                            ca2, line2, line4 = add_full_door_notch(ca,
                                                      door,
                                                      door_width,
                                                      wall_width)


                            if main_line.Intersect(line2) == DB.SetComparisonResult.Overlap \
                                and main_line.Intersect(line4) == DB.SetComparisonResult.Overlap:
                                doc.Create.NewModelCurveArray(ca2, sketch)
                            else:
                                doc.Create.NewModelCurve(main_line, sketch)
                        elif (door.ToRoom[phase] != None and door.ToRoom[phase].Id == room.Id):
                            doc.Create.NewModelCurve(room_boundary.GetCurve(), sketch)
                            pass
                    elif dependent_doors.Count > 1:
                        
                        ordered_doors = order_doors_by_proximity(main_line, dependent_doors)
                        dependent_doors = ordered_doors

                        print("More than one door")
                        print(dependent_doors.Count)
                        ca = DB.CurveArray()
                        ca.Append(main_line)
                        for door in (dependent_doors):
                            door = doc.GetElement(door)
                            door_width = door.get_Parameter(DB.BuiltInParameter.FAMILY_ROUGH_WIDTH_PARAM).AsDouble()
                            print("----------0----------")
                            if (door.FromRoom[phase] != None and door.FromRoom[phase].Id == room.Id):
                                print("----------1----------")
                                ca2, line2, line4 = add_full_door_notch(ca,
                                                        door,
                                                        door_width,
                                                        wall_width)
                                print("----------2----------")

                                if main_line.Intersect(line2) == DB.SetComparisonResult.Overlap \
                                    and main_line.Intersect(line4) == DB.SetComparisonResult.Overlap:
                                    print("----------3----------")
                                    print(ca2.Size)
                                    ca = ca2
                                else:
                                    ca = ca
                            elif (door.ToRoom[phase] != None and door.ToRoom[phase].Id == room.Id):
                                pass
                        doc.Create.NewModelCurveArray(ca, sketch)
                    else:
                        doc.Create.NewModelCurve(room_boundary.GetCurve(), sketch)
                        pass
                else:
                    doc.Create.NewModelCurve(room_boundary.GetCurve(), sketch)
                    pass


            # print("---------------------")
            # room_bounded_doors = list(set(room_bounded_doors))
            # print(room_bounded_doors)
            # print(set([door.Id for door in room_bounded_doors]))
 




if __name__ == '__main__':
    main()
    # try:
    #     tool_instance = FinishingTool(__revit__) # type: ignore
    #     tool_instance.create_floors()
    # except Exception as e:
    #     print(traceback.format_exc())