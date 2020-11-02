# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

__doc__ = """Открывает директорию с библитекой Dynamo / Opens Folder With Dynamo library"""
__title__ = "Библиотека Dynamo"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

import subprocess
subprocess.Popen(r'explorer "\\10.10.50.30\shared$\Standards\01.BA STANDARDS\08.BIM STANDARDS\02.RESOURCES\Autodesk_Dynamo"')
