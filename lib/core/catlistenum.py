# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

from collections import OrderedDict

import Autodesk.Revit.DB as DB

CATEGORIES = OrderedDict([
    ('Air Terminal', 'OST_DuctTerminal'),
    ('Areas', 'OST_Areas'),
    ('Assemblies', 'OST_Assemblies'),
    ('Cable Tray Fitting', 'OST_CableTrayFitting'),
    ('Cable Tray Runs', 'OST_CableTrayRun'),
    ('Cable Trays', 'OST_CableTray'),
    ('Casework', 'OST_Casework'),
    ('Ceilings', 'OST_Ceilings'),
    ('Columns', 'OST_Columns'),
    ('CommunicationDevices', 'OST_CommunicationDevices'),
    ('Conduit Fittings', 'OST_ConduitFitting'),
    ('Conduit Runs', 'OST_ConduitRun'),
    ('Conduits', 'OST_Conduit'),
    ('Curtain Panels', 'OST_CurtainWallPanels'),
    ('Curtain Systems', 'OST_CurtaSystem'),
    ('Curtain Wall Mullions', 'OST_CurtainWallMullions'),
    ('Data Devices', 'OST_DataDevices'),
    ('Doors', 'OST_Doors'),
    ('Duct Accessories', 'OST_DuctAccessory'),
    ('Duct Fittings', 'OST_DuctFitting'),
    ('Duct Insulations', 'OST_DuctInsulations'),
    ('Duct Linings', 'OST_DuctLinings'),
    ('Duct Placeholders', 'OST_PlaceHolderDucts'),
    ('Duct Systems', 'OST_DuctSystem'),
    ('Ducts', 'OST_DuctCurves'),
    ('Electrical Equipment', 'OST_ElectricalEquipment'),
    ('Electrical Fixtures', 'OST_ElectricalFixtures'),
    ('Entourage', 'OST_Entourage'),
    ('Fire Alarm Device Tags', 'OST_FireAlarmDeviceTags'),
    ('Flex Ducts', 'OST_FlexDuctCurves'),
    ('Flex Pipes', 'OST_FlexPipeCurves'),
    ('Floors', 'OST_Floors'),
    ('Furniture', 'OST_Furniture'),
    ('Furniture Systems', 'OST_FurnitureSystems'),
    ('Generic Models', 'OST_GenericModel'),
    ('Grids', 'OST_Grids'),
    ('HVAC Zones', 'OST_HVAC_Zones'),
    ('Levels', 'OST_Levels'),
    ('Lighting Devices', 'OST_LightingDevices'),
    ('Lighting Fixtures', 'OST_LightingFixtures'),
    ('Lines', 'OST_Lines'),
    ('Mass', 'OST_Mass'),
    ('Mechanical Equipment', 'OST_MechanicalEquipment'),
    ('Model Groups', 'OST_IOSModelGroups'),
    ('Nurse Call Devices', 'OST_NurseCallDevices'),
    ('Parking', 'OST_Parking'),
    ('Parts', 'OST_Parts'),
    ('Pipe Accessories', 'OST_PipeAccessory'),
    ('Pipe Fittings', 'OST_PipeFitting'),
    ('Pipe Insulations', 'OST_PipeInsulations'),
    ('Pipe Placeholders', 'OST_PlaceHolderPipes'),
    ('Pipes', 'OST_PipeCurves'),
    ('Piping Systems', 'OST_PipingSystem'),
    ('Planting', 'OST_Planting'),
    ('Plumbing Fixtures', 'OST_PlumbingFixtures'),
    ('RVT Links', 'OST_RvtLinks'),
    ('Railings', 'OST_StairsRailing'),
    ('Ramps', 'OST_Ramps'),
    ('Roads', 'OST_Roads'),
    ('Roofs', 'OST_Roofs'),
    ('Rooms', 'OST_Rooms'),
    ('Security Devices', 'OST_SecurityDevices'),
    ('Shaft Openings', 'OST_ShaftOpening'),
    ('Site', 'OST_Site'),
    ('Spaces', 'OST_MEPSpaces'),
    ('Specialty Equipment', 'OST_SpecialityEquipment'),
    ('Sprinklers', 'OST_Sprinklers'),
    ('Stairs', 'OST_Stairs'),
    ('Structural Area Reinforcement', 'OST_AreaRein'),
    ('Structural Beam Systems', 'OST_StructuralFramingSystem'),
    ('Structural Columns', 'OST_StructuralColumns'),
    ('Structural Connections', 'OST_StructConnections'),
    ('Structural Foundations', 'OST_StructuralFoundation'),
    ('Structural Framing', 'OST_StructuralFraming'),
    ('Structural Path Reinforcement', 'OST_PathRein'),
    ('Structural Rebar', 'OST_Rebar'),
    ('Structural Rebar Couplers', 'OST_Coupler'),
    ('Structural Stiffeners', 'OST_StructuralStiffener'),
    ('Structural Trusses', 'OST_StructuralTruss'),
    ('Switch System', 'OST_SwitchSystem'),
    ('Telephone Devices', 'OST_TelephoneDevices'),
    ('Topography', 'OST_Topography'),
    ('Views', 'OST_Views'),
    ('Walls', 'OST_Walls'),
    ('Windows', 'OST_Windows'),
    ('Wires', 'OST_Wire'),
])


def category_names():
    """Return the category names offered to the user, in display order."""
    return list(CATEGORIES)


def collect_category(doc, name):
    """Return a collector of the placed elements of the category `name`."""
    category = getattr(DB.BuiltInCategory, CATEGORIES[name])
    return DB.FilteredElementCollector(doc).OfCategory(category)         .WhereElementIsNotElementType()
