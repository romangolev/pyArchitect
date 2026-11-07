# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

import Autodesk.Revit.DB as DB
from core.selectionhelpers import CustomISelectionFilterByIdInclude, ID_WALLS, \
    get_selection_basic
from core.unitsconverter import UnitConverter

doc = __revit__.ActiveUIDocument.Document           # type: ignore
uidoc = __revit__.ActiveUIDocument                  # type: ignore
uiapp = __revit__                                   # type: ignore


def is_solid(item):
    return isinstance(item, DB.Solid)


def element_volume(element):
    """Return the volume of `element` in m³, from its geometry when needed."""
    volume = element.get_Parameter(
        DB.BuiltInParameter.HOST_VOLUME_COMPUTED).AsDouble()
    if not volume:
        volume = sum(item.Volume for item in element.get_Geometry(DB.Options())
                     if is_solid(item))
    return UnitConverter.convertDoubleToM3(uiapp, volume)


def main():
    selection = get_selection_basic(
        uidoc, CustomISelectionFilterByIdInclude(ID_WALLS))
    volumes = []
    for item in selection:
        element = doc.GetElement(item)
        try:
            volume = element_volume(element)
        except Exception:
            print("Couldn't get the volume of element {}".format(element.Id))
            continue
        volumes.append(volume)
        print(volume)
    print("Summary : {}".format(sum(volumes)) + " m³")


if __name__ == '__main__':
    main()
