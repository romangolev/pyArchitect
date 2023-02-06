# -*- coding: utf-8 -*-
__doc__ = """Creates many RVT, DWG or IFC links at once.
"""

__title__ = 'Link more'

__helpurl__ = "https://apex-project.github.io/pyApex/help#link-more"

import clr
import System
import os
clr.AddReference('System')

from pyrevit import script, revit, forms, HOST_APP
from Autodesk.Revit.DB import Document, XYZ, Transaction, DWGImportOptions, DGNImportOptions, RevitLinkOptions, RevitLinkType, \
    RevitLinkInstance, ImportUnit, View, ElementId, ModelPathUtils, UnitSystem, SaveAsOptions
from pyrevit.revit import doc, selection, uidoc

logger = script.get_logger()
output = script.get_output()


def link_method_cad():
    files_filter = "DWG files (*.dwg)|*.dwg|DXF files (*.dxf)|*.dxf|DGN files (*.dgn)|*.dgn"
    files = pick_files(files_filter)

    # preset

    origin = doc.ActiveProjectLocation.GetTotalTransform().Origin
    activeview = uidoc.ActiveView  # or uidoc.ActiveView

    q = forms.alert("Link CAD to current view only?", yes=True, no=True)
    if q:
        this_view_only = True
        target_view = activeview
    else:
        this_view_only = False
        target_view = None

    logger.debug("Files")
    logger.debug(files)

    for f in files:
        logger.info("Process file %s ..." % f)
        link_func = doc.Link.Overloads[str, DWGImportOptions, View, System.Type.MakeByRefType(ElementId)]

        ext = f[-4:]
        if ext == ".dwg":
            o = DWGImportOptions()
            o.AutoCorrectAlmostVHLines = False
            o.Unit = ImportUnit.Meter
            o.OrientToView = False
            o.ReferencePoint = origin
            o.ThisViewOnly = this_view_only
            link_func = doc.Link.Overloads[str, DWGImportOptions, View, System.Type.MakeByRefType(ElementId)]
        elif ext == ".dgn":
            o = DGNImportOptions()
            o.AutoCorrectAlmostVHLines = False
            o.Unit = ImportUnit.Meter
            o.OrientToView = False
            o.ReferencePoint = origin
            o.ThisViewOnly = this_view_only
            link_func = doc.Link.Overloads[str, DWGImportOptions, View, System.Type.MakeByRefType(ElementId)]

        t = Transaction(doc)
        t.Start(__title__)
        try:
            status, e_id = link_func(f, o, target_view, )
        except Exception as e:
            logger.error("Unable to import CAD")
            logger.error(e)
            status = False
            e_id = None
        #
        # # override rotation option
        # if __shiftclick__:
        #     q = TaskDialog.Show(__title__, "Is it okay?\nIf not CAD will be rotated",
        #                         TaskDialogCommonButtons.Yes | TaskDialogCommonButtons.No | TaskDialogCommonButtons.Cancel)
        #     if str(q) == "No":
        #         rotate = True
        #     elif str(q) == "Yes":
        #         rotate = False
        #     else:
        #         return

        if status:
            l = doc.GetElement(e_id)
            # if rotate:
            #     if l.Pinned:
            #         l.Pinned = False
            #     axis = Line.CreateBound(origin,
            #                             XYZ(origin.X, origin.Y, origin.Z + 1))
            #
            #     ElementTransformUtils.RotateElement(doc, l.Id, axis, -project_angle)
            l.Pinned = True
            t.Commit()
        else:
            t.RollBack()


def link_method_rvt():
    files_filter = "RVT files (*.rvt)|*.rvt"
    files = pick_files(files_filter)

    for f in files:
        t = Transaction(doc)
        t.Start(__title__)

        try:
            mp = ModelPathUtils.ConvertUserVisiblePathToModelPath(f)
            o = RevitLinkOptions(False)
            linkType = RevitLinkType.Create(doc, mp, o)
            instance = RevitLinkInstance.Create(doc, linkType.ElementId)
            status = True
        except Exception as e:
            logger.error("Unable to import RVT")
            logger.error(e)
            status = False
            instance = None

        if status:
            instance.Pinned = True
            t.Commit()
        else:
            t.RollBack()


def link_method_ifc():
    files_filter = "IFC files (*.ifc)|*.ifc"
    files = pick_files(files_filter)
    for f in files:
        t = Transaction(doc)
        t.Start(__title__)
        f_cache = f + ".rvt"
        recreate = not os.path.exists(f_cache)
        logger.debug("Recreate ifc %s = %s" % (f, recreate))
        # try:
        o = RevitLinkOptions(False)
        # create empty doc
        if recreate:
            doc_ifc = HOST_APP.app.OpenIFCDocument(f)
            save_options = SaveAsOptions()
            save_options.OverwriteExistingFile = True
            doc_ifc.SaveAs(f_cache, save_options)
            doc_ifc.Close()

        link_load_results = RevitLinkType.CreateFromIFC(doc, f, f_cache, False, o)
        # TODO log results http://www.revitapidocs.com/2019/11b095e1-24d9-91b9-ae2e-004f67c94d6e.htm
        logger.debug(link_load_results.LoadResult)
        instance = RevitLinkInstance.Create(doc, link_load_results.ElementId)
        status = True
        # except Exception as e:
        #     logger.error("Unable to import IFC")
        #     logger.error(e)
        #     status = False
        #     instance = None

        if status:
            instance.Pinned = True
            t.Commit()
        else:
            t.RollBack()

def link_method_pointcloud():
    files_filter = "Point Cloud project (*.rcp)|*.rcp|Point clouds (*.rcs)|*.rcs"
    files = pick_files(files_filter)


def pick_files(files_filter):
    logger.debug(files_filter)
    result = []
    for i in range(10):
        paths = forms.pick_file(
            files_filter=files_filter + "|All files (*.*)|*.*",
            restore_dir=True,
            multi_file=True)

        if not paths:
            break
        result += list(paths)

        logger.info("Files selected: " + "\n".join(paths))

        form_result = forms.alert("Add more files?", yes=True, cancel=True)
        if not form_result:
            break

    return set(result)


def method_switch():
    if revit.doc.IsFamilyDocument:
        available_methods_dict = {"CAD": link_method_cad}
    else:
        available_methods_dict = {"CAD": link_method_cad,
                                  "RVT": link_method_rvt,
                                  "IFC": link_method_ifc,
                                  # "PointCloud": link_method_pointcloud
                                  }

    selected_switch = forms.CommandSwitchWindow.show(available_methods_dict.keys(), message='Select file type to link')
    return available_methods_dict.get(selected_switch)


def main():
    func = method_switch()
    if not func:
        return
    data = func()


if __name__ == '__main__':
    main()
