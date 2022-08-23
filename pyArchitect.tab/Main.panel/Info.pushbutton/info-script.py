# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 


from pyrevit import HOST_APP
from Autodesk.Revit.ApplicationServices import LanguageType
if HOST_APP.language == LanguageType.Russian:
    user = "Имя пользователя"
    Rvers = "Версия Ревит"
    Bvers = "Версия расширения"
    lang = "RU"
else:
    user = "Username"
    Rvers = "Revit Version"
    Bvers = "Extension version"
    lang = "EN"

__doc__ = """Информация о проекте, программе и расширении / Basic Information about current project and extension"""
__title__ = "Info"
__author__ = "Roman Golev"
__context__ = 'zero-doc'


import pyrevit
from pyrevit import script
from pyrevit import output
from pyrevit import forms
import rpw
from rpw import revit, ui
import os
import os.path as op

import core

parent = op.dirname
#svg = parent(__file__) + r"\logo.svg"

style = 'img {max-width: 589px; padding: 25px 0} span {display: block; text-align: center;}'
output.get_output().add_style(style)
output.get_output().set_width(500)
output.get_output().set_height(500)
output.get_output().center()
out = script.get_output()
#out.print_image(svg)
out.print_html('<h1 style="text-align:center;"> pyArchitect Extension Tools for pyRevit</h1>')

#name = pyrevit._HostApplication.username()
print(str(user) + ' : {}'.format(revit.username))
print(str(Rvers) + ' : {}'.format(revit.version))
print(str(Rvers) + ' : {}'.format(HOST_APP.subversion))
print(str(Bvers) + ' : {}'.format(core.get_local_version()))
#print(revit.app)
#print(revit.docs)