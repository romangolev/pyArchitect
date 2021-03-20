# -*- coding: utf-8 -*-
# pylint: skip-file
# Opens Folder With BIM Standards Locations
# by Roman Golev 
# Blank Architects

__doc__ = """Открывает директорию с актуальным БИМ стандартом / Opens Folder With BIM Standard Location"""
__title__ = "BIM Стандарт"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

#Opens folder in explorer

import subprocess
subprocess.Popen(r'explorer "#Here is the location of folder"')
