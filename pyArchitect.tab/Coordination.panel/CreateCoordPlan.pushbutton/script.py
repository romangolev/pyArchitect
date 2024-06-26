# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

#__helpurl__ = ""

import Autodesk.Revit.DB as DB
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application

t = DB.Transaction(doc)


def get_viewtype(tr, a):
    floor_plans = [i for i in a.ToElements() if i.FamilyName == "Floor Plan"]
    for vft in a.ToElements():
        # Walkaround over an error while retrieving Name directly from ViewType
        params = vft.Parameters
        iterator = params.ForwardIterator()
        iterator.Reset()

        while iterator.MoveNext():
            try:
                if iterator.Current.Definition.Id.ToString() == "-1002001":
                    if iterator.Current.AsString() == "Coordination Plan":
                        return vft
            except:
                pass
    tr.Start("Create View Family Type")
    try:
        old_v = floor_plans[0]
        new_v = old_v.Duplicate("Coordination Plan")
        try:
            vft.DefaultTemplateId = 0
        except:
            pass
        tr.Commit()
        return new_v
    except:
        tr.RollBack()

def get_categoryID(cat):
    if cat == "BasePoint":
        collector = DB.Category\
            .GetCategory(doc, DB.BuiltInCategory.OST_ProjectBasePoint)
    elif cat == "SurveyPoint":
        collector = DB.Category\
            .GetCategory(doc, DB.BuiltInCategory.OST_SharedBasePoint)
    elif cat == "SitePoint":
        collector = DB.Category\
            .GetCategory(doc, DB.BuiltInCategory.OST_SitePoint)
    elif cat == "Site":
        collector = DB.Category\
            .GetCategory(doc, DB.BuiltInCategory.OST_Site)          
    else:
        pass
    return collector.Id

def make_active(a):
    uidoc.ActiveView = doc.GetElement(a.Id)
    pass

def find_coord(doc):
    coord_views = []
    elems = DB.FilteredElementCollector(doc).\
                OfCategory(DB.BuiltInCategory.OST_Views).\
                WhereElementIsNotElementType().ToElements()
    for elem in elems:
        if elem.ViewType == DB.ViewType.FloorPlan and elem.IsTemplate == False :
            if "Coordination Plan" in elem.Name:
                coord_views.append(elem)
    return coord_views

def create_coord_plan(doc, vft, lvl):
    elem = DB.ViewPlan.Create(doc, vft, lvl)
    par = elem.get_Parameter(DB.BuiltInParameter.VIEW_TEMPLATE)
    if par != None:
        par.Set(DB.ElementId.InvalidElementId)
    elem.DetailLevel = DB.ViewDetailLevel.Coarse
    elem.DisplayStyle = DB.DisplayStyle.Wireframe
    elem.Discipline = DB.ViewDiscipline.Coordination
    elem.Name = "Coordination Plan"
    elem.SetCategoryHidden(get_categoryID("Site"), False)
    elem.SetCategoryHidden(get_categoryID('BasePoint'), False)
    elem.SetCategoryHidden(get_categoryID('SurveyPoint'), False)
    #TODO Find out the category of Internal origin and turn it on
    #(Autodesk.Revit.DB.InternalOrigin.IsHidden(elem))
    #elem.SetCategoryHidden(get_categoryID('SitePoint'), False)

    #Change Crop View, Crop Region and Annotation Crop
    elem.AreAnnotationCategoriesHidden = False
    elem.CropBoxActive = False
    elem.CropBoxVisible = False
    ancrop = elem.get_Parameter(DB.BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE)
    ancrop.Set(0)

    #Change View range to unlimited
    vr = elem.GetViewRange()
    vr.SetLevelId(DB.PlanViewPlane.TopClipPlane, DB.PlanViewRange.Unlimited)
    vr.SetLevelId(DB.PlanViewPlane.BottomClipPlane, DB.PlanViewRange.Unlimited)
    vr.SetLevelId(DB.PlanViewPlane.ViewDepthPlane, DB.PlanViewRange.Unlimited)
    elem.SetViewRange(vr)
    return elem

def main():
    a = DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType)
    #Get viewtype and default level
    vf = get_viewtype(t, a)
    level = DB.FilteredElementCollector(doc)\
            .OfCategory(DB.BuiltInCategory.OST_Levels)\
            .WhereElementIsNotElementType().ToElements()[0]#.FirstOrDefault()
    #Find existing coorfination plans
    ex = find_coord(doc)
    if len(ex) == 0:
        t.Start("Create Coordination Plan")
        new_plan = create_coord_plan(doc, vf.Id, level.Id)
        t.Commit()
        make_active(new_plan)
    else:
        msg = """Existing Coordination plan(s) detected. Do you want to delete existing and create new one?"""
        ops = ['Delete old and create new','Keep existing']
        cfgs = {'option1': { 'background': '0xFF55FF'}} 
        options = forms.CommandSwitchWindow.show(ops,
            message=msg,
            config=cfgs,)
        if options == "Delete old and create new":
            #Create dummy view 
            try:

                t.Start("Create dummy plan")
                dummy = DB.ViewPlan.Create(doc, vf.Id, level.Id)
                t.Commit()
                make_active(dummy)
            except:
                t.RollBack()
                forms.alert("Error in creating dummy plan")

            # Create new Coord plan and delete old plans
            try:
                t.Start("Create Coordination Plan")
                for view in ex:
                    doc.Delete(view.Id)
                new_plan = create_coord_plan(doc, vf.Id, level.Id)
                t.Commit()
                make_active(new_plan)
            except:
                t.RollBack()
                forms.alert("Error in creating new coord plan")

            #Delete dummy plan
            try:
                t.Start("Delete dummy 3D view")
                doc.Delete(dummy.Id)
                t.Commit()
            except:
                t.RollBack()
                forms.alert("Error in deleting dummy")
        else:
            make_active(ex[0])


if __name__ == '__main__':
    main()
