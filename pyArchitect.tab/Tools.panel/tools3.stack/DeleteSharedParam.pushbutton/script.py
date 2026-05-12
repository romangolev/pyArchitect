# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import sys

import clr
clr.AddReference("RevitAPI")
clr.AddReference('System')

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    SharedParameterElement,
    Transaction,
)
from pyrevit import forms

doc = __revit__.ActiveUIDocument.Document
transaction = Transaction(doc)

def get_shared_parameters(doc):
    collector = FilteredElementCollector(doc) \
        .WhereElementIsNotElementType() \
        .OfClass(SharedParameterElement) \
        .ToElements()
    return {param.Name: param.GuidValue for param in collector}

def delete_all_shared_params(doc, transaction):
    transaction.Start("Delete All Shared Parameters")
    collector = FilteredElementCollector(doc) \
        .WhereElementIsNotElementType() \
        .OfClass(SharedParameterElement) \
        .ToElements()
    for param in collector:
        doc.Delete(param.Id)
    transaction.Commit()

def delete_single_param(doc, transaction, param_name, param_guid):
    transaction.Start("Delete Shared Parameter")
    sParamElement = SharedParameterElement.Lookup(doc, param_guid)
    doc.Delete(sParamElement.Id)
    transaction.Commit()

def main():
    shared_params = get_shared_parameters(doc)

    if not shared_params:
        forms.alert(
            'No shared parameters exist in the project.',
            title='No Shared Parameters'
        )
        sys.exit()

    options = ['All'] + list(shared_params.keys())
    choose = forms.CommandSwitchWindow.show(options, message='Select Option')

    if choose is None:
        sys.exit()
    elif choose == 'All':
        result = forms.alert(
            'This will delete ALL shared parameters completely from the '
            'project. This action cannot be undone. Are you sure you want '
            'to continue?',
            title='Delete All Shared Parameters',
            cancel=True
        )
        if result is None:
            sys.exit()
        delete_all_shared_params(doc, transaction)
    else:
        guid = shared_params[choose]
        result = forms.alert(
            'Delete parameter "{}" with GUID {}?'.format(choose, guid),
            title='Delete Shared Parameter',
            cancel=True
        )
        if result is None:
            sys.exit()
        delete_single_param(doc, transaction, choose, guid)

if __name__ == '__main__':
    main()