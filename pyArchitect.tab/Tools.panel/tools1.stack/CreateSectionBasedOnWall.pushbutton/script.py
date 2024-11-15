# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 

import sys
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import BuiltInParameter, XYZ, Transform, BoundingBoxXYZ, \
                                ViewSection, ViewFamilyType, FilteredElementCollector, \
                                ViewFamily

from pyrevit import forms
from core.selectionhelpers import CustomISelectionFilterByIdInclude, ID_WALLS
from Autodesk.Revit.UI.Selection import ObjectType

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore
transaction = DB.Transaction(doc)
transaction_group = DB.TransactionGroup(doc)

# Get unput: selected by user elements
def get_selection():
     selobject = uidoc.Selection.GetElementIds()
     if selobject.Count == 0:
          try:
               selection = uidoc.Selection.PickObjects(ObjectType.Element, CustomISelectionFilterByIdInclude(ID_WALLS), "Selection Objects")
          except:
               sys.exit()
     elif selobject.Count != 0:
          selection = selobject
     return selection


def create_section_by_wall(el, doc, viewFamilyTypeId, transaction, flip):
    offset = 100/304.8 # 100mm offset as Double
    wall = doc.GetElement(el)
    # Determine section box
    lc = wall.Location
    line = lc.Curve

    p = line.GetEndPoint(0)
    q = line.GetEndPoint(1)
    if flip == False:
        v = q - p
    else:
        v = p - q

    bb = wall.get_BoundingBox(None)
    minZ = bb.Min.Z
    maxZ = bb.Max.Z

    w = v.GetLength()
    h = maxZ - minZ
    d = wall.WallType.Width
    wallBaseOffset = wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
    wallUnconnectedHeight = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).AsDouble()

    # XYZ(min/max section line length, min/max height of the section box, min/max far clip)
    min = XYZ(-0.5*w - offset, wallBaseOffset - offset, - offset - 0.5*d)
    max = XYZ(0.5*w + offset, wallBaseOffset + wallUnconnectedHeight + offset, offset + 0.5*d)

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

    # Create wall section view
    transaction.Start('Create Section')
    try:
        newSection = ViewSection.CreateSection(doc, viewFamilyTypeId, sectionBox)
        transaction.Commit()
        return newSection
    except Exception as e:
        transaction.RollBack()
        transaction.Dispose()
        print(e)


def main():
    # Get selection
    sel = get_selection()

    # Check selected elements
    if not sel:
        forms.alert("Please, select wall", "Section For Wall")
        sys.exit()
    for element in sel:
        if doc.GetElement(element).Category.Id.ToString() != "-2000011":
            forms.alert("Please, select only wall(s)","Section For Wall")
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

    viewFamilyTypeId = res[options].Id
    
    #Make section(s)
    if len(sel) == 1:
        create_section_by_wall(sel[0], doc, viewFamilyTypeId, transaction, sw["Flip section"])
    elif len(sel) > 1:
        transaction_group.Start("Create multiple sections")
        for el in sel:
            create_section_by_wall(el, doc, viewFamilyTypeId, transaction, sw["Flip section"])
        transaction_group.Assimilate()

if __name__ == '__main__':
    main()