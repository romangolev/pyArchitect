# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import Autodesk
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import *


def convertDouble(uiapp, doubleValue,units):

     versionNumber = uiapp.Application.VersionNumber
     
     if "2019" in versionNumber or "2020" in versionNumber:
          from Autodesk.Revit.DB import UnitUtils
     if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
          from Autodesk.Revit.DB import UnitUtils, UnitTypeId

     
     if "2019" in versionNumber or "2020" in versionNumber:
               value_converted = UnitUtils.ConvertToInternalUnits(doubleValue, units)
     if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
               value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, units)

     return value_converted