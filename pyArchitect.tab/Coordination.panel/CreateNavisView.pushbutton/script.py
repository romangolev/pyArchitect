# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev
#__helpurl__ = ""

import Autodesk
import Autodesk.Revit.DB as DB

from pyrevit import forms
from pyrevit import HOST_APP
from Autodesk.Revit.ApplicationServices import LanguageType

doc = __revit__.ActiveUIDocument.Document # type: ignore
uidoc = __revit__.ActiveUIDocument # type: ignore
uiapp = __revit__ # type: ignore
app = uiapp.Application
t = DB.Transaction(doc)


def get3D_viewtype():
    collector3d = DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType).ToElements()
    for el in collector3d:
        if el.ViewFamily == DB.ViewFamily.ThreeDimensional:
            viewFamTypeId = el.Id
            return viewFamTypeId
        else:
            pass

def get_categoryID(cat):
    if cat == "OST_PipeCurves":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PipeCurves)
    elif cat == "OST_PipeSegments":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PipeSegments)
    elif cat == "OST_PlaceHolderPipes":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PlaceHolderPipes)
    elif cat == "OST_PipeInsulations":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PipeInsulations)
    elif cat == "OST_PipeFitting":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PipeFitting)
    elif cat == "OST_PipeAccessory":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PipeAccessory)
    elif cat == "OST_MechanicalEquipment":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_MechanicalEquipment)
    elif cat == "OST_DuctTerminal":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_DuctTerminal)
    elif cat == "OST_Lines":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Lines)
    elif cat == "OST_Walls":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Walls)
    elif cat == "OST_CurtainWallPanels":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_CurtainWallPanels)    
    elif cat == "OST_PlumbingFixtures":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_PlumbingFixtures)   
    elif cat == "OST_StructConnectionSymbols":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_StructConnectionSymbols)   
    elif cat == "OST_DuctAccessory":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_DuctAccessory)   
    elif cat == "OST_FlexPipeCurves":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_FlexPipeCurves)   
    elif cat == "OST_FlexDuctCurves":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_FlexDuctCurves)
    elif cat == "OST_ConduitFitting":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_ConduitFitting)  
    elif cat == "OST_Conduit":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Conduit)  
    elif cat == "OST_LightingFixtures":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_LightingFixtures)
    elif cat == "OST_LightingDevices":
        collector = Autodesk.Revit.DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_LightingDevices)      
    else:
        pass
    return collector.Id


def make_active(a):
    uidoc.ActiveView = doc.GetElement(a.Id)
    pass

