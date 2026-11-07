# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Join the geometry of two groups of elements where they really meet.

Only pairs that intersect are joined, so Revit never warns that joined elements
do not intersect, and nothing has to be unjoined afterwards.
"""

import Autodesk.Revit.DB as DB
from System.Collections.Generic import List

from core.selectionhelpers import id_value


def join_intersecting(doc, firsts, seconds):
    """Join every element of `firsts` with the elements of `seconds` it touches.

    Args:
        doc (DB.Document): the active document.
        firsts (list[DB.Element]): the first group.
        seconds (list[DB.Element]): the second group.

    Returns:
        (int): the number of pairs joined.
    """
    candidates = List[DB.ElementId]([second.Id for second in seconds])
    count = 0
    for first in firsts:
        for second in touching(doc, first, candidates):
            if id_value(second.Id) != id_value(first.Id) \
                    and join(doc, first, second):
                count += 1
    return count


def touching(doc, first, candidates):
    """Return the elements among the `candidates` ids that intersect `first`."""
    if not candidates.Count:
        return []
    return DB.FilteredElementCollector(doc, candidates) \
        .WherePasses(DB.ElementIntersectsElementFilter(first)).ToElements()


def join(doc, first, second):
    """Join two elements unless they are joined already; True when joined."""
    try:
        if DB.JoinGeometryUtils.AreElementsJoined(doc, first, second):
            return False
        DB.JoinGeometryUtils.JoinGeometry(doc, first, second)
        return True
    except Exception:
        return False
