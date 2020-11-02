# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Открывает директорию с актуальными шаблонами Revit / Opens Folder With Revit Templates"""
__title__ = "Шаблоны\nRevit"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

import subprocess
subprocess.Popen(r'explorer "\\BA-MAIN\Standards\01.BA STANDARDS\08.BIM STANDARDS\02.RESOURCES\Autodesk_Revit\02.TEMPLATES"')
