# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """ Базовая информация о проекте и плагине / Basic Information about current project and plug-in"""
__title__ = "BA Инфо"
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
              '<p style="text-align:center;">version 0.1.2</p>')

#name = pyrevit._HostApplication.username()
print('Имя пользователя: {}'.format(revit.username))
#print(revit.doc)
#print(revit.app)
#print(revit.docs)
#