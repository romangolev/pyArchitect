# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

from pyrevit import HOST_APP
from Autodesk.Revit.ApplicationServices import LanguageType
if HOST_APP.language == LanguageType.Russian:
    user = "Имя пользователя"
    Rvers = "Версия Ревит"
    lang = "RU"
else:
    user = "Username"
    Rvers = "Revit Version"
    lang = "EN"

__doc__ = """ Информация о проекте, программе и расширении / Basic Information about current project and plug-in"""
__title__ = "BA Info"
__author__ = "Roman Golev"
__context__ = 'zero-doc'


import pyrevit
from pyrevit import script
from pyrevit import output
import rpw
from rpw import revit, ui
import os

parent = os.path.dirname
svg = parent(__file__) + r"\ba.svg"

style = 'img {max-width: 589px; padding: 25px 0} span {display: block; text-align: center;}'
output.get_output().add_style(style)
output.get_output().set_width(500)
output.get_output().set_height(500)
output.get_output().center()
out = script.get_output()
out.print_image(svg)
out.print_html('<h1 style="text-align:center;">Blank Architects Tools for Revit</h1>' +\
              '<p style="text-align:center;">version 0.1.4</p>')

#name = pyrevit._HostApplication.username()
print(str(user) + ' : {}'.format(revit.username))
print(str(Rvers) + ' : {}'.format(revit.version))
#print(revit.app)
#print(revit.docs)