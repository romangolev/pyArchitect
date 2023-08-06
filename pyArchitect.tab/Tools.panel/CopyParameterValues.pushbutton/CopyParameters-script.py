# -*- coding: utf-8 -*-
__title__ = 'Copy Values'
__doc__ = """Copy parameter value from one property to another /
Копирует значения параметра для выбранных элементов из одного свойства в другое
"""
__helpurl__ = ""

import clr
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import Clipboard
#clr.AddReference('IronPython.Wpf')

import pyrevit
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
from Autodesk.Revit.UI.Selection import ObjectType
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory \
                                ,ElementId, Transaction, BuiltInParameter\
                                ,UnitUtils, StorageType, Parameter

from System.Collections.Generic import *
import collections
import sys
from core.selectionhelpers import CustomISelectionFilterByIdExclude, ID_MODEL_ELEMENTS
from core.unitsconverter import convertDouble
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Transaction(doc)


# Get unput: selected by user elements
def get_selection():
     selobject = uidoc.Selection.GetElementIds()
     if selobject.Count == 0:
          try:
               selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilterByIdExclude(ID_MODEL_ELEMENTS), "Selection Objects")
          except:
               sys.exit()
     elif selobject.Count != 0:
          selection = selobject
     return selection


class ManageParameters:
     def __init__(self,selection):
          self.selection = selection

          self.inst_params = list()
          self.type_params = list()

          self.collect_parameters()
          self.inst_dict_raw = dict(zip(self.inst_params,range(0,len(self.inst_params),1)))
          self.type_dict_raw = dict(zip(self.type_params,range(0,len(self.type_params),1)))
          self.compile_from_params()
          self.compile_to_dictionary()

     def collect_parameters(self):
          for element in self.selection:
               el = doc.GetElement(element)
               eltype = doc.GetElement(el.GetTypeId())
               # Collect Instance parameters
               try:
                    params = el.GetOrderedParameters()
                    for param in params:
                         self.inst_params.append(param)
               except:
                    pass
               # Collect Type parameters
               try:
                    tparams = eltype.GetOrderedParameters()
                    for tparam in tparams:
                         self.type_params.append(tparam)
               except:
                    pass


     @property
     def select_from_dictionary(self):
          return self.from_dict


     def compile_from_params(self):
          inst_dict = dict()
          for elem in self.inst_dict_raw.items():
               if elem[0].IsShared == False:
                    inst_dict[elem[0].Definition.Name] = elem[1]
               elif elem[0].IsShared == True:
                    inst_dict[str(str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']')] = elem[1]
          self.inst_dict_names = collections.OrderedDict(inst_dict)

          type_dict = dict()
          for elem in self.type_dict_raw.items():
               if elem[0].IsShared == False:
                    type_dict[elem[0].Definition.Name] = elem[1]
               elif elem[0].IsShared == True:
                    type_dict[str(str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']')] = elem[1]
          self.type_dict_names = collections.OrderedDict(type_dict)

          from_dict_raw = dict(self.inst_dict_names,**self.type_dict_names)
          self.from_dict = collections.OrderedDict(sorted(from_dict_raw.items()))

     @property
     def select_to_dictionary(self):
          return self.to_dict
     
     def compile_to_dictionary(self):
          inst_dict = dict()
          for elem in self.inst_dict_raw.items():
               if elem[0].IsReadOnly == False:
                    if elem[0].IsShared == False:
                         inst_dict[elem[0].Definition.Name] = elem[1]
                    elif elem[0].IsShared == True:
                         inst_dict[str(str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']')] = elem[1]
               else: 
                    pass
          inst_dict_names = collections.OrderedDict(inst_dict)

          type_dict = dict()
          for elem in self.type_dict_raw.items():
               if elem[0].IsReadOnly == False:
                    if elem[0].IsShared == False:
                         type_dict[elem[0].Definition.Name] = elem[1]
                    elif elem[0].IsShared == True:
                         type_dict[str(str(elem[0].Definition.Name) + ' [' + str(elem[0].Definition.Id) + ']')] = elem[1]
               else:
                    pass
          type_dict_names = collections.OrderedDict(type_dict)

          to_dict_raw = dict(inst_dict_names,**type_dict_names)
          self.to_dict = collections.OrderedDict(sorted(to_dict_raw.items()))
     
     @property
     def inst_dict_names(self):
          return self.inst_dict_names
     @property
     def type_dict_names(self):
          return self.type_dict_names    

     @property
     def inst_params(self):
          return self.inst_params
     @property
     def type_params(self):
          return self.type_params


