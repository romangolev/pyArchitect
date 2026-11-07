# -*- coding: utf-8 -*-
import unittest

import revit_stubs

class ViewFamily(object):
    ThreeDimensional = "ThreeDimensional"


revit_stubs.install()
revit_stubs.stub("Autodesk.Revit.DB", ViewFamily=ViewFamily)

from core import views


class ViewType(object):
    def __init__(self, family):
        self.ViewFamily = family


class ViewType3DTests(unittest.TestCase):

    def test_the_first_3d_type_is_returned(self):
        wanted = ViewType(ViewFamily.ThreeDimensional)
        views.view_types = lambda doc: [ViewType("Section"), wanted]
        self.assertIs(views.view_type_3d(None), wanted)

    def test_none_when_the_model_has_no_3d_type(self):
        views.view_types = lambda doc: [ViewType("Section")]
        self.assertIsNone(views.view_type_3d(None))


if __name__ == "__main__":
    unittest.main()
