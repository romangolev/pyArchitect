# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import CategoryType

clr.AddReference('System')
clr.AddReference('RevitAPIUI')

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application
t = Autodesk.Revit.DB.Transaction(doc)


categories = doc.Settings.Categories
n = categories.Size

for c in categories:
    #print (c.Name, c.Id.IntegerValue, c.SubCategories.Size, c.CategoryType, c.AllowsBoundParameters )
    if c.SubCategories.Size != 0:
        print(c.SubCategories, c.SubCategories.Size)
        print(c.Name)
        print(c.CategoryType)
        print(c.Id)
        print('----------------------------------------------------------------')
        # for i in c.SubCategories:
        #     iterator = i.SubCategories.ForwardIterator()
        #     print(iterator, iterator.GetType())
        #     try:
        #         print(iterator.get_Current())
        #     except:
        #         pass
