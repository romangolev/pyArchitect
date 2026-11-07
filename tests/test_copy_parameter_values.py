# -*- coding: utf-8 -*-
import unittest

import revit_stubs


class StorageType(object):
    Integer = "Integer"
    Double = "Double"
    String = "String"
    ElementId = "ElementId"


revit_stubs.install()
revit_stubs.stub("Autodesk.Revit.DB", StorageType=StorageType)
script = revit_stubs.load_script(
    "pyArchitect.tab", "Tools.panel", "CopyParameterValues.pushbutton",
    "script.py")

FEET_TO_MM = 304.8


class Parameter(object):
    IsShared = False
    Name = "Length"

    def __init__(self, storage_type, value=None):
        self.StorageType = storage_type
        self.value = value
        self.Definition = self

    def AsDouble(self):
        return self.value

    def GetUnitTypeId(self):
        return "millimeters"

    def Set(self, value):
        self.value = value


class Element(object):
    def __init__(self, parameter):
        self.parameter = parameter

    def GetParameters(self, name):
        return [self.parameter]


class CopyDoubleTests(unittest.TestCase):

    def setUp(self):
        script["UnitConverter"].convertDouble = staticmethod(
            lambda uiapp, value, units: value * FEET_TO_MM)

    def copy(self, to_type):
        source = Parameter(StorageType.Double, 10.0)
        target = Parameter(to_type)
        copier = script["CopyValues"](source, target, Element(source),
                                      Element(target))
        return copier.runLogic(), target.value

    def test_a_10_ft_length_copies_to_a_number_as_10_ft(self):
        self.assertEqual(self.copy(StorageType.Double), ("Success", 10.0))

    def test_a_10_ft_length_copies_to_an_integer_in_display_units(self):
        self.assertEqual(self.copy(StorageType.Integer), ("Success", 3048))


if __name__ == "__main__":
    unittest.main()
