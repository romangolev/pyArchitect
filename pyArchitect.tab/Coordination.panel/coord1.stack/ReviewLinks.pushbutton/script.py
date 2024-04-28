# -*- coding: utf-8 -*- 

try:
    from pyrevit.versionmgr import PYREVIT_VERSION

    pyRevitNewer44 = PYREVIT_VERSION.major >= 4 and PYREVIT_VERSION.minor >= 5

except:
    from pyrevit import versionmgr

    PYREVIT_VERSION = versionmgr.get_pyrevit_version()
    pyRevitNewer44 = True

if pyRevitNewer44:
    from pyrevit import script, revit

    logger = script.get_logger()
    output = script.get_output()
    linkify = output.linkify
    selection = revit.get_selection()
    doc = revit.doc
    uidoc = revit.uidoc
else:
    from scriptutils import logger
    from scriptutils import this_script

    linkify = this_script.output.linkify
    uidoc = __revit__.ActiveUIDocument # type: ignore
    doc = uidoc.Document

from Autodesk.Revit.UI import TaskDialog, TaskDialogCommonButtons
from Autodesk.Revit.DB import *
import re
import os

cl = FilteredElementCollector(doc).WhereElementIsElementType()
selection = cl.OfCategory(BuiltInCategory.OST_RvtLinks).ToElementIds()


def file2ws_name(filename):
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

    tr = {ord(a): ord(b) for a, b in zip(*symbols)}

    filename, ext = os.path.splitext(filename)
    ext = ext.replace('.', '')
    filename = re.sub(r'[^a-zA-Zа-яА-Я0-9_-]', '_', filename)
    filename = filename.translate(tr)

    return "##_{ext}_{filename}".format(ext=ext, filename=filename).upper()


class Check(object):
    def __init__(self, elements):

        self.elements = elements
        self.errors = {}
        self.fix_text = "Fix these warnings?"

    def run(self):
        self.check_all()
        if len(self.errors.keys()) > 0:
            error_text = self.fix_text + "\n\n" + "\n\n".join(list(self.errors.keys()))

            q = TaskDialog.Show(type(self).__name__, error_text,
                                TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel)
            if str(q) == "Ok":
                self.fix()

    def check_all(self):
        for k in self.elements.keys():
            els = self.elements[k]
            for e in els:
                self.check_one(e, k) # type: ignore

    def check_one(self, e):
        pass

    def fix(self):
        pass


class CheckPinned(Check):
    def __init__(self, elements):
        super(self.__class__, self).__init__(elements)

    def check_one(self, e, k):
        t = doc.GetElement(k)
        filename = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
        is_nested = doc.GetElement(e.GetTypeId()).IsNestedLink

        if e.Pinned == False and not is_nested:
            message = '%s instance not pinned' % (filename,)
            if message not in self.errors:
                self.errors[message] = []
            self.errors[message].append(e)

    def fix(self):
        t = Transaction(doc, 'Fix links - Pin')
        t.Start()
        for vv in self.errors.values():
            for e in vv:
                e.Pinned = True
        t.Commit()


class SaveSharedCoordinatesCallback(ISaveSharedCoordinatesCallback):
    def GetSaveModifiedLinksOption(self, link):
        return SaveModifiedLinksOptions.DisableSharedPositioning

    def __init__(self):
        pass


class CheckWorkset(Check):
    def __init__(self, elements):
        super(self.__class__, self).__init__(elements)
        self.allowed_pattern = r"(A[-_]{1}LNK|\.|00[-_]{1}|01[-_]{1}|#)"
        _all_worksets = FilteredWorksetCollector(doc).OfKind(WorksetKind.UserWorkset).ToWorksets()
        self.all_worksets = {}

        for w in _all_worksets:
            self.all_worksets[w.Id.IntegerValue] = w.Name

    def check_one(self, e, k):
        ws_name = self.all_worksets[e.WorksetId.IntegerValue]
        m = re.match(self.allowed_pattern, ws_name, re.I)
        ws_name_type = self.all_worksets[doc.GetElement(e.GetTypeId()).WorksetId.IntegerValue]
        m_type = re.match(self.allowed_pattern, ws_name_type, re.I)
        is_nested = doc.GetElement(e.GetTypeId()).IsNestedLink
        if (not m or not m_type) and not is_nested:
            t = doc.GetElement(k)
            filename = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
            ws_name_new = file2ws_name(filename)
            message = '%s in %s --> %s' % (filename, ws_name, ws_name_new,)
            if message not in self.errors:
                self.errors[message] = []
            self.errors[message].append((e, ws_name_new))

    #
    def fix(self):
        needed_workset = set()
        [[needed_workset.add(v[1]) for v in vv] for vv in self.errors.values()]
        t = Transaction(doc, 'Workset creation')
        t.Start()
        for ws in needed_workset:
            if ws not in self.all_worksets.values():
                print("new workset %s" % ws)
                ws_new = Workset.Create(doc, ws)
                self.all_worksets[ws_new.Id.IntegerValue] = ws
                # e, new_value = self.errors[k]
        t.Commit()
        t = Transaction(doc, 'Workset change')
        t.Start()
        all_worksets_inv = {v: k for k, v in self.all_worksets.iteritems()}

        for vv in self.errors.values():
            for e, ws_name_new in vv:
                is_nested = doc.GetElement(e.GetTypeId()).IsNestedLink
                if is_nested:
                    continue

                wsparam = e.get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
                if (wsparam == None):
                    continue
                wsparam.Set(all_worksets_inv[ws_name_new])
                # Update type workset
                wsparam = doc.GetElement(e.GetTypeId()).get_Parameter(BuiltInParameter.ELEM_PARTITION_PARAM)
                if (wsparam == None):
                    continue
                wsparam.Set(all_worksets_inv[ws_name_new])

        t.Commit()


def collect_links():
    """
    Collects links from model in format
    { LinkType: [LinkInstance, LinkInstance, ... ] }

    :return:
    dict
    """

    links = {}

    cl = FilteredElementCollector(doc).OfCategory(
        BuiltInCategory.OST_RvtLinks).WhereElementIsNotElementType().ToElementIds()
    for e_id in cl:
        e = doc.GetElement(e_id)
        type_id = e.GetTypeId()
        if type_id not in links:
            links[type_id] = []
        links[type_id].append(e)

    return links


def main():
    links = collect_links()
    if doc.IsWorkshared:
        CheckWorkset(links).run()
    CheckPinned(links).run()


if __name__ == '__main__':
    main()