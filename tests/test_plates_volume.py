# -*- coding: utf-8 -*-
import unittest

import revit_stubs


class PlatesVolumeTests(unittest.TestCase):

    def test_the_script_loads(self):
        script = revit_stubs.load_script(
            "pyArchitect.tab", "Tools.panel", "tools2.stack",
            "PlatesVolume.pushbutton", "script.py")
        self.assertIn("main", script)


if __name__ == "__main__":
    unittest.main()