class NavisworksView:
    def __init__(self, Document):
        self.doc = Document

    def find_ex(self):
        navis3ds=[]
        elems = Autodesk.Revit.DB.FilteredElementCollector(doc).\
                OfCategory(Autodesk.Revit.DB.BuiltInCategory.OST_Views).\
                WhereElementIsNotElementType().ToElements()
        for elem in elems:
            if elem.ViewType == DB.ViewType.ThreeD and elem.IsTemplate == False:
                if "Navis" in elem.Name:
                    navis3ds.append(elem)
                elif "navis" in elem.Name:
                    navis3ds.append(elem)
            else:
                pass
        return navis3ds

    def create3D(self,option1):
        view3d = Autodesk.Revit.DB.View3D.CreateIsometric(doc, get3D_viewtype())
        try:
            view3d.Name = "Navisworks"

            #Remove view template
            par = view3d.get_Parameter(DB.BuiltInParameter.VIEW_TEMPLATE)
            if par != None:
                par.Set(DB.ElementId.InvalidElementId)

            #Hide all annotations, import, point clouds on view
            view3d.AreAnnotationCategoriesHidden = True
            view3d.AreImportCategoriesHidden = True
            view3d.ArePointCloudsHidden = True
            #Changes Display Style to "FlatColors" of new Navis view
            view3d.DisplayStyle = DB.DisplayStyle.FlatColors

            #Change detail level for view
            view3d.DetailLevel = DB.ViewDetailLevel.Medium

            #Change override DetailLevel for High
            ovg_high = Autodesk.Revit.DB.OverrideGraphicSettings()
            ovg_high.SetDetailLevel(DB.ViewDetailLevel.Fine)
            view3d.SetCategoryOverrides(get_categoryID("OST_PipeCurves"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_PipeAccessory"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_PipeInsulations"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_PipeFitting"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_PlaceHolderPipes"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_MechanicalEquipment"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_DuctTerminal"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_PlumbingFixtures"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_DuctAccessory"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_FlexPipeCurves"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_FlexDuctCurves"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_LightingFixtures"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_LightingDevices"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_Conduit"), ovg_high)
            view3d.SetCategoryOverrides(get_categoryID("OST_ConduitFitting"), ovg_high)

            #Change override — Hide specific category 
            view3d.SetCategoryHidden(get_categoryID("OST_Lines"), True) 

            # Make wall and Curtain walls half-transparent
            transp = Autodesk.Revit.DB.OverrideGraphicSettings()
            transp.SetSurfaceTransparency(50)
            view3d.SetCategoryOverrides(get_categoryID("OST_Walls"), transp)
            view3d.SetCategoryOverrides(get_categoryID("OST_CurtainWallPanels"), transp)

            #TODO:Hide a sub-category "Symbol" for Structural Connections discipline
            #TODO:Hide a sub-category "Center line" for Ducts category
            #TODO:Hide a sub-category "Center line" for Pipes category
            #TODO: Make it work for all languages
            
            if HOST_APP.language == LanguageType.English_USA:
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_DuctCurves).SubCategories.get_Item("Center line").Id, True)
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_PipeCurves).SubCategories.get_Item("Center Line").Id, True)
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_StructConnections).SubCategories.get_Item("Symbol").Id, True)
            elif HOST_APP.language == LanguageType.Russian:
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_DuctCurves).SubCategories.get_Item("Осевая линия").Id, True)
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_PipeCurves).SubCategories.get_Item("Осевая линия").Id, True)
                view3d.SetCategoryHidden(doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_StructConnections).SubCategories.get_Item("Обозначение").Id, True)              
            else:
                print("Hide a sub-category 'Symbol' for Structural Connections discipline error")
                print("Hide a sub-category 'Center line' for Ducts category error")
                print("Hide a sub-category 'Center Line' for Pipes category")

            #Hide links options
            if option1 == 1:
                try:
                    view3d.HideElements(self.collect_links())
                except:
                    pass
            else:
                pass
            return view3d
        except:
            return 'Error in creating 3D View'

    def create_default3D(self):
        view3d = Autodesk.Revit.DB.View3D.CreateIsometric(doc, get3D_viewtype())
        return view3d

    def collect_links(self):
        #links = []
        cl = DB.FilteredElementCollector(doc) \
                .OfCategory(DB.BuiltInCategory.OST_RvtLinks) \
                .ToElementIds()
        return cl




def main():
    nwex = NavisworksView(doc).find_ex()
    #links_on = 0
    if __shiftclick__: # type: ignore
        links_on = 0
    else :
        links_on = 1

    if nwex == []:
        t.Start("Create Navis View")
        try:
            nwnew = NavisworksView(doc).create3D(links_on)
            t.Commit()
            make_active(nwnew)
        except:
            t.RollBack()
            forms.alert("Error")
        

    elif nwex != []:
        msg = """Existing Navisworks view detected. Do you want to delete existing and create new one?"""
        ops = ['Delete all and create new View','Keep existing and open it']
        cfgs = {'option1': { 'background': '0xFF55FF'}}
        options = forms.CommandSwitchWindow.show(ops,
            message=msg,
            config=cfgs,)
        if options == "Delete all and create new View":

            #Create Default 3D
            try:
                t.Start("Create dummy 3D view")
                def3D = NavisworksView(doc).create_default3D()
                t.Commit()
            except:
                t.RollBack()
                forms.alert("Error")
            make_active(def3D)

            #Delete all existing Navis views and create new
            try:
                t.Start("Delete Existing 'Navis' views")
                for el_nw in nwex:
                    doc.Delete(el_nw.Id)
                nwnew = NavisworksView(doc).create3D(links_on)
                t.Commit()
            except:
                t.RollBack()
                forms.alert("Error")
            make_active(nwnew)

            #Delete dummy 3d view
            try:
                t.Start("Delete dummy 3D view")
                doc.Delete(def3D.Id)
                t.Commit()
            except:
                t.RollBack()
                forms.alert("Error")
        elif options == "Keep existing and open it":
            try:
                make_active(nwex[0])
            except:
                pass
            pass

if __name__ == '__main__':
    main()
