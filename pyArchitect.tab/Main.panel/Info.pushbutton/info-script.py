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

__context__ = 'zero-doc'

try:
    remote_version = core.get_git_version()
except:
    remote_version = 'Not available'

# Handle Language versions
if HOST_APP.language == LanguageType.Russian:
    user = "Имя пользователя"
    Rvers = "Версия Ревит"
    Bvers = "Версия установленного расширения"
    Bvers_remote = "Последняя доступная версия"
    lang = "RU"
else:
    user = "Username"
    Rvers = "Revit Version"
    Bvers = "Extension version"
    Bvers_remote = "Latest available version"
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
print(str(Bvers_remote) + ' : {}'.format(remote_version))

out.print_html('<a href="https://github.com/romangolev/pyArchitect">pyArchitect GitHub repository</a>')
out.print_html('<a href="https://www.romangolev.com">Roman Golev</a><a> </a><a href="https://www.linkedin.com/in/romangolev/">LinkedIn</a><a>, 2024</a>')