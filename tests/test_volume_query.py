# -*- coding: utf-8 -*-
import unittest

import revit_stubs

script = revit_stubs.load_script(
    "pyArchitect.tab", "Tools.panel", "tools2.stack",
    "VolumeQuery.pushbutton", "script.py")

FT3_TO_M3 = 0.0283168


class Value(object):
    def __init__(self, value):
        self.value = value

    def AsDouble(self):
        return self.value


class Solid(object):
    def __init__(self, volume):
        self.Volume = volume


class Wall(object):
    def __init__(self, computed, solids=()):
        self.computed = computed
        self.solids = list(solids)

    def get_Parameter(self, key):
        return Value(self.computed)

    def get_Geometry(self, options):
        return self.solids


class ElementVolumeTests(unittest.TestCase):

    def setUp(self):
        script["UnitConverter"].convertDoubleToM3 = staticmethod(
            lambda uiapp, value: value * FT3_TO_M3)
        script["is_solid"] = lambda item: isinstance(item, Solid)

    def test_a_wall_with_a_computed_volume_reports_it_in_m3(self):
        self.assertAlmostEqual(script["element_volume"](Wall(100.0)), 2.83168)

    def test_a_wall_without_one_adds_up_its_solids(self):
        wall = Wall(0.0, [Solid(60.0), Solid(40.0)])
        self.assertAlmostEqual(script["element_volume"](wall), 2.83168)


if __name__ == "__main__":
    unittest.main()
