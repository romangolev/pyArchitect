# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


__doc__ = """Записывает состав слоёв стены в параметр типа. / Writes down the information about Wall layers inside type.'

Берёт информацию из типа отделки. Считывает значение 'Type Mark' (Марка типа) и 'Description' (Описание) 
для каждого из материала, который назначен слоям конструкции. Объединяет информацию в многострочный текст и
записывает в параметр BA_AI_Structure
"""
__author__ = 'Roman Golev'
__title__ = "Floor Layers"

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

types = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Floors).WhereElementIsElementType()
FloorTypeInfo = namedtuple('FloorTypeInfo',['t_floortype','t_layerid','t_materialid'])
floorinfoall = []
for type in types:
    if type.ToString() == "Autodesk.Revit.DB.FloorType": # and type.Kind.ToString() == "Basic":
        try:
            layers = type.GetCompoundStructure().GetLayers()
            layerid, materialid = [],[]
            for layer in layers:
                layerid.append(layer.LayerId)
                materialid.append(layer.MaterialId)
        except:
            layerid = []
            materialid = []
        floorinfo = FloorTypeInfo(type, layerid, materialid)
        floorinfoall.append(floorinfo)
    else:
        pass

def add_data(m_FloorTypeInfo):
    n = 1
    #Add TypeMark parameter
    mark = m_FloorTypeInfo.t_floortype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK).AsString()
    matt = str(mark) + '\r\n'
    for mat in m_FloorTypeInfo.t_materialid:
        try:
            m = doc.GetElement(mat).get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
        except:
            m = "No material or description"
        matt += '-  ' + str(m) + "\r\n"
        #matt += str(n) + '.' + m + "\r\n"
        n = n + 1 
    db.Element(m_FloorTypeInfo.t_floortype).parameters['BA_AI_Structure'].value = matt

with db.Transaction('BA_Floor Layers'):
    for floorinfo in floorinfoall:
        add_data(floorinfo)
    forms.alert('Operation completed')