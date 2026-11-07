# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

doc = __revit__.ActiveUIDocument.Document

categories = doc.Settings.Categories

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
