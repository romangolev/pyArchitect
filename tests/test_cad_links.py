# -*- coding: utf-8 -*-
import unittest

import revit_stubs

revit_stubs.install()

from tools.cad_links import group_by_format


class Instance(object):
    def __init__(self, element_id, linked=True, view_specific=False):
        self.Id = element_id
        self.WorksetId = 1
        self.IsLinked = linked
        self.ViewSpecific = view_specific


class GroupByFormatTests(unittest.TestCase):

    def test_two_dwgs_and_a_dgn_make_two_groups(self):
        groups = group_by_format([(Instance(1), u"plan.dwg"),
                                  (Instance(2), u"site.DWG"),
                                  (Instance(3), u"survey.dgn")])
        self.assertEqual([(g.target, sorted(g.element_ids())) for g in groups],
                         [(u"##_DGN", [3]), (u"##_DWG", [1, 2])])

    def test_a_view_specific_dwg_is_left_out(self):
        groups = group_by_format([(Instance(1, view_specific=True), u"a.dwg")])
        self.assertEqual(groups, [])

    def test_an_imported_dwg_is_left_out(self):
        groups = group_by_format([(Instance(1, linked=False), u"a.dwg")])
        self.assertEqual(groups, [])

    def test_the_group_label_counts_its_files(self):
        groups = group_by_format([(Instance(1), u"a.dwg"),
                                  (Instance(2), u"b.dwg")])
        self.assertEqual(groups[0].file_name, u"*.dwg (2)")


if __name__ == "__main__":
    unittest.main()
