# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Workset helpers shared by the link doctor and the workset doctor.

Both tools plan their repairs as :class:`Fix` objects and carry them out the
same way: every fix runs in a sub-transaction of its own, so a fix that cannot
be applied is rolled back and reported with a reason without undoing the
others.  The rename, move and delete handlers live here, together with the
reasons they give, so the two tools can never disagree on how a workset is
renamed, filled or deleted.
"""

import Autodesk.Revit.DB as DB

from core.localization import StringTable
from core.selectionhelpers import id_value


S = StringTable({
    "done.applied": {
        "en_us": u"Applied {} fix(es).",
        "ru": u"Применено исправлений: {}.",
        "es_es": u"Se aplicaron {} corrección(es).",
    },
    "done.skipped": {
        "en_us": u"Skipped {} fix(es):",
        "ru": u"Пропущено исправлений ({}):",
        "es_es": u"Se omitieron {} corrección(es):",
    },

    "skip.name_taken": {
        "en_us": u"the name is already taken",
        "ru": u"имя уже занято",
        "es_es": u"el nombre ya está en uso",
    },
    "skip.not_empty": {
        "en_us": u"it still holds {} element(s)",
        "ru": u"в нём ещё есть элементы ({})",
        "es_es": u"todavía contiene {} elemento(s)",
    },
    "skip.cannot_delete": {
        "en_us": u"Revit does not allow deleting it (active or not editable)",
        "ru": u"Revit не разрешает его удалить (активный или занят)",
        "es_es": u"Revit no permite eliminarlo (activo o no editable)",
    },
    "skip.read_only": {
        "en_us": u"its workset cannot be changed",
        "ru": u"рабочий набор нельзя изменить",
        "es_es": u"su subproyecto no se puede cambiar",
    },
    "skip.borrowed": {
        "en_us": u"another user is editing it",
        "ru": u"его редактирует другой пользователь",
        "es_es": u"otro usuario lo está editando",
    },
    "skip.revit_error": {
        "en_us": u"Revit refused the change: {}",
        "ru": u"Revit отклонил изменение: {}",
        "es_es": u"Revit rechazó el cambio: {}",
    },
})


LINK_WORKSET_PREFIX = u"##"


class Fix(object):
    """One repair the user can tick on or off.

    Attributes:
        kind (str): what the fix does, e.g. ``"rename"`` or ``"move"``.
        label (str): the line shown in the list.
        link (Link): the link it is about, or None.
        workset_id (DB.WorksetId): the workset renamed or deleted; for a move,
            the workset its rename would take over, if one was planned.
        name (str): the new name, the move target, or the workset deleted.
    """

    def __init__(self, kind, label, link=None, workset_id=None, name=None):
        self.kind = kind
        self.label = label
        self.link = link
        self.workset_id = workset_id
        self.name = name


class Result(object):
    """What a run of fixes did.

    Attributes:
        applied (list[str]): labels of the fixes carried out.
        skipped (list): ``(label, reason)`` pairs for fixes left alone.
    """

    def __init__(self):
        self.applied = []
        self.skipped = []

    def record(self, fix, reason):
        """File `fix` as applied when `reason` is None, as skipped otherwise."""
        if reason is None:
            self.applied.append(fix.label)
            return
        self.skipped.append((fix.label, reason))

    def lines(self):
        """Return the report lines for the applied and the skipped fixes."""
        lines = [S("done.applied", len(self.applied))]
        lines.extend(u"- {}".format(label) for label in self.applied)
        if self.skipped:
            lines.append(u"")
            lines.append(S("done.skipped", len(self.skipped)))
            lines.extend(u"- {}: {}".format(label, reason)
                         for label, reason in self.skipped)
        return lines


def is_link_workset(name):
    """True when the workset is named the way the doctors name link worksets."""
    return name.startswith(LINK_WORKSET_PREFIX)


def user_worksets(doc):
    """Return ``{workset id int: workset}`` for the user worksets."""
    worksets = DB.FilteredWorksetCollector(doc) \
        .OfKind(DB.WorksetKind.UserWorkset).ToWorksets()
    return dict((id_value(ws.Id), ws) for ws in worksets)


def workset_contents(doc, workset_id):
    """Return the ids of every element on a workset as ints."""
    return set(id_value(element_id) for element_id in
               DB.FilteredElementCollector(doc)
               .WherePasses(DB.ElementWorksetFilter(workset_id, False))
               .ToElementIds())


def find_workset(doc, name):
    """Return the user workset called `name`, or None."""
    for workset in user_worksets(doc).values():
        if workset.Name == name:
            return workset
    return None


def can_delete_worksets():
    """True when this Revit version can delete worksets.

    The API that deletes a workset arrived in Revit 2023, together with the
    settings that go with it.
    """
    return (hasattr(DB.WorksetTable, "DeleteWorkset")
            and hasattr(DB, "DeleteWorksetSettings")
            and hasattr(DB, "DeleteWorksetOption"))


def owned_by_others(doc, elements):
    """True when another user has borrowed one of `elements`."""
    if not doc.IsWorkshared:
        return False
    return any(DB.WorksharingUtils.GetCheckoutStatus(doc, e.Id)
               == DB.CheckoutStatus.OwnedByOtherUser for e in elements)


def apply_one(doc, fix, handler):
    """Run one fix in a sub-transaction that is rolled back if it is skipped.

    Returns:
        (str): None when the fix was applied, the reason it was skipped
        otherwise.
    """
    sub = DB.SubTransaction(doc)
    sub.Start()
    reason = S("skip.revit_error", u"")
    try:
        reason = handler(doc, fix)
    except Exception as error:
        reason = S("skip.revit_error", getattr(error, "Message", None) or error)
    finally:
        if reason is None:
            sub.Commit()
        else:
            sub.RollBack()
    return reason


def rename(doc, fix):
    """Rename ``fix.workset_id`` to ``fix.name``."""
    if not DB.WorksetTable.IsWorksetNameUnique(doc, fix.name):
        return S("skip.name_taken")
    DB.WorksetTable.RenameWorkset(doc, fix.workset_id, fix.name)
    return None


def move(doc, fix):
    """Put every element of ``fix.link`` on the workset ``fix.name``.

    The workset is created when it does not exist yet.
    """
    target = find_workset(doc, fix.name)
    to_move = [e for e in fix.link.elements()
               if target is None or id_value(e.WorksetId) != id_value(target.Id)]
    if owned_by_others(doc, to_move):
        return S("skip.borrowed")
    params = [e.get_Parameter(DB.BuiltInParameter.ELEM_PARTITION_PARAM)
              for e in to_move]
    if any(p is None or p.IsReadOnly for p in params):
        return S("skip.read_only")
    if target is None:
        target = DB.Workset.Create(doc, fix.name)
    target_id = id_value(target.Id)
    for param in params:
        param.Set(target_id)
    return None


def delete(doc, fix):
    """Delete ``fix.workset_id`` when it really holds no element any more."""
    if not can_delete_worksets():
        return S("skip.cannot_delete")
    remaining = workset_contents(doc, fix.workset_id)
    if remaining:
        return S("skip.not_empty", len(remaining))
    active = doc.GetWorksetTable().GetActiveWorksetId()
    settings = DB.DeleteWorksetSettings(
        DB.DeleteWorksetOption.MoveElementsToWorkset, active)
    if id_value(active) == id_value(fix.workset_id) \
            or not DB.WorksetTable.CanDeleteWorkset(doc, fix.workset_id, settings):
        return S("skip.cannot_delete")
    DB.WorksetTable.DeleteWorkset(doc, fix.workset_id, settings)
    return None
