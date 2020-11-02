# -*- coding: utf-8 -*-
# pylint: skip-file
# Opens Folder With BIM Standards Locations
# by Roman Golev 
# Blank Architects

__doc__ = """Открывает директорию с актуальным БИМ стандартом / Opens Folder With BIM Standard Location"""
__title__ = "BIM Стандарт"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

import subprocess
subprocess.Popen(r'explorer "\\10.10.50.30\shared$\Standards\01.BA STANDARDS\08.BIM STANDARDS\01.BA_BIM-STANDARD"')
