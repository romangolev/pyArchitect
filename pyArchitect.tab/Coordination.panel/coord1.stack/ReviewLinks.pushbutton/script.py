# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Diagnose the links of the project and fix them.

The checks and the fixes live in ``tools.link_doctor``; this script is the
ribbon command around them: diagnose, apply, report.  A click applies every
fix; a Shift+click shows them in a list first, all ticked, and applies only
the ones still ticked.
"""

import traceback

from pyrevit import forms

from tools.link_doctor import S, apply_fixes, diagnose, format_summary


doc = __revit__.ActiveUIDocument.Document


def pick_fixes(fixes):
    """Show every fix ticked and return the ones the user kept.

    Returns:
        (list): the chosen fixes, or None when the dialog was cancelled.
    """
    items = [forms.TemplateListItem(fix, checked=True, name_attr="label")
             for fix in fixes]
    return forms.SelectFromList.show(
        items,
        title=S("title"),
        button_name=S("dialog.button"),
        multiselect=True,
        width=800,
    )


def main(manual):
    """Run one diagnose-and-fix pass over the links of the active document.

    Args:
        manual (bool): ask which fixes to apply instead of applying them all.
    """
    fixes, undeletable = diagnose(doc)
    if not fixes:
        message = S("done.healthy")
        if undeletable:
            message = format_summary(None, undeletable)
        forms.alert(message, title=S("title"))
        return

    if manual:
        fixes = pick_fixes(fixes)
        if not fixes:
            return

    result = apply_fixes(doc, fixes)
    forms.alert(format_summary(result, undeletable), title=S("title"))


if __name__ == '__main__':
    try:
        main(__shiftclick__)
    except Exception as error:
        print(traceback.format_exc())
        forms.alert(S("done.failed", error), title=S("title"))
