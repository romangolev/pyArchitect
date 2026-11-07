# -*- coding: utf-8 -*-
import unittest

import revit_stubs

script = revit_stubs.load_script(
    "pyArchitect.tab", "Tools.panel", "tools3.stack",
    "DeleteSharedParam.pushbutton", "script.py")


class ConfirmDeleteTests(unittest.TestCase):

    def confirm(self, answer):
        script["forms"].alert = lambda *args, **kwargs: answer
        script["make_label"] = lambda name, guid, info: name
        return script["confirm_delete"](["Mark"], {"Mark": "guid"}, {})

    def test_clicking_ok_confirms(self):
        self.assertTrue(self.confirm(True))

    def test_clicking_cancel_does_not_confirm(self):
        self.assertFalse(self.confirm(False))


if __name__ == "__main__":
    unittest.main()
