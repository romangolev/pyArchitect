# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

__doc__ = """Select all element of desired category / Выбирает все элементы заданной категории на виде
-----------------------------------
Simply run the script and choose the category / Запустить и выбрать категорию
"""
__author__ = 'Roman Golev'
__title__ = "All Elements\nOf Category"


import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import *
import clr
clr.AddReference("System")
from System.Collections.Generic import List
import pyrevit
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

ops = ['Air Terminal','Areas','Assemblies','Cable Tray Fitting','Cable Tray Runs','Cable Trays','Casework','Ceilings',
'Columns','CommunicationDevices','Conduit Fittings','Conduit Runs','Conduits','Curtain Panels','Curtain Systems',
'Curtain Wall Mullions','Data Devices','Doors','Duct Accessories','Duct Fittings','Duct Insulations','Duct Fittings',
'Duct Linings','Duct Placeholders','Duct Systems','Ducts','Electrical Equipment','Electrical Fixtures','Entourage',
'Fire Alarm Device Tags','Flex Ducts','Flex Pipes','Floors','Furniture','Furniture Systems','Generic Models','Grids',
'HVAC Zones','Levels','Lighting Devices','Lighting Fixtures','Lines','Mass','Mechanical Equipment','Model Groups',
'Nurse Call Devices','Parking','Parts','Pipe Accessories','Pipe Fittings','Pipe Insulations','Pipe Placeholders','Pipes',
'Piping Systems','Planting','Plumbing Fixtures','RVT Links','Railings','Ramps','Roads','Roofs','Rooms','Security Devices',
'Shaft Openings','Site','Spaces','Specialty Equipment','Sprinklers','Stairs','Structural Area Reinforcement',
'Structural Beam Systems','Structural Columns','Structural Connections','Structural Foundations','Structural Framing',
'Structural Path Reinforcement','Structural Rebar','Structural Rebar Couplers','Structural Stiffeners','Structural Trusses',
'Switch System','Telephone Devices','Topography','Views','Walls','Windows','Wires'
]

choose = forms.CommandSwitchWindow.show(ops, message='Select Option')

catlist = {
	'Air Terminal':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctTerminal),
	'Areas':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Areas),
	'Assemblies':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Assemblies),
	'Cable Tray Fitting':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CableTrayFitting),
	'Cable Tray Runs':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CableTrayRun),
	'Cable Trays':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CableTray),
	'Casework':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Casework),
	'Ceilings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Ceilings),
	'Columns':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Columns),
	'CommunicationDevices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CommunicationDevices),
	'Conduit Fittings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_ConduitFitting),
	'Conduit Runs':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_ConduitRun),
	'Conduits':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Conduit),
	'Curtain Panels':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CurtainWallPanels),
	'Curtain Systems':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CurtaSystem),
	'Curtain Wall Mullions':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_CurtainWallMullions),
	'Data Devices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DataDevices),
	'Doors':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Doors),
	'Duct Accessories':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctAccessory),
	'Duct Fittings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctFitting),
	'Duct Insulations':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctInsulations),
	'Duct Fittings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctFitting),
	'Duct Linings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctLinings),
	'Duct Placeholders':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PlaceHolderDucts),
	'Duct Systems':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctSystem),
	'Ducts':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_DuctCurves),
	'Electrical Equipment':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_ElectricalEquipment),
	'Electrical Fixtures':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_ElectricalFixtures),
	'Entourage':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Entourage),
	'Fire Alarm Device Tags':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_FireAlarmDeviceTags),
	'Flex Ducts':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_FlexDuctCurves),
	'Flex Pipes':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_FlexPipeCurves),
	'Floors':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Floors),
	'Furniture':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Furniture),
	'Furniture Systems':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_FurnitureSystems),
	'Generic Models':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_GenericModel),
	'Grids':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Grids),
	'HVAC Zones':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_HVAC_Zones),
	'Levels':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Levels),
	'Lighting Devices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_LightingDevices),
	'Lighting Fixtures':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_LightingFixtures),
	'Lines':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Lines),	
	'Mass':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Mass),
	'Mechanical Equipment':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_MechanicalEquipment),
	'Model Groups':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_IOSModelGroups),
	'Nurse Call Devices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_NurseCallDevices),
	'Parking':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Parking),
	'Parts':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Parts),
	'Pipe Accessories':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeAccessory),
	'Pipe Fittings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeFitting),
	'Pipe Insulations':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeInsulations),
	'Pipe Placeholders':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PlaceHolderPipes),
	'Pipes':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipeCurves),
	'Piping Systems':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PipingSystem),
	'Planting':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Planting),
	'Plumbing Fixtures':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PlumbingFixtures),
	'RVT Links':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_RvtLinks),
	'Railings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StairsRailing),
	'Ramps':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Ramps),
	'Roads':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Roads),
	'Roofs':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Roofs),
	'Rooms':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rooms),
	'Security Devices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_SecurityDevices),
	'Shaft Openings':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_ShaftOpening),
	'Site':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Site),
	'Spaces':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_MEPSpaces),
	'Specialty Equipment':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_SpecialityEquipment),
	'Sprinklers':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Sprinklers),
	'Stairs':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Stairs),
	'Structural Area Reinforcement':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_AreaRein),
	'Structural Beam Systems':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralFramingSystem),
	'Structural Columns':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns),
	'Structural Connections':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructConnections),
	'Structural Foundations':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralFoundation),
	'Structural Framing':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralFraming),
	'Structural Path Reinforcement':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_PathRein),
	'Structural Rebar':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Rebar),
	'Structural Rebar Couplers':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Coupler),
	'Structural Stiffeners':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralStiffener),
	'Structural Trusses':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralTruss),
	'Switch System':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_SwitchSystem),
	'Telephone Devices':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_TelephoneDevices),
	'Topography':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Topography),
	'Views':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Views),
	'Walls':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls),
	'Windows':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Windows),
	'Wires':DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Wire)
}

elements = []
try :
	elements = catlist[choose].WhereElementIsNotElementType().ToElements() 
except:
	forms.alert("There are No elements of the choosen category in project!")
	
elid = [el.Id for el in elements]
uidoc.Selection.SetElementIds(List[ElementId](elid))