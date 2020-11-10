# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev 
# Blank Architects

#TODO:Create Shared Parameter of there is no such parameter in project

__doc__ = 'Создаёт разрез для выбранных стен. /Make Section based on seleccted walls.'
__author__ = 'Roman Golev'
__title__ = "Создать\nРазрез"

#Load Revit API
import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import DisplayUnitType, UnitUtils, FilteredElementCollector, ViewFamilyType, BuiltInParameter, XYZ, Transform, BoundingBoxXYZ, ViewSection
from collections import namedtuple
#import revitpythonwrapper by guitalarico 
import rpw
from rpw import doc, uidoc, DB, UI, db, ui
from rpw.ui.forms import (FlexForm, Label, ComboBox, TextBox, TextBox, Separator, Button, CheckBox)

def units(mmToFeets):
	dut = DisplayUnitType.DUT_MILLIMETERS
	return UnitUtils.ConvertToInternalUnits(mmToFeets, dut)

# wall selection
walls = ui.Selection().get_elements(wrapped=False)
if not walls:
    UI.TaskDialog.Show('Развёртка стен', 'Для создания развёртки необходимо выделяить как минимум одну стену.')
    sys.exit()

#Get sec_types
sec_types = []
#sec_types = rpw.db.Collector(of_category='OST_Walls', is_type=True).get_elements(wrapped=False)
view_types = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
for types in view_types :
    #if types.ViewFamily.ToString() == "Section" or types.ViewFamily.ToString() == "Detail":
    if types.ViewFamily.ToString() == "Section":
        sec_types.append(types)

#Select section type
sec_type_options = {DB.Element.Name.GetValue(t): t for t in sec_types}

components = [Label('Выберите тип разреза:'),
              ComboBox('s_type', sec_type_options),
              Label('Введите привязку разреза, мм'),
              Label('(по умолчанию 50мм):'),
              TextBox('s_offset', sec_offset="50.0"),
              CheckBox('flip', 'Развернуть разрез на 180'),
              Button('Start')]
form = FlexForm('Создать развёртку стены',components)
form.show()

# user offset (crop region = far clip)
if form.values['s_offset'] != "":
    offset = units(float(form.values['s_offset']))
else:
    offset = units(50)

viewFamilyTypeId = form.values['s_type'].Id

def builtInParam(wallParam):
    return units(float(wall.get_Parameter(wallParam).AsValueString()))

if form.values['flip'] == False:
    newSections = []
    for wall in walls:
        # Determine section box
        lc = wall.Location
        line = lc.Curve

        p = line.GetEndPoint(0)
        q = line.GetEndPoint(1)
        v = q - p

        bb = wall.get_BoundingBox(None)
        minZ = bb.Min.Z
        maxZ = bb.Max.Z

        w = v.GetLength()
        h = maxZ - minZ
        d = wall.WallType.Width
        wallBaseOffset = builtInParam(BuiltInParameter.WALL_BASE_OFFSET)
        wallUnconnectedHeight = builtInParam(BuiltInParameter.WALL_USER_HEIGHT_PARAM)

        # XYZ(min/max section line length, min/max height of the section box, min/max far clip)
        min = XYZ(-0.5*w - offset, wallBaseOffset - offset, - offset - 0.5*d)
        max = XYZ(0.5*w + offset, wallBaseOffset + wallUnconnectedHeight + offset, offset + 0.5*d)

        # factor for direction of section view
        if p.X > q.X or (p.X == q.X and p.Y < q.Y): fc = 1
        else: fc = -1

        midpoint = p + 0.5*v
        walldir = fc*v.Normalize()
        up = XYZ.BasisZ
        viewdir = walldir.CrossProduct(up)

        t = Transform.Identity
        t.Origin = midpoint
        t.BasisX = walldir
        t.BasisY = up
        t.BasisZ = viewdir

        sectionBox = BoundingBoxXYZ()
        sectionBox.Transform = t
        sectionBox.Min = min # scope box bottom
        sectionBox.Max = max # scope box top

        with db.Transaction('Create Section'):
            # Create wall section view
            newSection = ViewSection.CreateSection(doc, viewFamilyTypeId, sectionBox)
            newSections.append(newSection)
else:
    newSections = []
    for wall in walls:
        # Determine section box
        lc = wall.Location
        line = lc.Curve

        p = line.GetEndPoint(0)
        q = line.GetEndPoint(1)
        v = p - q

        bb = wall.get_BoundingBox(None)
        minZ = bb.Min.Z
        maxZ = bb.Max.Z

        w = v.GetLength()
        h = maxZ - minZ
        d = wall.WallType.Width
        wallBaseOffset = builtInParam(BuiltInParameter.WALL_BASE_OFFSET)
        wallUnconnectedHeight = builtInParam(BuiltInParameter.WALL_USER_HEIGHT_PARAM)

        # XYZ(min/max section line length, min/max height of the section box, min/max far clip)
        min = XYZ(-0.5*w - offset, wallBaseOffset - offset, - offset - 0.5*d)
        max = XYZ(0.5*w + offset, wallBaseOffset + wallUnconnectedHeight + offset, offset + 0.5*d)

        # factor for direction of section view
        if p.X > q.X or (p.X == q.X and p.Y < q.Y): fc = 1
        else: fc = -1

        midpoint = q + 0.5*v
        walldir = fc*v.Normalize()
        up = XYZ.BasisZ
        viewdir = walldir.CrossProduct(up)

        t = Transform.Identity
        t.Origin = midpoint
        t.BasisX = walldir
        t.BasisY = up
        t.BasisZ = viewdir

        sectionBox = BoundingBoxXYZ()
        sectionBox.Transform = t
        sectionBox.Min = min # scope box bottom
        sectionBox.Max = max # scope box top

        with db.Transaction('Create Section'):
            # Create wall section view
            newSection = ViewSection.CreateSection(doc, viewFamilyTypeId, sectionBox)
            newSections.append(newSection)



