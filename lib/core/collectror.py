import Autodesk.Revit.DB as DB

class UniversalProjectCollector(object):
    @staticmethod
    def collect_room_instances(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Rooms) \
                .WhereElementIsNotElementType() \
                .ToElements()

    @staticmethod
    def collect_floor_instances(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Floors) \
                .WhereElementIsNotElementType() \
                .ToElements()

    @staticmethod
    def collect_wall_instances(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Walls) \
                .WhereElementIsNotElementType() \
                .ToElements()

    @staticmethod
    def collect_ceiling_instances(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Ceilings) \
                .WhereElementIsNotElementType() \
                .ToElements()
    
    @staticmethod
    def collect_floor_types(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Floors) \
                .OfClass(DB.FloorType) \
                .ToElements()

    @staticmethod
    def collect_wall_types(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Walls) \
                .OfClass(DB.WallType) \
                .ToElements()

    @staticmethod
    def collect_ceiling_types(doc):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_Ceilings) \
                .OfClass(DB.CeilingType) \
                .ToElements()

    @staticmethod
    def collect_build_in_types(doc, build_in_category):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(build_in_category) \
                .WhereElementIsElementType() \
                .ToElements()
    
    @staticmethod
    def collect_build_in_instances(doc, build_in_category):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(build_in_category) \
                .WhereElementIsNotElementType() \
                .ToElements()