# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")
import sys


class UnitConverter:

    @staticmethod
    def convertDouble(uiapp, doubleValue, units):

          versionNumber = uiapp.Application.VersionNumber
          value_converted = ''
          if "2019" in versionNumber or "2020" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
               value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, units)
          else:
               from Autodesk.Revit.DB import UnitUtils, UnitTypeId
               value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, units)

          return value_converted

    @staticmethod
    def convertDoubleToM3(uiapp, doubleValue):
          versionNumber = uiapp.Application.VersionNumber
          value_converted = ''
          if "2019" in versionNumber or "2020" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
               value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, DisplayUnitType.DUT_CUBIC_METERS)
          else:
               from Autodesk.Revit.DB import UnitUtils, UnitTypeId
               value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, UnitTypeId.CubicMeters)

          return value_converted
