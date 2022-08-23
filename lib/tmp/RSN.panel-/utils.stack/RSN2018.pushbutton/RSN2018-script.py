# -*- coding: utf-8 -*-
# pylint: skip-file

__doc__ = """Меняет адрес Revit Server 2018 / Change Revit Server 2018 Network adress"""
__title__ = "RSN 2018"
__author__ = "Roman Golev"
__context__ = 'zero-doc'

import subprocess
subprocess.call([r'\\10.10.50.30\shared$\Standards\01.BA STANDARDS\08.BIM STANDARDS\04.TEMPLATE\01.RSN_SETUP\2018\copy_RSN.cmd'])
