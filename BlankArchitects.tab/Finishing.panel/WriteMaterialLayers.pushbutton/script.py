# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = 'Записывает состав слоёв стены в параметр типа. / Writes down the information about Wall layers inside type.'
__author__ = 'Roman Golev'
__title__ = "Wall\nLayers"

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit import DB
import clr
clr.AddReference("System")
from collections import namedtuple
import rpw
from rpw import db
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

types = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Walls).WhereElementIsElementType()
WallTypeInfo = namedtuple('WallTypeInfo',['t_walltype','t_layerid','t_materialid'])
wallinfoall = []
for type in types:
    if type.ToString() == "Autodesk.Revit.DB.WallType" and type.Kind.ToString() == "Basic":
        try:
            layers = type.GetCompoundStructure().GetLayers()
            layerid, materialid = [],[]
            for layer in layers:
                layerid.append(layer.LayerId)
                materialid.append(layer.MaterialId)
            wallinfo = WallTypeInfo(type, layerid, materialid)
            wallinfoall.append(wallinfo)
        except:
            pass
    else:
        pass

def add_data(m_WallTypeInfo):
    n = 1
    matt = ''
    for mat in m_WallTypeInfo.t_materialid:
        m = doc.GetElement(mat).get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
        matt += str(n) + '.' + m + "\r\n"
        n = n + 1 
    db.Element(m_WallTypeInfo.t_walltype).parameters['BA_AI_WallStructure'].value = matt

with db.Transaction('Add Data'):
    for wallinfo in wallinfoall:
        add_data(wallinfo)
    forms.alert('Operation completed')