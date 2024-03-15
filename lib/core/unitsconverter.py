# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")
import sys


class UnitConverter:
     
     @staticmethod
     def convertDouble(uiapp, doubleValue,units):

          versionNumber = uiapp.Application.VersionNumber
          value_converted = ''
          if "2019" in versionNumber or "2020" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
          elif "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, UnitTypeId
          else:
               try:
                    from Autodesk.Revit.DB import UnitUtils, UnitTypeId
               except Exception as e:
                    print(e)
                    sys.exit()

          if "2019" in versionNumber or "2020" in versionNumber:
                    value_converted = UnitUtils.ConvertToInternalUnits(doubleValue, units)
          if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
                    value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, units)

          return value_converted

     @staticmethod
     def convertDoubleToM3(uiapp, doubleValue):
          versionNumber = uiapp.Application.VersionNumber
          value_converted = ''
          if "2019" in versionNumber or "2020" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, DisplayUnitType
          elif "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
               from Autodesk.Revit.DB import UnitUtils, UnitTypeId
          else:
               try:
                    from Autodesk.Revit.DB import UnitUtils, UnitTypeId
               except Exception as e:
                    print(e)
                    sys.exit()

          
          if "2019" in versionNumber or "2020" in versionNumber:
                    value_converted = UnitUtils.ConvertToInternalUnits(doubleValue, DisplayUnitType.DUT_CUBIC_METERS)
          if "2021" in versionNumber or "2022" in versionNumber or "2023" in versionNumber or "2024" in versionNumber:
                    value_converted = UnitUtils.ConvertFromInternalUnits(doubleValue, UnitTypeId.CubicMeters)

          return value_converted