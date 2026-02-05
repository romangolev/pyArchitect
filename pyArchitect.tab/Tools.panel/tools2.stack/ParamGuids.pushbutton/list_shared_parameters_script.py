# -*- coding: utf-8 -*-
# pylint: skip-file

import clr
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import FilteredElementCollector, SharedParameterElement

clr.AddReference('System')

from collections import OrderedDict

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
uiapp = __revit__
app = uiapp.Application

collector = FilteredElementCollector(doc).OfClass(SharedParameterElement).ToElements()

params_data = []
for param in collector:
    params_data.append([
        param.GuidValue.ToString(),
        param.Name,
        str(param.Id)
    ])

if params_data:
    from pyrevit import output
    out = output.get_output()
    columns = ['GUID', 'Parameter Name', 'Revit ID']
    sorted_data = sorted(params_data, key=lambda x: x[1])
    out.print_table(sorted_data, columns=columns, title='Shared Parameters')
else:
    print('No shared parameters found in the project')
