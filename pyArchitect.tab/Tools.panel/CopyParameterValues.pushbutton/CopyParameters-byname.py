# -*- coding: utf-8 -*-
__title__ = 'Copy Parameters'
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

from System.Windows.Controls import(ComboBox, 
    ComboBoxItem, ListBox, ListBoxItem)
from System.Collections.ObjectModel import *
from System.ComponentModel import *
from System.Windows.Controls import *
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory \
                                ,ElementId, Transaction, BuiltInParameter\
                                ,UnitUtils, DisplayUnitType, ParameterType

from System.Collections.Generic import *

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Transaction(doc)

selobject = uidoc.Selection.GetElementIds()
params1 = []

if selobject.Count == 0:
     print('Nothing selected')
elif selobject.Count != 0:
     for element in selobject:
          el = doc.GetElement(element)
          try:
               params = el.GetOrderedParameters()
               for param in params:
                    params1.append(param)
          except:
               pass



class MyWindow(WPFWindow):
    def __init__(self,xaml_file_name):
          WPFWindow.__init__(self, xaml_file_name)
          self.drop1 = self.FindName('drop1')
          self.drop2 = self.FindName('drop2')
          self.drop1.ItemsSource = map(lambda x:x.Definition.Name, params)
          self.drop2.ItemsSource = map(lambda x:x.Definition.Name, params)

    def rewrite(self, sender, args):
          selected1 = self.drop1.SelectedItem
          selected4 = self.drop2.SelectedItem


          for i in params:
               if i.Definition.Name == selected1:
                    for sel in selobject:
                         print(doc.GetElement(sel).GetParameters(selected1)[0].Definition.ParameterType)
                         if i.Definition.ParameterType == ParameterType.Text:
                              if doc.GetElement(sel).GetParameters(selected1).Count == 1:
                                   print(doc.GetElement(sel).GetParameters(selected1)[0].AsString())
                                   t.Start("Copy parameters")
                                   for element in selobject:
                                        val = doc.GetElement(element).GetParameters(selected1)[0].AsString()
                                        doc.GetElement(element).GetParameters(selected4)[0].Set(val)
                                   t.Commit()
                              else: 
                                   print("The parameter you choose has a duplicate")
                         else:
                              if doc.GetElement(sel).GetParameters(selected1).Count == 1:
                                   print(doc.GetElement(sel).GetParameters(selected1)[0].AsValueString())
                                   t.Start("Copy parameters")
                                   for element in selobject:
                                        val = doc.GetElement(element).GetParameters(selected1)[0].AsValueString()
                                        doc.GetElement(element).GetParameters(selected4)[0].Set(val)
                                   t.Commit()
                              else: 
                                   print("The parameter you choose has a duplicate")




MyWindow('ui.xaml').ShowDialog()
