# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """ Базовая информация о проекте и плагине / Basic Information about current project and plug-in"""
__title__ = "BA Инфо"
__author__ = "Roman Golev"
__context__ = 'zero-doc'


import pyrevit
from pyrevit import *
import rpw
from rpw import revit, ui

#name = pyrevit._HostApplication.username()


Info = "Blank Architects Tools for Revit\nversion 0.1.0"


print(Info)
print('Имя пользователя: {}'.format(revit.username))
print(revit.doc)


#import clr
#clr.AddReference('System.Windows.Forms')
#clr.AddReference('IronPython.Wpf')

#from pyrevit import script 
#xamlfile = script.get_bundle_file('ui.xaml')

#import wpf
#from System import Windows

#class MyWindow(Windows.Window):
#    def __init__(self,sender,args):
#            wpf.LoadComponent(self,xamlfile)


#MyWindow().ShowDialog()
