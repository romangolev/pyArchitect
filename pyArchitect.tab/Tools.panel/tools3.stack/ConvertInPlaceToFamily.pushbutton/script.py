# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Turn the displayed solid geometry of a model-in-place component into an RFA.

Revit exposes model-in-place families through the project document only; unlike
loadable families they cannot be opened with Document.EditFamily(). Therefore
there is no API operation that preserves the original feature tree. This tool
captures the resulting solids as FreeFormElements in a new family document.
"""

import os
import traceback

import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI.Selection import ISelectionFilter, ObjectType
from pyrevit import forms, script


doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application
output = script.get_output()

EPSILON = 0.0000001


def log(message):
    """Write a diagnostic line to pyRevit's output window."""
    print('[Convert In-Place to Family] {}'.format(message))


def log_exception(error):
    """Keep the dialog short but emit the complete failure details to output."""
    log('ERROR: {}'.format(error))
    print(traceback.format_exc())


def element_name(element, fallback='<unnamed>'):
    """Return Element.Name without letting IronPython's API binding abort us."""
    try:
        name = element.Name
        if name:
            return name
    except Exception:
        pass
    return fallback


def source_family_name(component):
    """FamilySymbol.FamilyName works for in-place families in Revit 2026."""
    try:
        name = component.Symbol.FamilyName
        if name:
            return name
    except Exception:
        pass
    parameter = component.Symbol.get_Parameter(
        DB.BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM)
    if parameter and parameter.AsString():
        return parameter.AsString()
    return element_name(component.Symbol, 'In-Place Family')


def family_name_from_family(family):
    """Resolve names through FamilySymbol; Family.Name is absent for some API types."""
    try:
        for symbol_id in family.GetFamilySymbolIds():
            symbol = doc.GetElement(symbol_id)
            if symbol and symbol.FamilyName:
                return symbol.FamilyName
    except Exception:
        pass
    return element_name(family)


class InPlaceFamilyFilter(ISelectionFilter):
    """Limits PickObject to model-in-place FamilyInstances."""

    def AllowElement(self, element):
        try:
            return isinstance(element, DB.FamilyInstance) \
                and element.Symbol.Family.IsInPlace
        except Exception:
            return False

    def AllowReference(self, reference, position):
        return False


class ReloadFamilyOptions(DB.IFamilyLoadOptions):
    """Reload our just-created family without showing a Revit prompt."""

    def OnFamilyFound(self, family_in_use, overwrite_parameter_values):
        overwrite_parameter_values.Value = False
        return True

    def OnSharedFamilyFound(self, shared_family, family_in_use, source,
                            overwrite_parameter_values):
        source.Value = DB.FamilySource.Family
        overwrite_parameter_values.Value = False
        return True


def selected_in_place_component():
    """Return exactly one selected/picked in-place component, or None."""
    selected_ids = uidoc.Selection.GetElementIds()
    if selected_ids.Count == 1:
        candidate = doc.GetElement(list(selected_ids)[0])
        if InPlaceFamilyFilter().AllowElement(candidate):
            log('Using selected in-place component: {} ({})'.format(
                candidate.Name, candidate.Id))
            return candidate

    try:
        reference = uidoc.Selection.PickObject(
            ObjectType.Element,
            InPlaceFamilyFilter(),
            'Select one model-in-place component to convert')
        candidate = doc.GetElement(reference.ElementId)
        log('Using picked in-place component: {} ({})'.format(
            candidate.Name, candidate.Id))
        return candidate
    except Exception as error:
        log('Selection was cancelled or failed: {}'.format(error))
        return None


def family_name_exists(name):
    """An RFA file name must not collide with an already loaded family."""
    names = set(family_name_from_family(family) for family in
                DB.FilteredElementCollector(doc).OfClass(DB.Family))
    return name in names


def safe_file_stem(name):
    """Make a family name safe as the initial Save As file name."""
    invalid = '<>:"/\\|?*'
    return ''.join('_' if char in invalid else char for char in name).strip()


def get_anchor(component):
    """Return an origin that gives the replacement the same world placement."""
    try:
        return component.GetTransform().Origin
    except Exception:
        pass

    location = component.Location
    if isinstance(location, DB.LocationPoint):
        return location.Point
    if isinstance(location, DB.LocationCurve):
        return location.Curve.Evaluate(0.5, True)

    bounding_box = component.get_BoundingBox(None)
    if bounding_box:
        return (bounding_box.Min + bounding_box.Max) * 0.5
    return DB.XYZ.Zero


