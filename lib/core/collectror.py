import Autodesk.Revit.DB as DB

class UniversalProjectCollector(object):
    def __init__(self, doc):
        self.doc = doc # type: DB.Document
        self.rooms = self.collect_rooms()
        self.floors = self.collect_floors()
        self.walls = self.collect_walls()
        self.ceiling = self.collect_ceiling()
    
    def collect_room_instances(self):
        rooms = []
        for room in DB.FilteredElementCollector(self.doc).OfCategory(DB.BuiltInCategory.OST_Rooms).WhereElementIsNotElementType():
            rooms.append(room)
        return rooms
    
    def collect_floor_types(self):
        floors = []
        for floor in DB.FilteredElementCollector(self.doc).OfCategory(DB.BuiltInCategory.OST_Floors).WhereElementIsNotElementType():
            floors.append(floor)
        return floors
    
    def collect_wall_types(self):
        walls = []
        for wall in DB.FilteredElementCollector(self.doc).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsNotElementType():
            walls.append(wall)
        return walls
    
    def collect_ceiling_types(self):
        ceilings = []
        for ceiling in DB.FilteredElementCollector(self.doc).OfCategory(DB.BuiltInCategory.OST_Ceilings).WhereElementIsNotElementType():
            ceilings.append(ceiling)
        return ceilings