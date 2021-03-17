# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Записывает состав слоёв потолка (категорией кровля) в параметр типа. / Writes down the information about Roof layers inside type.

Берёт информацию из типа отделки. Считывает значение 'Type Mark' (Марка типа) и 'Description' (Описание) 
для каждого из материала, который назначен слоям конструкции. Объединяет информацию в многострочный текст и
записывает в параметр BA_AI_Structure
"""
__author__ = 'Roman Golev'
__title__ = "Ceiling Layers"

import Autodesk.Revit.DB
from Autodesk.Revit.DB import *
from Autodesk.Revit import DB
import clr
clr.AddReference("System")
from collections import namedtuple
from rpw import db
from pyrevit import forms

uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

types = Autodesk.Revit.DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_Roofs).WhereElementIsElementType()
RoofTypeInfo = namedtuple('RoofTypeInfo',['t_rooftype','t_layerid','t_materialid'])
roofinfoall = []
for type in types:
    if type.ToString() == "Autodesk.Revit.DB.RoofType": #and type.Kind.ToString() == "Basic":
        try:
            layers = type.GetCompoundStructure().GetLayers()
            layerid, materialid = [],[]
            for layer in layers:
                layerid.append(layer.LayerId)
                materialid.append(layer.MaterialId)
        except:
            layerid = []
            materialid = []
        roofinfo = RoofTypeInfo(type, layerid, materialid)
        roofinfoall.append(roofinfo)
    else:
        pass

def add_data(m_RoofTypeInfo):
    n = 1
    #Add TypeMark parameter
    mark = m_RoofTypeInfo.t_rooftype.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK).AsString()
    matt = str(mark) + '\r\n'
    for mat in m_RoofTypeInfo.t_materialid:
        try:
            m = doc.GetElement(mat).get_Parameter(BuiltInParameter.ALL_MODEL_DESCRIPTION).AsString()
        except:
            m = "No material or description"
        matt += '-  ' + str(m) + "\r\n"
        #matt += str(n) + '.' + m + "\r\n"
        n = n + 1 
    db.Element(m_RoofTypeInfo.t_rooftype).parameters['BA_AI_Structure'].value = matt

with db.Transaction('BA_Roof Layers'):
    for roofinfo in roofinfoall:
        add_data(roofinfo)
    forms.alert('Operation completed')