def transformed_solid(solid, transform):
    """Return a copied solid in project coordinates, or None for empty solids."""
    if not solid or solid.Volume <= EPSILON:
        return None
    try:
        return DB.SolidUtils.CreateTransformed(solid, transform)
    except Exception:
        # A top-level solid is already in project coordinates. Keeping it is
        # safer than discarding usable geometry because of an API transform bug.
        if transform.IsIdentity:
            return solid
        raise


def collect_solids(geometry, transform, solids):
    """Flatten nested GeometryInstances into solid geometry in project space."""
    if geometry is None:
        return

    for geometry_object in geometry:
        if isinstance(geometry_object, DB.Solid):
            project_solid = transformed_solid(geometry_object, transform)
            if project_solid:
                solids.append(project_solid)
        elif isinstance(geometry_object, DB.GeometryInstance):
            combined = transform.Multiply(geometry_object.Transform)
            collect_solids(geometry_object.GetSymbolGeometry(), combined, solids)


def source_solids(component):
    options = DB.Options()
    options.DetailLevel = DB.ViewDetailLevel.Fine
    options.IncludeNonVisibleObjects = False
    options.ComputeReferences = False

    solids = []
    collect_solids(component.get_Geometry(options), DB.Transform.Identity, solids)
    log('Extracted {} solid(s) from source element {}.'.format(
        len(solids), component.Id))
    return solids


def set_matching_category(family_doc, source_category):
    """Use the original category when the generic template permits it."""
    if source_category is None:
        return False
    try:
        target_category = DB.Category.GetCategory(family_doc, source_category.Id)
        if target_category is None:
            log('Original category is unavailable in the chosen template.')
            return False
        family_doc.OwnerFamily.FamilyCategory = target_category
        log('Set output family category to "{}".'.format(target_category.Name))
        return True
    except Exception as error:
        log('Could not assign source category: {}'.format(error))
        return False


def first_symbol(family):
    for symbol_id in family.GetFamilySymbolIds():
        return doc.GetElement(symbol_id)
    return None


def find_loaded_family(family_name):
    for family in DB.FilteredElementCollector(doc).OfClass(DB.Family):
        if family_name_from_family(family) == family_name:
            return family
    return None


def make_family(component, template_path, output_path, family_name, anchor):
    """Create, save, load, and return the new family's first symbol."""
    solids = source_solids(component)
    if not solids:
        raise ValueError('The selected component has no solid geometry to convert.')

    log('Creating family "{}" from template: {}'.format(
        family_name, template_path))
    family_doc = app.NewFamilyDocument(template_path)
    try:
        transaction = DB.Transaction(family_doc, 'Create loadable family')
        transaction.Start()
        try:
            same_category = set_matching_category(family_doc, component.Category)
            offset = DB.Transform.CreateTranslation(
                DB.XYZ(-anchor.X, -anchor.Y, -anchor.Z))
            converted = 0
            for solid in solids:
                local_solid = DB.SolidUtils.CreateTransformed(solid, offset)
                DB.FreeFormElement.Create(family_doc, local_solid)
                converted += 1

            log('Created {} FreeFormElement(s) in the family document.'.format(
                converted))

            # Reuse the selected type name where possible. The new family has
            # one type because each output RFA represents one source instance.
            source_type_name = element_name(component.Symbol, 'Type 1')
            for symbol_id in family_doc.OwnerFamily.GetFamilySymbolIds():
                try:
                    family_doc.GetElement(symbol_id).Name = source_type_name
                except Exception:
                    pass
                break

            transaction.Commit()
            log('Committed family geometry transaction.')
        except Exception:
            transaction.RollBack()
            raise

        save_options = DB.SaveAsOptions()
        # Never overwrite an existing RFA silently. A duplicate path aborts
        # before the source component can be touched.
        save_options.OverwriteExistingFile = False
        family_doc.SaveAs(output_path, save_options)
        log('Saved family RFA: {}'.format(output_path))

        # The document-to-document overload belongs to the source family
        # document; calling it on the project produces "family documents only".
        log('Loading family into project document...')
        if not family_doc.LoadFamily(doc, ReloadFamilyOptions()):
            raise RuntimeError('Revit did not load the newly created family.')

        loaded_family = find_loaded_family(family_name)
        symbol = first_symbol(loaded_family) if loaded_family else None
        if symbol is None:
            raise RuntimeError('The new family was loaded, but no type was found.')
        log('Loaded family "{}"; selected symbol {} ({}).'.format(
            family_name_from_family(loaded_family), element_name(symbol), symbol.Id))
        return symbol, converted, same_category
    finally:
        family_doc.Close(False)
        log('Closed temporary family document.')


