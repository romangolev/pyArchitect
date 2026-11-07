# -*- coding: utf-8 -*-
import unittest

import revit_stubs

revit_stubs.install()

from tools.finishing import FinishingRoom


class Value(object):
    def __init__(self, value=0.0):
        self.value = value

    def AsDouble(self):
        return self.value

    def AsString(self):
        return u"101"

    def Set(self, value):
        self.value = value


class Floor(object):
    def __init__(self):
        self.params = {}

    def get_Parameter(self, key):
        return self.params.setdefault(key, Value())


class Document(object):
    def __init__(self):
        self.created = []
        self.Create = self

    def GetElement(self, element_id):
        return object()

    def NewFloor(self, *args):
        floor = Floor()
        self.created.append(floor)
        return floor


class Room(object):
    def __init__(self, doc):
        self.Document = doc
        self.Level = revit_stubs.Anything()

    def get_Parameter(self, key):
        return Value(3.0)

    def GetBoundarySegments(self, options):
        return [[revit_stubs.Anything()]]


class App(object):
    VersionNumber = "2021"


class FinishingFloorTests(unittest.TestCase):

    def test_a_ceiling_on_revit_2021_needs_no_door_notch_switch(self):
        doc = Document()
        room = FinishingRoom(Room(doc))
        switches = {"Consider Thickness": True,
                    "Write Room Data to Text Parameter": False}
        room.make_finishing_floor(Floor(), switches, App(), mode="ceiling")
        self.assertEqual(len(doc.created), 1)


if __name__ == "__main__":
    unittest.main()
