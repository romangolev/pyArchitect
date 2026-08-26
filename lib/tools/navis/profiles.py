# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import BuiltInCategory


PROFILE_ITEMS = [
    ("УНИВ.", "UNIVERSAL"),
    ("АР", "AR"),
    ("КР", "KR"),
    ("ОВ", "OV"),
    ("ВК", "VK"),
    ("ЭОМ", "EOM"),
    ("CUSTOM", "CUSTOM"),
]


ENGINEERING_COMMON = [
    BuiltInCategory.OST_Entourage,
    BuiltInCategory.OST_FurnitureSystems,
    BuiltInCategory.OST_Planting,
    BuiltInCategory.OST_Doors,
    BuiltInCategory.OST_Windows,
    BuiltInCategory.OST_Stairs,
    BuiltInCategory.OST_Ramps,
    BuiltInCategory.OST_Railings,
    BuiltInCategory.OST_Ceilings,
    BuiltInCategory.OST_Parking,
    BuiltInCategory.OST_Topography,
    BuiltInCategory.OST_CurtainWallMullions,
    BuiltInCategory.OST_CurtainWallPanels,
    BuiltInCategory.OST_Rebar,
    BuiltInCategory.OST_StructuralColumns,
    BuiltInCategory.OST_StructuralFoundation,
    BuiltInCategory.OST_StructuralFraming,
    BuiltInCategory.OST_Roads,
    BuiltInCategory.OST_VibrationManagement,
]

PROFILE_CATEGORIES = {
    "UNIVERSAL": [],
    "AR": [
        BuiltInCategory.OST_DuctCurves,
        BuiltInCategory.OST_FlexDuctCurves,
        BuiltInCategory.OST_PipeCurves,
        BuiltInCategory.OST_FlexPipeCurves,
        BuiltInCategory.OST_CableTray,
        BuiltInCategory.OST_Conduit,
        BuiltInCategory.OST_Wire,
        BuiltInCategory.OST_DuctFitting,
        BuiltInCategory.OST_PipeFitting,
        BuiltInCategory.OST_ConduitFitting,
        BuiltInCategory.OST_CableTrayFitting,
    ],
    "KR": [
        BuiltInCategory.OST_DuctCurves,
        BuiltInCategory.OST_FlexDuctCurves,
        BuiltInCategory.OST_PipeCurves,
        BuiltInCategory.OST_FlexPipeCurves,
        BuiltInCategory.OST_CableTray,
        BuiltInCategory.OST_Conduit,
        BuiltInCategory.OST_Wire,
        BuiltInCategory.OST_DuctFitting,
        BuiltInCategory.OST_PipeFitting,
        BuiltInCategory.OST_ConduitFitting,
        BuiltInCategory.OST_CableTrayFitting,
    ],
    "OV": ENGINEERING_COMMON
    + [
        BuiltInCategory.OST_Walls,
        BuiltInCategory.OST_Columns,
        BuiltInCategory.OST_Floors,
        BuiltInCategory.OST_Roofs,
    ],
    "VK": ENGINEERING_COMMON
    + [
        BuiltInCategory.OST_Walls,
        BuiltInCategory.OST_Columns,
        BuiltInCategory.OST_Floors,
        BuiltInCategory.OST_Roofs,
        BuiltInCategory.OST_DuctCurves,
        BuiltInCategory.OST_FlexDuctCurves,
        BuiltInCategory.OST_DuctFitting,
    ],
    "EOM": ENGINEERING_COMMON
    + [
        BuiltInCategory.OST_Walls,
        BuiltInCategory.OST_Columns,
        BuiltInCategory.OST_Floors,
        BuiltInCategory.OST_Roofs,
        BuiltInCategory.OST_PipeCurves,
        BuiltInCategory.OST_FlexPipeCurves,
        BuiltInCategory.OST_PipeFitting,
    ],
    "CUSTOM": [],
}
