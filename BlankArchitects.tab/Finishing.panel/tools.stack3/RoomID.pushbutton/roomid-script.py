# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects


__doc__ = 'Записывает параметр ID помещения. / Retrieves Room ID and put it into properties.'
__author__ = 'Roman Golev'
__title__ = "Room\nID"


import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import *
import rpw
from rpw import doc, uidoc, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)


#import pyrevit modules
from pyrevit import forms


uidoc = __revit__.ActiveUIDocument
doc = __revit__.ActiveUIDocument.Document

elements = DB.FilteredElementCollector(doc) \
			.OfCategory(DB.BuiltInCategory.OST_Rooms) \
			.WhereElementIsNotElementType() \
			.ToElements()

with db.Transaction('Room ID'):
    try:
        for room in elements:
            db.Element(room).parameters['BA_AI_RoomID'].value = room.Id
    except:
        forms.alert('You need to add shared parameters for BA finishing')