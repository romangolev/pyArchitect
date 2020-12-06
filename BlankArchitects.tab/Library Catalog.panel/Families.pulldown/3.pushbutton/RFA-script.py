# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Открывает директорию с библитекой семейств / Opens Folder With Revit Families"""
__title__ = "Обновлённая библиотека BlankArchitects"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

import subprocess
import pyrevit
from pyrevit import script
#subprocess.Popen(r'explorer "\\BA-MAIN\Standards\01.BA STANDARDS\08.BIM STANDARDS\02.RESOURCES\Autodesk_Revit\03.FAMILIES\03.COMPANIES\BRUSNICA"')

script.load_index(index_file = 'lib1.html')