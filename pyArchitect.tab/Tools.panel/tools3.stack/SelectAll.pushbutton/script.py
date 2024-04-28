# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import *
import clr
clr.AddReference("System")
from System.Collections.Generic import List
import pyrevit
from pyrevit import forms
from core.catlistenum import get_catlist
import sys

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

ops = ['Air Terminal','Areas','Assemblies','Cable Tray Fitting','Cable Tray Runs','Cable Trays','Casework','Ceilings',
'Columns','CommunicationDevices','Conduit Fittings','Conduit Runs','Conduits','Curtain Panels','Curtain Systems',
'Curtain Wall Mullions','Data Devices','Doors','Duct Accessories','Duct Fittings','Duct Insulations','Duct Fittings',
'Duct Linings','Duct Placeholders','Duct Systems','Ducts','Electrical Equipment','Electrical Fixtures','Entourage',
'Fire Alarm Device Tags','Flex Ducts','Flex Pipes','Floors','Furniture','Furniture Systems','Generic Models','Grids',
'HVAC Zones','Levels','Lighting Devices','Lighting Fixtures','Lines','Mass','Mechanical Equipment','Model Groups',
'Nurse Call Devices','Parking','Parts','Pipe Accessories','Pipe Fittings','Pipe Insulations','Pipe Placeholders','Pipes',
'Piping Systems','Planting','Plumbing Fixtures','RVT Links','Railings','Ramps','Roads','Roofs','Rooms','Security Devices',
'Shaft Openings','Site','Spaces','Specialty Equipment','Sprinklers','Stairs','Structural Area Reinforcement',
'Structural Beam Systems','Structural Columns','Structural Connections','Structural Foundations','Structural Framing',
'Structural Path Reinforcement','Structural Rebar','Structural Rebar Couplers','Structural Stiffeners','Structural Trusses',
'Switch System','Telephone Devices','Topography','Views','Walls','Windows','Wires'
]

choose = forms.CommandSwitchWindow.show(ops, message='Select Option')

catlist = get_catlist(doc)

elements = []
try :
	elements = catlist[choose].WhereElementIsNotElementType().ToElements() 
except:
	sys.exit()
	# forms.alert("There are No elements of the choosen category in project!")
	
elid = [el.Id for el in elements]
uidoc.Selection.SetElementIds(List[ElementId](elid))