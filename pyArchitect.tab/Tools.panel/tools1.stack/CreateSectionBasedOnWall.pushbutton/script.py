# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys
from Autodesk.Revit.DB import BuiltInParameter, XYZ, Transform, BoundingBoxXYZ, \
                                ViewSection, ViewFamilyType, FilteredElementCollector, \
                                ViewFamily

from pyrevit import forms
from core.selectionhelpers import CustomISelectionFilterByIdInclude, ID_WALLS, \
    ID_SEPARATION_LINES, get_selection_basic, id_value
from core.transaction import WrappedTransaction, WrappedTransactionGroup

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore

SUPPORTED = ID_WALLS + ID_SEPARATION_LINES


def unsupported(elements):
    return [e for e in elements
            if e.Category is None or id_value(e.Category.Id) not in SUPPORTED]


def create_section(ref_elem, doc, viewFamilyTypeId, flip):
    offset = 100/304.8 # 100mm offset as Double
    # Determine section box
    lc = ref_elem.Location
    line = lc.Curve

    p = line.GetEndPoint(0)
    q = line.GetEndPoint(1)
    if flip == False:
        v = q - p
    else:
        v = p - q

    if id_value(ref_elem.Category.Id) in ID_WALLS:
        w = v.GetLength()
        d = ref_elem.WallType.Width
        BaseOffset = ref_elem.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        UnconnectedHeight = ref_elem.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()
    else:
        w = ref_elem.get_Parameter(BuiltInParameter.CURVE_ELEM_LENGTH).AsDouble()
        d = 300/304.8 # 300mm as Double
        BaseOffset = 0
        UnconnectedHeight = 3000/304.8 # 3000mm as Double

    # XYZ(min/max section line length, min/max height of the section box, min/max far clip)
    min = XYZ(-0.5*w - offset, BaseOffset - offset, - offset - 0.5*d)
    max = XYZ(0.5*w + offset, BaseOffset + UnconnectedHeight + offset, offset + 0.5*d)

    # factor for direction of section view
    if p.X > q.X or (p.X == q.X and p.Y < q.Y): fc = 1
    else: fc = -1

    if flip == False:
        midpoint = p + 0.5*v
    else:
        midpoint = q + 0.5*v

    walldir = fc*v.Normalize()
    up = XYZ.BasisZ
    viewdir = walldir.CrossProduct(up)

    tr = Transform.Identity
    tr.Origin = midpoint
    tr.BasisX = walldir
    tr.BasisY = up
    tr.BasisZ = viewdir

    sectionBox = BoundingBoxXYZ()
    sectionBox.Transform = tr
    sectionBox.Min = min # scope box bottom
    sectionBox.Max = max # scope box top

    # Create ref_elem section view
    with WrappedTransaction(doc, 'Create Section'):
        return ViewSection.CreateSection(doc, viewFamilyTypeId, sectionBox)


def main():
    selection = get_selection_basic(
        uidoc, CustomISelectionFilterByIdInclude(SUPPORTED))
    elements = [doc.GetElement(item) for item in selection]

    # Check selected elements
    if not elements:
        forms.alert("Please, select ref_elem", "Section For Wall")
        sys.exit()
    if unsupported(elements):
        forms.alert("The tool works only with walls and separation liners", "Section For Wall")
        sys.exit()

    #Get section types
    sec_types = []
    view_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
    for types in view_types :
        if types.ViewFamily == ViewFamily.Section:
            sec_types.append(types)

    # Find applicable section types:
    sec_type_options = []
    for i in sec_types:
        sec_type_options.append(i.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString())
    # Make a dictionary for sections to easy selection
    res = dict(zip(sec_type_options,sec_types))

    # Switches panel implementation using pyrevit
    msg = """Choose section type and parameter"""
    switches = ["Flip section"]
    cfgs = {'option1': { 'background': '0xFF55FF'}}
    options, sw = forms.CommandSwitchWindow.show(sec_type_options,
                                            message=msg,
                                            config=cfgs,
                                            switches=switches)
    if options is None:
        sys.exit()

    viewFamilyTypeId = res[options].Id

    #Make section(s)
    with WrappedTransactionGroup(doc, "Create multiple sections"):
        for element in elements:
            try:
                create_section(element, doc, viewFamilyTypeId, sw["Flip section"])
            except Exception as e:
                print(e)

if __name__ == '__main__':
    main()