class CopyValues:
     def __init__(self, parameter_from, parameter_to, element_from, element_to):
          self.param_from = parameter_from
          self.param_to = parameter_to
          self.element_from = element_from
          self.element_to = element_to
     
     def getValueFrom(self):
          if self.param_from.IsShared == True:
               val = self.element_from.get_Parameter(self.param_from.GUID)
          elif self.param_from.IsShared == False:
               val =  self.element_from.GetParameters(self.param_from.Definition.Name)[0]
          else:
               return None 
                        
          if self.param_from.StorageType == StorageType.Integer:
               return val.AsInteger(), StorageType.Integer, None
          
          elif self.param_from.StorageType == StorageType.Double:
               # 
               try:
                    value = val.AsDouble(), StorageType.Double, self.param_from.DisplayUnitType
               except:
                    value = val.AsDouble(), StorageType.Double, self.param_from.GetUnitTypeId()
               return value
          elif self.param_from.StorageType == StorageType.String:
               return val.AsString(), StorageType.String, None
          
          elif self.param_from.StorageType == StorageType.ElementId:
               return val.AsElementId(), StorageType.ElementId, None
          
          else:
               pass


     def setValueTo(self, value):
          if self.param_to.IsShared == True:
               self.element_to.get_Parameter(self.param_to.GUID).Set(value)
          elif self.param_to.IsShared == False:
               self.element_to.GetParameters(self.param_to.Definition.Name)[0].Set(value)


     def runLogic(self):
          value, storageTypeFrom, units = self.getValueFrom()

          if storageTypeFrom == StorageType.Integer:
               if self.param_to.StorageType == StorageType.Integer:
                    self.setValueTo(value)
               elif self.param_to.StorageType == StorageType.Double:
                    self.setValueTo(value)
               elif self.param_to.StorageType == StorageType.String:
                    self.setValueTo(str(value))
               elif self.param_to.StorageType == StorageType.ElementId:
                    pyrevit.forms.alert("This type of copying is not supported!")

          elif storageTypeFrom == StorageType.Double:
               if self.param_to.StorageType == StorageType.Integer:
                    value_converted = convertDouble(uiapp, value, units)
                    self.setValueTo(round(value_converted))
               elif self.param_to.StorageType == StorageType.Double:
                    self.setValueTo(value)
               elif self.param_to.StorageType == StorageType.String:
                    value_converted = convertDouble(uiapp, value, units)
                    self.setValueTo(str(value_converted))
               elif self.param_to.StorageType == StorageType.ElementId:
                    pyrevit.forms.alert("This type of copying is not supported!")
               # TODO Double units conversion (add unit conversion helper to the project)
          elif storageTypeFrom == StorageType.String:
               if self.param_to.StorageType == StorageType.Integer:
                    try:
                         self.setValueTo(int(value))
                    except:
                         pass
               elif self.param_to.StorageType == StorageType.Double:
                    try:
                         self.setValueTo(float(value))
                    except:
                         pass
               elif self.param_to.StorageType == StorageType.String:
                    self.setValueTo(value)
               elif self.param_to.StorageType == StorageType.ElementId:
                    pyrevit.forms.alert("This type of copying is not supported!")

          elif storageTypeFrom == StorageType.ElementId:
               if self.param_to.StorageType == StorageType.Integer:
                    pyrevit.forms.alert("This type of copying is not supported!")
               elif self.param_to.StorageType == StorageType.Double:
                    pyrevit.forms.alert("This type of copying is not supported!")
               elif self.param_to.StorageType == StorageType.String:
                    pyrevit.forms.alert("This type of copying is not supported!")
               elif self.param_to.StorageType == StorageType.ElementId:
                    self.setValueTo(value)
                    


class MyWindow(WPFWindow):
     def __init__(self,xaml_file_name):
          WPFWindow.__init__(self, xaml_file_name)
          self.drop1 = self.FindName('drop1')
          self.drop2 = self.FindName('drop2')
          self.drop1.ItemsSource = paraMan.select_from_dictionary
          self.drop2.ItemsSource = paraMan.select_to_dictionary

     def rewrite(self, sender, args):
          selected1 = self.drop1.SelectedItem
          selected2 = self.drop2.SelectedItem

          t.Start("Copy parameters")
          # From parameter is a Type parameter:
          if paraMan.type_dict_names.get(selected1) != None:
               from_parameter = paraMan.type_params[paraMan.type_dict_names.get(selected1)]

               # To parameter is Type parameter:
               if paraMan.type_dict_names.get(selected2) != None:
                    to_parameter = paraMan.type_params[paraMan.type_dict_names.get(selected2)]
                    for elem in selection:
                         copy_result = CopyValues(from_parameter,
                                                  to_parameter,
                                                  doc.GetElement(elem.GetTypeId()),
                                                  doc.GetElement(elem.GetTypeId())).runLogic()

               # To parameter is Instance parameter:
               elif paraMan.inst_dict_names.get(selected2) != None:
                    to_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected2)]
                    for elem in selection:
                         copy_result = CopyValues(from_parameter,
                                                  to_parameter,
                                                  doc.GetElement(elem.GetTypeId()),
                                                  doc.GetElement(elem)).runLogic()
          
          # From parameter is Instance:
          elif paraMan.inst_dict_names.get(selected2) != None:
               from_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected1)]

               # To parameter is Type parameter:
               if paraMan.type_dict_names.get(selected2) != None:
                    to_parameter = paraMan.type_params[paraMan.type_dict_names.get(selected2)]
                    # print("Cannot write date from Instance to Type parameters")
                    pyrevit.forms.alert("Cannot write date from Instance to Type parameters")

               # To parameter is Instance parameter:             
               elif paraMan.inst_dict_names.get(selected2) != None:
                    to_parameter = paraMan.inst_params[paraMan.inst_dict_names.get(selected2)]
                    for elem in selection:
                         copy_result = CopyValues(from_parameter,
                                                  to_parameter,
                                                  doc.GetElement(elem),
                                                  doc.GetElement(elem)).runLogic()
          t.Commit()

if __name__ == '__main__':
     # Get selection
     selection = get_selection()
     # Determine which parameters applicable
     paraMan = ManageParameters(selection)
     # Run dialog window
     MyWindow('ui.xaml').ShowDialog()


#TODO optional report after execution with SHIFT
