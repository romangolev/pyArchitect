# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev
# Reference information:
#(https://forums.autodesk.com/t5/revit-api-forum/hide-unhide-revitlinkinstance-in-visibility-settings/td-p/8194955)

__doc__ = """Создаёт координационный план. /Creates Coordination Plan.

Creates new Coordination Plan based on the selected plan\
(Reveals Base Point, Survey Point and Internal Origin) \

Shift+Click\
Reveals Base Point in active view
---------------------------------------------------------------------

Создаёт новый план координации  \

Shift+Click\
Показывает базовую точку на выбранном виде
"""
__author__ = 'Roman Golev'
__title__ = "Create Coord\nPlan"
#__helpurl__ = ""

import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *

clr.AddReference('System')
clr.AddReference('RevitAPIUI')
import pyrevit
from pyrevit import forms

import sys
import string
import random

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def get_plan_viewtype():
    collector = Autodesk.Revit.DB.FilteredElementCollector(doc).OfClass(Autodesk.Revit.DB.ViewFamilyType).ToElements()
    print(collector)
    for el in collector:
        if el.ViewFamily == ViewFamily.FloorPlan:
            viewFamTypeId = el.Id
            return viewFamTypeId
        else:
            0

def get_selected_elements():
    """Return Selected Elements as a list[]. Returns empty list if no elements are selected.
    Usage:
    - Select 1 or more elements
    > selected_elements = get_selected_elements()
    > [<Autodesk.Revit.DB.FamilyInstance object at 0x0000000000000034 [Autodesk.Revit.DB.FamilyInstance]>]
    """
    selection = uidoc.Selection
    selection_ids = selection.GetElementIds()
    elements = []
    for element_id in selection_ids:
        elements.append(doc.GetElement(element_id))
    return elements

def get_categoryID(cat):
    if cat == "BasePoint":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc,BuiltInCategory.OST_ProjectBasePoint)
    elif cat == "SurveyPoint":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc,BuiltInCategory.OST_SharedBasePoint)
    elif cat == "SitePoint":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc,BuiltInCategory.OST_SitePoint)
    elif cat == "Site":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc,BuiltInCategory.OST_Site)          
    else:
        pass
    return collector.Id

def make_active(a):
    uidoc.ActiveView = doc.GetElement(a.Id)
    pass

class plan:
    def __init__(self, Document):
        self.doc = Document

    def create_plan(self):
        newview = Autodesk.Revit.DB.ViewPlan.CreateAreaPlan(doc, areaSchemeId, levelId)
        return newview

    def duplicate_selected(self,view):
        duplicate = view.Duplicate(ViewDuplicateOption.Duplicate)
        return duplicate

    def check_selected(self,selection):
        if selection.count == 1:
            return True
        else:
            return False

    def collect_links(self):
        cl = Autodesk.Revit.DB.FilteredElementCollector(doc) \
                .OfCategory(BuiltInCategory.OST_RvtLinks) \
                .ToElementIds()
        return cl

    def adjust(self,view):
        elem = doc.GetElement(view)
        par = elem.get_Parameter(BuiltInParameter.VIEW_TEMPLATE)
        if par != None:
            par.Set(ElementId.InvalidElementId)
        elem.DetailLevel = ViewDetailLevel.Coarse
        elem.DisplayStyle = DisplayStyle.Wireframe
        elem.Discipline = ViewDiscipline.Coordination
        try:
            elem.Name = "Coordination Plan"
        except: 
            pass
        if elem.Name != "Coordination Plan":
            try:
                elem.Name = "Coordination Plan "  + id_generator()
            except:
                pyrevit.forms.alert("Naming Error")
                t.RollBack()
                sys.exit()
        else:
            pass
        elem.SetCategoryHidden(get_categoryID("Site"), False)
        elem.SetCategoryHidden(get_categoryID('BasePoint'), False)
        elem.SetCategoryHidden(get_categoryID('SurveyPoint'), False)
        #TODO Find out the category of Internal origin and turn it on
        #(Autodesk.Revit.DB.InternalOrigin.IsHidden(elem))
        #elem.SetCategoryHidden(get_categoryID('SitePoint'), False)
        #TODO Change view Type (###_CoordPlan)

        #Change Crop View, Crop Region and Annotation Crop
        elem.AreAnnotationCategoriesHidden = False
        elem.CropBoxActive = False
        elem.CropBoxVisible = False
        ancrop = elem.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE)
        ancrop.Set(0)

        #Change View range to unlimited
        vr = elem.GetViewRange()
        vr.SetLevelId(PlanViewPlane.TopClipPlane,PlanViewRange.Unlimited)
        vr.SetLevelId(PlanViewPlane.BottomClipPlane,PlanViewRange.Unlimited)
        vr.SetLevelId(PlanViewPlane.ViewDepthPlane,PlanViewRange.Unlimited)
        elem.SetViewRange(vr)

        return view

def main():
    if __shiftclick__:
        pass
    else :
        selected = get_selected_elements()
        if len(selected) == 1:
            if selected[0].GetType().ToString() ==  'Autodesk.Revit.DB.ViewPlan' :
                #print('WE HAVE A PLAN')
                t.Start("Create Coordination Plan")
                copied_plan = plan(doc).duplicate_selected(selected[0])
                plan(doc).adjust(copied_plan)
                t.Commit()
                uidoc.ActiveView = doc.GetElement(copied_plan)
                #TODO Implement Zoom To Fit or Focus on Base Point
                #Autodesk.Revit.UI.UIView.ZoomToFit()
                # for uv in uidoc.GetOpenUIViews():
                #     if uv.ViewId.Equals(copied_plan):
                #         uiview = uv
                #         break
                # uiview.ZoomToFit()
                #uidoc.ShowElements("Base point <Element>")
            else:
                print('You need to select a plan view in Project Browser')
        elif len(selected) >= 1:
            pyrevit.forms.alert("You need to select only 1 plan in Project Browser")
        elif len(selected) <= 1:
            pyrevit.forms.alert("You need to select a plan view in Project Browser")
        else:
            pyrevit.forms.alert("Error")
     
if __name__ == '__main__':
    main()
