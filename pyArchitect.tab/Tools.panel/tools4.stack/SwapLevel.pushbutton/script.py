# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Send the selection to another level without moving it up or down.

The offset arithmetic and the level test that makes this work live in
``tools.levels``; this script is the ribbon command around it, in the order the
work happens: take the elements first, then ask which level they should go to.

The selection comes from whatever is already selected, or from PickObjects when
nothing is.  Either way it is narrowed to elements that have a level of their
own, so materials, family types, grids and the like never reach the transaction
and never appear in the report as skips.
"""

import traceback

from pyrevit import forms

from core.selectionhelpers import get_selection_basic
from tools.levels import (
    LevelBasedElementFilter,
    S,
    change_levels,
    collect_levels,
    format_level_label,
    format_summary,
    split_selection,
)


doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument


def get_elements():
    """Return the elements to re-level, or None if there is nothing to do.

    Picking comes first, so the level list is asked for once the user has
    already said which objects are in play.

    Returns:
        (list): the ElementIds to re-level, or None when none qualify.
    """
    element_ids = get_selection_basic(uidoc, LevelBasedElementFilter())
    if not element_ids or element_ids.Count == 0:
        forms.alert(S("done.no_selection"), title=S("transaction"))
        return None

    usable, ignored = split_selection(doc, element_ids)
    if not usable:
        forms.alert(S("done.none_selected"), title=S("transaction"))
        return None
    return usable, ignored


def pick_target_level():
    """Show the level picker and return the chosen level, or None if cancelled.

    Returns:
        (DB.Level): the level the user picked.
    """
    levels = collect_levels(doc)
    if not levels:
        forms.alert(S("dialog.no_levels"), title=S("dialog.title"))
        return None

    labels = [format_level_label(level) for level in levels]
    chosen = forms.SelectFromList.show(
        labels,
        title=S("dialog.title"),
        button_name=S("dialog.button"),
    )
    if not chosen:
        return None
    return levels[labels.index(chosen)]


def main():
    """Run one re-leveling pass over the selection and report the outcome."""
    selection = get_elements()
    if selection is None:
        return
    element_ids, ignored = selection

    target_level = pick_target_level()
    if target_level is None:
        return

    result = change_levels(doc, target_level, element_ids)
    forms.alert(
        format_summary(result, target_level, ignored), title=S("transaction"))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(traceback.format_exc())
        forms.alert(S("done.failed", error), title=S("transaction"))
