# -*- coding: utf-8 -*-
__title__ = 'Copy Values'
__doc__ = """"""

__helpurl__ = ""

import clr
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Clipboard
#clr.AddReference('IronPython.Wpf')

import pyrevit
from pyrevit import script
from pyrevit import output
from pyrevit import forms
from pyrevit.forms import WPFWindow
import os.path as op
import json
import clr
clr.AddReference('System.Web.Extensions')
from System.Web.Script.Serialization import JavaScriptSerializer
import Autodesk
from System.Windows.Controls import(ComboBox, 
    ComboBoxItem, ListBox, ListBoxItem)
from System.Collections.ObjectModel import *
from System.ComponentModel import *
from System.Windows.Controls import *
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory \
                                ,ElementId, Transaction, BuiltInParameter\
                                ,UnitUtils, DisplayUnitType, ParameterType\
                                , StorageType    

from System.Collections.Generic import *
import collections
import sys

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Transaction(doc)

selobject = uidoc.Selection.GetElementIds()

params1 = []
params_names = []
param_guids = []
param_ids = []

params2 = []
tparams_names = []
param2_ids = []
tparam_guids = []

if selobject.Count == 0:
     pyrevit.forms.alert('Nothing selected')
     sys.exit()
elif selobject.Count != 0:
     for element in selobject:
          el = doc.GetElement(element)
          eltype = doc.GetElement(el.GetTypeId())
          
          try:
               params = el.GetOrderedParameters()
               for param in params:
                    params1.append(param)
                    param_ids.append(param.Id)
                    if param.IsShared == False:
                         params_names.append(param.Definition.Name)
                         param_guids.append('None')
                    elif param.IsShared == True:
                         params_names.append(str(param.Definition.Name) + ' [' +str(param.Definition.Id) + ']')
                         param_guids.append(param.GUID)

          except:
               pass
          
          try:
               tparams = eltype.GetOrderedParameters()
               for tparam in tparams:
                    params2.append(tparam)
                    param2_ids.append(tparam.Id)
                    if tparam.IsShared == False:
                         tparams_names.append(tparam.Definition.Name)
                         tparam_guids.append('None')
                    elif tparam.IsShared == True:
                         tparams_names.append(str(tparam.Definition.Name) + ' [' +str(tparam.Definition.Id) + ']')
                         tparam_guids.append(tparam.GUID)
          except:
               pass

# Instance parameters list
d1 = dict(zip(params_names,range(0,len(params_names),1)))
dictionary1 = collections.OrderedDict(sorted(d1.items()))
# Type parameters list
d2 = dict(zip(tparams_names,range(0,len(tparams_names),1))) # d2.update(d)
dictionary2 = collections.OrderedDict(sorted(d2.items()))
# Merged list
d3 = dict(d1,**d2)
dictionary3 = collections.OrderedDict(sorted(d3.items()))

     # merged_dictionary = merge(d,d2)

def getValueByName(element, param, typeorinstance):
     inst = doc.GetElement(element)
     type = doc.GetElement(inst.GetTypeId())
     if typeorinstance == True:
          val = type.GetParameters(param.Definition.Name)[0]
     else:
          val = inst.GetParameters(param.Definition.Name)[0]
     return val

def getValueByGuid(element, param, typeorinstance):
     inst = doc.GetElement(element)
     type = doc.GetElement(inst.GetTypeId())
     if typeorinstance == True:
          val = type.get_Parameter(param.GUID)
     else:
          val = inst.get_Parameter(param.GUID)
     return val




def execute(i,j,ti,tj):
     t.Start("Copy parameters")
     for sel in selobject:
          element = doc.GetElement(sel)
          eltype = doc.GetElement(element.GetTypeId())
          #Get and Set Value:
          if i.StorageType == Autodesk.Revit.DB.StorageType.Integer:
               try:
                    if i.IsShared == False:
                         val = getValueByName(sel,i,ti).AsInteger()
                    elif i.IsShared == True:
                         val = getValueByGuid(sel,i,ti).AsInteger()
               except: pass

               if j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.Integer :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(val)
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(val)
                    except: pass
               elif j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.Double :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(val)
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(val)
                    except: pass
               elif j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.String :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(str(val))
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(str(val))
                    except: pass


               
          elif i.StorageType == Autodesk.Revit.DB.StorageType.Double:
               try:
                    if i.IsShared == False:
                         val = getValueByName(sel,i,ti).AsDouble()
                    elif i.IsShared == True:
                         val = getValueByGuid(sel,i,ti).AsDouble()
               except: pass

               if j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.Double :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(val)
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(val)

                    except: pass
               elif j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.String :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(str(val))
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(str(val))
                    except: pass
               

          elif i.StorageType == Autodesk.Revit.DB.StorageType.String:
               try:
                    if i.IsShared == False:
                         val = getValueByName(sel,i,ti).AsString()
                    elif i.IsShared == True:
                         val = getValueByGuid(sel,i,ti).AsString()
               except: pass
               if j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.String :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(val)
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(val)
                    except: pass

          elif i.StorageType == Autodesk.Revit.DB.StorageType.ElementId:
               try:
                    if i.IsShared == False:
                         val = getValueByName(sel,i,ti).AsElementId()
                    elif i.IsShared == True:
                         val = getValueByGuid(sel,i,ti).AsElementId()
               except: pass
               if j.IsReadOnly == False and j.StorageType == Autodesk.Revit.DB.StorageType.ElementId :
                    try:
                         if j.IsShared == False:
                              getValueByName(sel,j,tj).Set(val)
                         elif j.IsShared == True:
                              getValueByGuid(sel,j,tj).Set(val)
                    except: pass


          #TODO add support for the same types of storage units
          else:
               t.RollBack()
               pyrevit.forms.alert('Error while copying. Maybe you tried unsupported parameter type!')
               break
          
     t.Commit()



class MyWindow(WPFWindow):
     def __init__(self,xaml_file_name):
          WPFWindow.__init__(self, xaml_file_name)
          self.drop1 = self.FindName('drop1')
          self.drop2 = self.FindName('drop2')
          self.drop1.ItemsSource = dictionary3
          self.drop2.ItemsSource = dictionary3


     def rewrite(self, sender, args):
          selected1 = self.drop1.SelectedItem
          selected2 = self.drop2.SelectedItem

          if dictionary2.get(selected1) != None:
               # print("Type")
               i = params2[dictionary2.get(selected1)]
               if dictionary2.get(selected2) != None:
                    j = params2[dictionary2.get(selected2)]
                    # print("Type")
                    # print("ok")
                    execute(i,j,True,True)
               elif dictionary1.get(selected2) != None:
                    j = params1[dictionary1.get(selected2)]
                    # print("Instance")
                    # print("ok")
                    execute(i,j,True, False)
          elif dictionary1.get(selected2) != None:
               i = params1[dictionary1.get(selected1)]
               # print("Instance")
               if dictionary2.get(selected2) != None:
                    j = params2[dictionary2.get(selected2)]
                    # print("Type")
                    # print("Cannot write date from instance to type")
               elif dictionary1.get(selected2) != None:
                    j = params1[dictionary1.get(selected2)]
                    # print("Instance")
                    # print("ok")
                    execute(i,j,False,False)

MyWindow('ui.xaml').ShowDialog()
