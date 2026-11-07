# -*- coding: utf-8 -*-
import unittest

import revit_stubs

script = revit_stubs.load_script(
    "pyArchitect.tab", "Tools.panel", "tools1.stack",
    "CreateSectionBasedOnWall.pushbutton", "script.py")

WALLS = -2000011
SEPARATION_LINES = -2000066
DOORS = -2000023


class Element(object):
    def __init__(self, category_id):
        self.Category = self
        self.Id = category_id


class UnsupportedTests(unittest.TestCase):

    def test_walls_and_separation_lines_are_supported(self):
        elements = [Element(WALLS), Element(SEPARATION_LINES)]
        self.assertEqual(script["unsupported"](elements), [])

    def test_a_door_is_not_supported(self):
        door = Element(DOORS)
        self.assertEqual(script["unsupported"]([Element(WALLS), door]), [door])


if __name__ == "__main__":
    unittest.main()
