# -*- coding: utf-8 -*-
import unittest

import revit_stubs

revit_stubs.install()

from tools import joining


class Element(object):
    def __init__(self, element_id):
        self.Id = element_id


class JoinIntersectingTests(unittest.TestCase):

    def setUp(self):
        self.joined = []
        self.touching = {}
        self.seconds = []
        joining.touching = lambda doc, first, candidates: [
            s for s in self.seconds if s.Id in self.touching.get(first.Id, ())]
        joining.join = lambda doc, a, b: self.joined.append((a.Id, b.Id)) or True

    def join_intersecting(self, firsts, seconds):
        self.seconds = seconds
        return joining.join_intersecting(None, firsts, seconds)

    def test_only_elements_that_touch_are_joined(self):
        self.touching = {1: {2}}
        count = self.join_intersecting([Element(1)], [Element(2), Element(3)])
        self.assertEqual((count, self.joined), (1, [(1, 2)]))

    def test_an_element_in_both_groups_is_not_joined_to_itself(self):
        wall = Element(1)
        self.touching = {1: {1, 2}}
        self.join_intersecting([wall], [wall, Element(2)])
        self.assertEqual(self.joined, [(1, 2)])


if __name__ == "__main__":
    unittest.main()
