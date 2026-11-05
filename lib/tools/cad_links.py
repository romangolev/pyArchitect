# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Linked CAD files, grouped by format so that each format gets one workset.

Every linked DWG goes on ``##_DWG``, every DGN on ``##_DGN`` and so on.  A CAD
link placed in one view only lives on that view's workset and cannot be moved,
and an imported file is not a link at all, so both are left out.

A :class:`CadLinks` group answers the same questions as a Revit
:class:`tools.link_doctor.Link`, so the workset doctor plans it the same way.
"""

import os

import Autodesk.Revit.DB as DB

from core.selectionhelpers import id_value


class CadLinks(object):
    """The linked CAD files of one format, which share one workset.

    Attributes:
        file_name (str): the label shown in the fix list.
        target (str): the workset the group belongs on.
    """

    def __init__(self, extension, instances):
        self._instances = list(instances)
        self.file_name = u"*.{} ({})".format(extension.lower(),
                                             len(self._instances))
        self.target = u"##_{}".format(extension.upper())

    def elements(self):
        """Return the placed instances."""
        return list(self._instances)

    def element_ids(self):
        """Return the ids of the placed instances."""
        return set(id_value(instance.Id) for instance in self._instances)


def group_by_format(entries):
    """Group the movable CAD links by file format.

    Args:
        entries (list): ``(ImportInstance, type name)`` pairs.

    Returns:
        (list[CadLinks]): one group per format, sorted by workset name.
    """
    formats = {}
    for instance, type_name in entries:
        if not instance.IsLinked or instance.ViewSpecific:
            continue
        extension = os.path.splitext(type_name)[1].lstrip(u".").upper()
        formats.setdefault(extension, []).append(instance)
    groups = [CadLinks(extension, instances)
              for extension, instances in formats.items() if extension]
    return sorted(groups, key=lambda group: group.target)


def collect_cad_links(doc):
    """Return the linked CAD files of the project, one group per format."""
    instances = DB.FilteredElementCollector(doc) \
        .OfClass(DB.ImportInstance).ToElements()
    return group_by_format([(instance, _type_name(doc, instance))
                            for instance in instances])


def _type_name(doc, instance):
    link_type = doc.GetElement(instance.GetTypeId())
    param = link_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME) \
        if link_type is not None else None
    return (param.AsString() if param is not None else None) or u""
