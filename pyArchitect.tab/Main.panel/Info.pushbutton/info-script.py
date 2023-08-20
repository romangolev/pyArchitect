# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

# Imports
from pyrevit import HOST_APP
from Autodesk.Revit.ApplicationServices import LanguageType
from pyrevit import script
from pyrevit import output
import os.path as op
import core

# Handling button
__doc__ = """Информация о проекте, программе и расширении / Basic Information about current project and extension"""
__title__ = "Info"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

# Handle Language versions
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
dir_path = op.dirname(op.realpath(__file__))
style = 'img {max-width: 589px; padding: 25px 0} span {display: block; text-align: center;}'
output.get_output().add_style(style)
output.get_output().set_width(500)
output.get_output().set_height(500)
output.get_output().center()
out = script.get_output()
out.print_html('<h1 style="text-align:center;"> pyArchitect Extension Tools for pyRevit</h1>')

print(str(user) + ' : {}'.format(HOST_APP.username))
print(str(Rvers) + ' : {}'.format(HOST_APP.version_name + HOST_APP.build))
print(str(Rvers) + ' : {}'.format(HOST_APP.subversion))
print(str(Bvers) + ' : {}'.format(core.get_local_version()))

out.print_html('<a href="https://github.com/romangolev/pyArchitect">pyArchitect repository</a>')
out.print_html('<a href="https://www.romangolev.com">Roman Golev</a>')