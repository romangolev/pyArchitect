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
    InstanceBinding,
    TypeBinding,
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


def get_binding_types(doc):
    """Map parameter NAME -> 'Type' / 'Instance' from the document's
    parameter bindings, matched back to shared parameters by name.

    Mirrors pyRevit's revit.db.query.iter_project_parameters pattern:
    ForwardIterator().Reset() + MoveNext(), binding via param_bindings[key].
    The BindingMap keys are Revit Definition objects (External or Internal
    Definition depending on version), so we do NOT read .GUID from them and
    do NOT filter by type -- we just key the result by the definition Name.
    Parameters not bound to any category won't appear here -> 'Unbound'.
    """
    info = {}
    if doc.IsFamilyDocument:
        # doc.ParameterBindings is not available in family documents.
        return info
    try:
        param_bindings = doc.ParameterBindings
    except Exception:
        return info
    try:
        pb_iterator = param_bindings.ForwardIterator()
        pb_iterator.Reset()
        while pb_iterator.MoveNext():
            try:
                key = pb_iterator.Key
                binding = param_bindings[key]
                name = key.Name
            except Exception:
                # fall back to Current if the indexer fails for this entry
                try:
                    binding = pb_iterator.Current
                    name = pb_iterator.Key.Name
                except Exception:
                    continue
            if isinstance(binding, InstanceBinding):
                info[name] = 'Instance'
            elif isinstance(binding, TypeBinding):
                info[name] = 'Type'
    except Exception:
        pass
    return info


def make_label(name, guid, type_info):
    tlabel = type_info.get(name, 'Unbound')
    return '{}  [{}]  ({})'.format(name, tlabel, str(guid))


def delete_params(doc, transaction, param_guids):
    transaction.Start("Delete Shared Parameters")
    try:
        deleted = 0
        for guid in param_guids:
            sParamElement = SharedParameterElement.Lookup(doc, guid)
            if sParamElement:
                doc.Delete(sParamElement.Id)
                deleted += 1
        transaction.Commit()
        return deleted
    except Exception:
        transaction.RollBack()
        raise


def confirm_delete(selected_names, shared_params, type_info):
    summary = '\n'.join(
        '- ' + make_label(name, shared_params[name], type_info)
        for name in selected_names
    )
    result = forms.alert(
        'The following {} shared parameter(s) will be completely removed '
        'from the project. This action cannot be undone.\n\n{}\n\n'
        'Do you want to continue?'.format(len(selected_names), summary),
        title='Delete Shared Parameters',
        cancel=True,
    )
    return result is not None


def main():
    shared_params = get_shared_parameters(doc)

    if not shared_params:
        forms.alert(
            'No shared parameters exist in the project.',
            title='No Shared Parameters'
        )
        sys.exit()

    type_info = get_binding_types(doc)

    # Diagnostic: if the document has shared parameters but we could not
    # resolve a single binding, surface how many bindings the map reports
    # so we can tell "genuinely unbound" from "iterator broken".
    if not type_info:
        try:
            map_size = doc.ParameterBindings.Size
        except Exception:
            map_size = '?'
        forms.alert(
            'Could not determine Type/Instance binding for any shared '
            'parameter (BindingMap size: {}). All parameters will be shown '
            'as [Unbound]. If your parameters are bound to categories, '
            'please report this number.'.format(map_size),
            title='Delete Shared Parameters - Diagnostic'
        )

    # Build a display label per parameter and a lookup back to its GUID/name.
    labels = []
    label_to_guid = {}
    label_to_name = {}
    for name in sorted(shared_params.keys()):
        guid = shared_params[name]
        label = make_label(name, guid, type_info)
        labels.append(label)
        label_to_guid[label] = guid
        label_to_name[label] = name

    # List form: SelectFromList with a checkbox per row, a search box and a
    # built-in "Toggle All" button. Tick the parameters one by one (or all at
    # once with Toggle All), then confirm.
    selected_labels = forms.SelectFromList.show(
        labels,
        title='Select Shared Parameters to Delete',
        multiselect=True,
        button_name='Confirm Selection',
    )

    if not selected_labels:
        sys.exit()

    selected_guids = [label_to_guid[label] for label in selected_labels]
    selected_names = [label_to_name[label] for label in selected_labels]

    if not confirm_delete(selected_names, shared_params, type_info):
        sys.exit()

    deleted = delete_params(doc, transaction, selected_guids)

    forms.alert(
        'Deleted {} shared parameter(s).'.format(deleted),
        title='Delete Shared Parameters'
    )


if __name__ == '__main__':
    main()