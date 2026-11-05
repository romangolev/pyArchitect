# -*- coding: utf-8 -*-
import contextlib
import os
import sys
import types
import unittest

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
sys.path.insert(0, LIB)


def stub(name, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module
    return module


class Anything(object):
    def __getattr__(self, name):
        return Anything()

    def __call__(self, *args, **kwargs):
        return Anything()


stub("System", Version=object)
stub("Autodesk")
stub("Autodesk.Revit")
sys.modules["Autodesk.Revit.DB"] = Anything()
stub("pyrevit")
stub("pyrevit.coreutils")
stub("pyrevit.coreutils.applocales", get_locale_string=lambda v: None)
stub("core.selectionhelpers", id_value=lambda element_id: element_id)


@contextlib.contextmanager
def wrapped(*args):
    yield


stub("core.transaction", WrappedTransaction=wrapped,
     WrappedTransactionGroup=wrapped)

import tools.workset_doctor as wd
from tools.cad_links import CadLinks
from tools.link_doctor import file2ws_name


class Element(object):
    def __init__(self, element_id, workset):
        self.Id = element_id
        self.WorksetId = workset


class Link(object):
    def __init__(self, file_name, element_ids, workset):
        self.file_name = file_name
        self.target = file2ws_name(file_name)
        self._elements = [Element(i, workset) for i in element_ids]

    def elements(self):
        return self._elements

    def element_ids(self):
        return set(e.Id for e in self._elements)


class Workset(object):
    def __init__(self, key, name, default=False):
        self.Id = key
        self.Name = name
        self.IsDefaultWorkset = default


class Doc(object):
    def __init__(self, workshared=True):
        self.IsWorkshared = workshared


def run(worksets, contents, links, workshared=True, cad=(), datums=(),
        model=None):
    table = dict((ws.Id, ws) for ws in worksets)
    placed = contents if model is None else model
    wd.user_worksets = lambda doc: table
    wd.workset_contents = lambda doc, key: set(contents.get(key, ()))
    wd.placed_model_ids = lambda doc, key: set(placed.get(key, ()))
    wd.collect_links = lambda doc: links
    wd.can_delete_worksets = lambda: True
    wd.collect_cad_links = lambda doc: list(cad)
    wd.collect_datums = lambda doc: list(datums)
    return wd.diagnose(Doc(workshared))


def kinds(diagnosis):
    return [(f.kind, f.name) for f in diagnosis.fixes]


class DiagnoseTests(unittest.TestCase):

    def test_a_workset_holding_only_link_a_is_renamed_into_place(self):
        link = Link("A.rvt", [10, 11], 2)
        diagnosis = run([Workset(1, u"Workset1", True), Workset(2, u"Links")],
                        {2: {10, 11}}, [link])
        self.assertEqual(kinds(diagnosis), [("rename", u"##_RVT_A")])

    def test_two_links_with_the_same_target_share_one_workset(self):
        first = Link("A B.rvt", [10], 1)
        second = Link("A_B.rvt", [20], 1)
        diagnosis = run([Workset(1, u"Workset1", True)], {1: {10, 20}},
                        [first, second])
        self.assertEqual(kinds(diagnosis), [("move", u"##_RVT_A_B"),
                                            ("move", u"##_RVT_A_B")])

    def test_second_link_with_the_same_target_follows_the_renamed_workset(self):
        first = Link("A B.rvt", [10], 2)
        second = Link("A_B.rvt", [20], 1)
        diagnosis = run([Workset(1, u"Workset1", True), Workset(2, u"Old")],
                        {2: {10}}, [first, second])
        self.assertEqual(kinds(diagnosis), [("rename", u"##_RVT_A_B"),
                                            ("move", u"##_RVT_A_B")])

    def test_an_empty_template_workset_is_kept(self):
        diagnosis = run([Workset(1, u"Workset1", True),
                         Workset(2, u"Interiors")], {}, [])
        self.assertEqual(kinds(diagnosis), [])

    def test_an_empty_link_workset_is_deleted(self):
        diagnosis = run([Workset(1, u"Workset1", True),
                         Workset(2, u"##_RVT_OLD")], {}, [])
        self.assertEqual(kinds(diagnosis), [("delete", u"##_RVT_OLD")])

    def test_a_link_workset_emptied_by_a_move_is_deleted(self):
        a = Link("A.rvt", [10], 2)
        b = Link("B.rvt", [20], 2)
        diagnosis = run([Workset(1, u"Workset1", True),
                         Workset(2, u"##_RVT_SHARED")], {2: {10, 20}}, [a, b])
        self.assertEqual(kinds(diagnosis), [("move", u"##_RVT_A"),
                                            ("move", u"##_RVT_B"),
                                            ("delete", u"##_RVT_SHARED")])


class DefaultWorksetTests(unittest.TestCase):

    def test_a_renamed_default_gets_workset1_back_and_its_content_keeps_the_name(self):
        link = Link("A.rvt", [10], 1)
        diagnosis = run([Workset(1, u"Architecture", True)],
                        {1: {10, 50, 51}}, [link])
        self.assertEqual(kinds(diagnosis), [("rename", u"Workset1"),
                                            ("move", u"##_RVT_A"),
                                            ("empty", u"Architecture")])

    def test_a_localized_default_name_is_renamed_to_workset1(self):
        diagnosis = run([Workset(1, u"Рабочий набор1", True)], {1: {50}}, [])
        self.assertEqual(kinds(diagnosis), [("rename", u"Workset1"),
                                            ("empty", u"Рабочий набор1")])

    def test_workset1_holding_model_elements_is_emptied_into_model(self):
        diagnosis = run([Workset(1, u"Workset1", True)], {1: {50}}, [])
        self.assertEqual(kinds(diagnosis), [("empty", u"Model")])

    def test_workset1_holding_only_internal_elements_needs_no_emptying(self):
        diagnosis = run([Workset(0, u"Workset1", True)],
                        {0: set(range(500, 918))}, [], model={0: set()})
        self.assertEqual(kinds(diagnosis), [])

    def test_workset1_holding_only_a_link_needs_no_emptying(self):
        link = Link("A.rvt", [10], 1)
        diagnosis = run([Workset(1, u"Workset1", True)], {1: {10}}, [link])
        self.assertEqual(kinds(diagnosis), [("move", u"##_RVT_A")])

    def test_an_empty_renamed_default_is_only_renamed(self):
        diagnosis = run([Workset(1, u"Architecture", True)], {}, [])
        self.assertEqual(kinds(diagnosis), [("rename", u"Workset1")])

    def test_a_default_named_like_a_link_hands_the_name_to_the_link(self):
        link = Link("A.rvt", [10], 1)
        diagnosis = run([Workset(1, u"##_RVT_A", True)], {1: {10, 50}}, [link])
        self.assertEqual(kinds(diagnosis), [("rename", u"Workset1"),
                                            ("move", u"##_RVT_A"),
                                            ("empty", u"Model")])
        self.assertEqual(diagnosis.notes, [])

    def test_the_default_is_left_alone_when_workset1_is_taken(self):
        diagnosis = run([Workset(1, u"Architecture", True),
                         Workset(2, u"Workset1")], {1: {50}, 2: {60}}, [])
        self.assertEqual(kinds(diagnosis), [])
        self.assertIn(u"'Workset1'", wd.format_summary(None, diagnosis))

    def test_an_unflagged_workset_named_workset1_is_not_the_default(self):
        diagnosis = run([Workset(0, u"Architecture", True),
                         Workset(7, u"Workset1")], {0: {50}, 7: {60}}, [])
        self.assertEqual(kinds(diagnosis), [])
        self.assertIn(u"'Architecture'", wd.format_summary(None, diagnosis))

    def test_of_two_flagged_worksets_the_one_with_id_0_is_the_default(self):
        diagnosis = run([Workset(0, u"Architecture", True),
                         Workset(7, u"Other", True)], {0: {50}, 7: {60}}, [])
        self.assertEqual([(f.kind, id_of(f)) for f in diagnosis.fixes],
                         [("rename", 0), ("empty", 0)])

    def test_two_flagged_worksets_without_id_0_are_left_alone(self):
        diagnosis = run([Workset(3, u"Architecture", True),
                         Workset(7, u"Other", True)], {3: {50}, 7: {60}}, [])
        self.assertEqual(kinds(diagnosis), [])


class SharedLevelsAndGridsTests(unittest.TestCase):

    def test_a_grid_on_workset1_moves_to_shared_levels_and_grids(self):
        grid = Element(40, 0)
        diagnosis = run([Workset(0, u"Workset1", True),
                         Workset(189, u"Shared Levels and Grids")],
                        {0: {40}, 189: {41}}, [],
                        datums=[grid, Element(41, 189)])
        self.assertEqual(kinds(diagnosis),
                         [("datums", u"Shared Levels and Grids")])

    def test_a_level_on_another_workset_moves_too(self):
        diagnosis = run([Workset(0, u"Workset1", True),
                         Workset(189, u"Shared Levels and Grids"),
                         Workset(720, u"Architecture")],
                        {720: {42, 50}}, [], datums=[Element(42, 720)])
        self.assertEqual(kinds(diagnosis),
                         [("datums", u"Shared Levels and Grids")])

    def test_datums_already_in_place_need_nothing(self):
        diagnosis = run([Workset(0, u"Workset1", True),
                         Workset(189, u"Shared Levels and Grids")],
                        {189: {41}}, [], datums=[Element(41, 189)])
        self.assertEqual(kinds(diagnosis), [])

    def test_workset1_with_datums_and_model_elements_sends_each_its_way(self):
        diagnosis = run([Workset(0, u"Workset1", True)], {0: {40, 50}}, [],
                        datums=[Element(40, 0)])
        self.assertEqual(kinds(diagnosis),
                         [("datums", u"Shared Levels and Grids"),
                          ("empty", u"Model")])

    def test_a_datum_on_a_link_workset_lets_that_workset_go(self):
        diagnosis = run([Workset(0, u"Workset1", True),
                         Workset(189, u"Shared Levels and Grids"),
                         Workset(5, u"##_RVT_OLD")],
                        {5: {42}}, [], datums=[Element(42, 5)])
        self.assertEqual(kinds(diagnosis),
                         [("datums", u"Shared Levels and Grids"),
                          ("delete", u"##_RVT_OLD")])


class CadLinkTests(unittest.TestCase):

    def test_dwgs_on_workset1_move_to_one_dwg_workset(self):
        dwgs = CadLinks(u"DWG", [Element(30, 1), Element(31, 1)])
        diagnosis = run([Workset(1, u"Workset1", True)], {1: {30, 31}}, [],
                        cad=[dwgs])
        self.assertEqual(kinds(diagnosis), [("move", u"##_DWG")])

    def test_dwgs_already_on_the_dwg_workset_need_nothing(self):
        dwgs = CadLinks(u"DWG", [Element(30, 2)])
        diagnosis = run([Workset(1, u"Workset1", True),
                         Workset(2, u"##_DWG")], {2: {30}}, [], cad=[dwgs])
        self.assertEqual(kinds(diagnosis), [])


def id_of(fix):
    return fix.workset_id


class SummaryTests(unittest.TestCase):

    def test_a_non_workshared_file_says_so(self):
        diagnosis = run([], {}, [], workshared=False)
        self.assertEqual(wd.format_summary(None, diagnosis),
                         wd.S("done.not_workshared"))

    def test_a_healthy_project_reports_nothing_about_the_default(self):
        diagnosis = run([Workset(1, u"Workset1", True)], {}, [])
        self.assertEqual(wd.format_summary(None, diagnosis),
                         wd.S("done.healthy"))


if __name__ == "__main__":
    unittest.main()
