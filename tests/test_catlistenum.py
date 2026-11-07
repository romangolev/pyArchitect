# -*- coding: utf-8 -*-
import unittest

import revit_stubs

revit_stubs.install()

from core import catlistenum


class CategoryTableTests(unittest.TestCase):

    def test_every_name_is_listed_once_in_order(self):
        names = catlistenum.category_names()
        self.assertEqual(names, sorted(set(names), key=names.index))
        self.assertEqual(names.count("Duct Fittings"), 1)

    def test_walls_map_to_the_walls_category(self):
        self.assertEqual(catlistenum.CATEGORIES["Walls"], "OST_Walls")


if __name__ == "__main__":
    unittest.main()
