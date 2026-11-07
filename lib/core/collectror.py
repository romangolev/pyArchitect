import Autodesk.Revit.DB as DB

class UniversalProjectCollector(object):
    @staticmethod
    def collect_build_in_types(doc, build_in_category):
        return DB.FilteredElementCollector(doc) \
                .OfCategory(build_in_category) \
                .WhereElementIsElementType() \
                .ToElements()