def replace_component(source, symbol, anchor):
    """Place the RFA before deleting the source, so a failed placement is safe."""
    transaction = DB.Transaction(doc, 'Replace model-in-place with family')
    transaction.Start()
    try:
        log('Placing replacement at ({}, {}, {}).'.format(
            anchor.X, anchor.Y, anchor.Z))
        if not symbol.IsActive:
            symbol.Activate()
            doc.Regenerate()
            log('Activated symbol {}.'.format(symbol.Id))

        replacement = doc.Create.NewFamilyInstance(
            anchor, symbol, DB.Structure.StructuralType.NonStructural)
        log('Placed replacement instance {}. Deleting source {}...'.format(
            replacement.Id, source.Id))
        doc.Delete(source.Id)
        transaction.Commit()
        log('Committed replacement transaction.')
        return replacement
    except Exception as error:
        log('Replacement transaction failed; rolling back: {}'.format(error))
        transaction.RollBack()
        raise


def main():
    log('Starting conversion. Project: "{}". Revit: {}.'.format(
        doc.Title, app.VersionNumber))
    if doc.IsFamilyDocument:
        log('Stopped: active document is already a family document.')
        forms.alert('Run this command from a Revit project, not a family document.',
                    title='Convert In-Place to Family', warn_icon=True)
        return

    source = selected_in_place_component()
    if source is None:
        log('Stopped: no in-place component was selected.')
        forms.alert('Select one model-in-place component and run the command again.',
                    title='Convert In-Place to Family', warn_icon=True)
        return

    source_name = source_family_name(source)
    log('Source family: "{}"; type: "{}"; category: "{}".'.format(
        source_name, element_name(source.Symbol),
        source.Category.Name if source.Category else '<none>'))
    default_stem = safe_file_stem('{} Loadable'.format(source_name))
    template_path = forms.pick_file(file_ext='rft')
    if not template_path:
        log('Stopped: no family template selected.')
        return

    output_path = forms.save_file(file_ext='rfa', default_name=default_stem)
    if not output_path:
        log('Stopped: no destination RFA selected.')
        return

    requested_name = os.path.splitext(os.path.basename(output_path))[0]
    if family_name_exists(requested_name):
        log('Stopped: family name "{}" is already loaded.'.format(
            requested_name))
        forms.alert(
            'A family named "{}" is already loaded. Choose a new RFA file '
            'name and run the command again.'.format(requested_name),
            title='Convert In-Place to Family', warn_icon=True)
        return
    family_name = requested_name
    anchor = get_anchor(source)
    log('Output RFA: {}. Family name: "{}".'.format(output_path, family_name))
    log('Source anchor: ({}, {}, {}).'.format(anchor.X, anchor.Y, anchor.Z))

    message = (
        'Create a loadable family from "{}"?\n\n'
        'The new RFA will contain its final solid geometry as free-form solids. '
        'Sketches, parameters, constraints, void history, and per-face materials '
        'cannot be converted. The original is deleted only after the new family '
        'loads and is placed successfully.'
    ).format(source_name)
    if not forms.alert(message, title='Convert In-Place to Family', yes=True, no=True):
        log('Stopped: conversion was not confirmed.')
        return

    try:
        symbol, solid_count, same_category = make_family(
            source, template_path, output_path, family_name, anchor)
        replacement = replace_component(source, symbol, anchor)
    except Exception as error:
        log_exception(error)
        forms.alert(
            'The original model-in-place component was not deleted.\n\n{}\n\n'
            'Open the pyRevit output window for the complete diagnostic log.'
            .format(error),
            title='Convert In-Place to Family Failed', warn_icon=True)
        return

    category_note = ''
    if not same_category:
        category_note = (
            '\n\nThe chosen template could not use the original category, so '
            'the family remains in the template category.'
        )
    forms.alert(
        'Created and loaded "{}" with {} free-form solid(s).\n'
        'Replacement instance: {}\nRFA: {}{}'
        .format(family_name, solid_count, replacement.Id, output_path, category_note),
        title='Convert In-Place to Family')
    log('Conversion completed successfully.')


if __name__ == '__main__':
    main()
