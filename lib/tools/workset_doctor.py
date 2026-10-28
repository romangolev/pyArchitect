# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Diagnose and repair the worksets of a project.

The Review Links command (:mod:`tools.link_doctor`) looks at the links and at
the worksets they sit on.  This module looks at the worksets themselves: it
gives every linked file a workset of its own, keeps only one link per workset
and deletes the worksets that are left empty.

The default workset -- the one Revit calls ``Workset1`` -- is the odd one out.
Autodesk's documentation on deleting a workset states that it cannot be
deleted, only renamed, and the API follows: ``WorksetTable`` offers no way to
remove it.  So the script cleans it up instead of deleting it: the links
sitting on it are moved onto worksets of their own, and the workset is given
its proper name back.

This tool is the strict one.  It puts every link on the workset named after
its file, even when the team keeps its links on a shared workset of an older
convention, which the link doctor tolerates.  Both tools name a link's workset
the same way, so they agree on the result and neither undoes the other.

:func:`diagnose` turns everything it finds into a list of :class:`Fix` objects
without touching the model.  :func:`apply_fixes` runs the chosen fixes in one
transaction group, so a single undo reverts the whole run, and a fix that
cannot be carried out is skipped and listed without undoing the others.
"""

import Autodesk.Revit.DB as DB

from core.localization import StringTable
from core.selectionhelpers import id_value
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from tools.link_doctor import collect_links, file2ws_name


S = StringTable({
    "title": {
        "en_us": u"Workset Doctor",
        "ru": u"Доктор рабочих наборов",
        "es_es": u"Doctor de subproyectos",
    },
    "dialog.button": {
        "en_us": u"Apply selected fixes",
        "ru": u"Исправить выбранное",
        "es_es": u"Aplicar las correcciones seleccionadas",
    },

    "fix.move": {
        "en_us": u"Move '{}' from {} to '{}'",
        "ru": u"Перенести «{}» из {} в «{}»",
        "es_es": u"Mover '{}' de {} a '{}'",
    },
    "fix.rename": {
        "en_us": u"Rename workset '{}' to '{}' for '{}'",
        "ru": u"Переименовать рабочий набор «{}» в «{}» для «{}»",
        "es_es": u"Renombrar el subproyecto '{}' a '{}' para '{}'",
    },
    "fix.rename_default": {
        "en_us": u"Rename the default workset '{}' to '{}'",
        "ru": u"Переименовать рабочий набор по умолчанию «{}» в «{}»",
        "es_es": u"Renombrar el subproyecto predeterminado '{}' a '{}'",
    },
    "fix.delete_empty": {
        "en_us": u"Delete empty workset '{}'",
        "ru": u"Удалить пустой рабочий набор «{}»",
        "es_es": u"Eliminar el subproyecto vacío '{}'",
    },

    "tx.rename": {
        "en_us": u"Workset Doctor - rename worksets",
        "ru": u"Доктор рабочих наборов - переименование наборов",
        "es_es": u"Doctor de subproyectos - renombrar subproyectos",
    },
    "tx.move": {
        "en_us": u"Workset Doctor - move links",
        "ru": u"Доктор рабочих наборов - перенос связей",
        "es_es": u"Doctor de subproyectos - mover vínculos",
    },
    "tx.delete": {
        "en_us": u"Workset Doctor - delete worksets",
        "ru": u"Доктор рабочих наборов - удаление наборов",
        "es_es": u"Doctor de subproyectos - eliminar subproyectos",
    },

    "done.healthy": {
        "en_us": u"Every link has a workset of its own and no empty workset is "
                 u"left over. Nothing to fix.",
        "ru": u"У каждой связи есть свой рабочий набор, и пустых наборов не "
               u"осталось. Исправлять нечего.",
        "es_es": u"Cada vínculo tiene su propio subproyecto y no queda ningún "
                 u"subproyecto vacío. No hay nada que corregir.",
    },
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
    "done.no_delete_api": {
        "en_us": u"Empty worksets were found, but this Revit version cannot "
                 u"delete worksets: {}",
        "ru": u"Найдены пустые рабочие наборы, но эта версия Revit не умеет "
               u"удалять рабочие наборы: {}",
        "es_es": u"Se encontraron subproyectos vacíos, pero esta versión de "
                 u"Revit no puede eliminarlos: {}",
    },
    "done.default_kept": {
        "en_us": u"'{}' is the default workset. Revit does not allow deleting "
                 u"it, so it was cleaned up instead.",
        "ru": u"«{}» — рабочий набор по умолчанию. Revit не разрешает его "
               u"удалять, поэтому он был очищен.",
        "es_es": u"'{}' es el subproyecto predeterminado. Revit no permite "
                 u"eliminarlo, por lo que se ha limpiado.",
    },
    "done.failed": {
        "en_us": u"Workset Doctor could not finish:\n{}",
        "ru": u"Доктор рабочих наборов не смог завершить работу:\n{}",
        "es_es": u"El doctor de subproyectos no pudo terminar:\n{}",
    },
    "done.not_workshared": {
        "en_us": u"The file is not workshared, so it has no worksets to review.",
        "ru": u"Файл не является совместным, поэтому в нём нет рабочих "
               u"наборов для проверки.",
        "es_es": u"El archivo no es compartido, por lo que no tiene subproyectos "
                 u"que revisar.",
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
    "skip.no_target": {
        "en_us": u"the workset '{}' could not be created",
        "ru": u"не удалось создать рабочий набор «{}»",
        "es_es": u"no se pudo crear el subproyecto '{}'",
    },
    "skip.revit_error": {
        "en_us": u"Revit refused the change: {}",
        "ru": u"Revit отклонил изменение: {}",
        "es_es": u"Revit rechazó el cambio: {}",
    },
})


DEFAULT_WORKSET_NAME = u"Workset1"

KIND_RENAME = "rename"
KIND_MOVE = "move"
KIND_DELETE = "delete"

# The renames run first: they give a workset the name a link is after and free
# the name it had.  The moves run after them, so a link moves onto a workset
# that already carries its name, and the deletions run last, so a workset that
# a move empties is only deleted once the move is done.
APPLY_ORDER = (KIND_RENAME, KIND_MOVE, KIND_DELETE)


class Fix(object):
    """One repair the user can tick on or off.

    Attributes:
        kind (str): one of ``KIND_RENAME``, ``KIND_MOVE`` or ``KIND_DELETE``.
        label (str): the line shown in the list.
        name (str): the workset name the fix works towards.
        workset_id (DB.WorksetId): the workset renamed or deleted.
        link (Link): the link the fix is about.
    """

    def __init__(self, kind, label, name=None, workset_id=None, link=None):
        self.kind = kind
        self.label = label
        self.name = name
        self.workset_id = workset_id
        self.link = link


class Result(object):
    """What :func:`apply_fixes` did.

    Attributes:
        applied (list[str]): labels of the fixes carried out.
        skipped (list): ``(label, reason)`` pairs for fixes left alone.
    """

    def __init__(self):
        self.applied = []
        self.skipped = []


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


def can_delete_worksets():
    """True when this Revit version can delete worksets.

    The API that deletes a workset arrived in Revit 2023, together with the
    settings that go with it.
    """
    return (hasattr(DB.WorksetTable, "DeleteWorkset")
            and hasattr(DB, "DeleteWorksetSettings")
            and hasattr(DB, "DeleteWorksetOption"))


def holds_levels_or_grids(doc, workset):
    """True when the workset carries the levels or the grids.

    Revit creates two default user worksets: the one with the model elements
    and the one with the levels and grids.  Only the first of them is the one
    that cannot be deleted, and the second is told apart by what it holds,
    since its name follows the language Revit runs in.

    Args:
        doc (DB.Document): the active document.
        workset (DB.Workset): the workset to look at.

    Returns:
        (bool): True when the workset holds levels or grids.
    """
    categories = (DB.BuiltInCategory.OST_Levels, DB.BuiltInCategory.OST_Grids)
    for category in categories:
        elements = DB.FilteredElementCollector(doc) \
            .OfCategory(category) \
            .WherePasses(DB.ElementWorksetFilter(workset.Id, False)) \
            .ToElements()
        if elements.Count:
            return True
    return False


def default_workset(doc, worksets):
    """Return the default workset, the one Revit will not let us delete.

    Revit's own documentation states that the workset it creates first cannot
    be deleted, only renamed, so the script has to recognise it by what it is
    rather than by its name, which the user is free to change.

    Args:
        doc (DB.Document): the active document.
        worksets (dict): the user worksets, keyed by their id.

    Returns:
        (DB.Workset): the default workset, or None when there is none.
    """
    flagged = [ws for ws in worksets.values()
               if getattr(ws, "IsDefaultWorkset", False)]
    for workset in flagged:
        if not holds_levels_or_grids(doc, workset):
            return workset
    for workset in worksets.values():
        if workset.Name == DEFAULT_WORKSET_NAME \
                and not holds_levels_or_grids(doc, workset):
            return workset
    return flagged[0] if flagged else None


def _find_workset(doc, name):
    """Return the user workset called `name`, or None."""
    for workset in user_worksets(doc).values():
        if workset.Name == name:
            return workset
    return None


def _owned_by_others(doc, elements):
    """True when another user has borrowed one of `elements`."""
    if not doc.IsWorkshared:
        return False
    return any(DB.WorksharingUtils.GetCheckoutStatus(doc, e.Id)
               == DB.CheckoutStatus.OwnedByOtherUser for e in elements)


def _canonical_names(links):
    """Return the workset name each link is heading for.

    Every link gets a workset of its own, named after the linked file, the way
    the link doctor names them.  Two links to files of the same name cannot
    share one workset, so the second one is numbered.

    Args:
        links (list[Link]): the links of the project.

    Returns:
        (list): ``(link, workset name)`` pairs, in the order of the links.
    """
    pairs = []
    used = set()
    for link in links:
        name = file2ws_name(link.file_name)
        if name in used:
            index = 2
            while u"{}_{}".format(name, index) in used:
                index += 1
            name = u"{}_{}".format(name, index)
        used.add(name)
        pairs.append((link, name))
    return pairs


def _plan_homes(pairs, names, contents, own, default_key):
    """Work out the workset every link ends up on.

    A link belongs on the workset named after the file it comes from.  When a
    workset holds nothing but that link, it is renamed into place, which keeps
    its ownership and its visibility settings instead of moving the link to a
    brand new workset.  A workset is only renamed when the name it takes is
    free and the name it gives up belongs to no other link, so two links never
    end up fighting over the same workset.

    Args:
        pairs (list): ``(link, workset name)`` pairs.
        names (dict): the current workset names, keyed by workset id.
        contents (dict): the element ids on every workset.
        own (dict): the element ids of every link.
        default_key (int): the id of the default workset.

    Returns:
        (tuple): ``{link id: destination id or None}`` and the ids of the
        worksets that are renamed into place.
    """
    reserved = set(name for _, name in pairs)
    free = set(names.values())

    homes = {}
    renames = {}
    claimed = set()
    for link, name in pairs:
        home = None
        for key, workset_name in names.items():
            if workset_name == name and key != default_key:
                home = key
                break
        if home is None:
            # A workset that holds nothing but this link can be renamed into
            # place, which keeps its ownership and its visibility settings.
            for key, held in contents.items():
                if key == default_key or key in claimed:
                    continue
                if not held or not held <= own[id(link)]:
                    continue
                if names[key] in reserved or name not in free:
                    continue
                renames[id(link)] = key
                claimed.add(key)
                free.discard(names[key])
                home = key
                break
        homes[id(link)] = home
    return homes, renames


def diagnose(doc):
    """Find what is wrong with the worksets of the project, without changing it.

    Args:
        doc (DB.Document): the active document.

    Returns:
        (tuple): the list of :class:`Fix` objects in apply order, the names of
        empty worksets this Revit version cannot delete, and the name of the
        default workset, which Revit will not let be deleted.
    """
    if not doc.IsWorkshared:
        return [], [], None

    worksets = user_worksets(doc)
    names = dict((key, ws.Name) for key, ws in worksets.items())
    contents = dict((key, workset_contents(doc, ws.Id))
                    for key, ws in worksets.items())
    default = default_workset(doc, worksets)
    default_key = id_value(default.Id) if default is not None else None

    pairs = _canonical_names(collect_links(doc))
    own = dict((id(link), link.element_ids()) for link, _ in pairs)
    homes, renames = _plan_homes(pairs, names, contents, own, default_key)

    rename_fixes = []
    move_fixes = []
    delete_fixes = []
    undeletable = []
    departures = {}
    arrivals = {}

    # The default workset keeps its proper name.  It cannot be deleted, so it
    # is cleaned up instead: the moves below take the links off it.  It goes
    # first, so its old name is free for a link that is after it.
    if default is not None and default.Name != DEFAULT_WORKSET_NAME:
        rename_fixes.append(Fix(KIND_RENAME,
                                S("fix.rename_default", default.Name,
                                  DEFAULT_WORKSET_NAME),
                                name=DEFAULT_WORKSET_NAME,
                                workset_id=default.Id))

    for link, name in pairs:
        home = homes[id(link)]
        if id(link) in renames:
            rename_fixes.append(Fix(KIND_RENAME,
                                    S("fix.rename", names[home], name,
                                      link.file_name),
                                    name=name, workset_id=home, link=link))

        to_move = []
        sources = set()
        for element in link.elements():
            current = id_value(element.WorksetId)
            if home is not None and current == home:
                continue
            to_move.append(element)
            sources.add(names.get(current, u"?"))
            departures.setdefault(current, set()).add(id_value(element.Id))
        if to_move:
            source_text = u", ".join(u"'{}'".format(s) for s in sorted(sources))
            move_fixes.append(Fix(KIND_MOVE,
                                  S("fix.move", link.file_name, source_text,
                                    name),
                                  name=name, link=link))
            if home is not None:
                arrivals.setdefault(home, set()).update(
                    id_value(element.Id) for element in to_move)

    # Whatever is left empty once the links have moved goes away.
    for key, workset in worksets.items():
        if key == default_key:
            continue
        remaining = contents[key] - departures.get(key, set())
        remaining |= arrivals.get(key, set())
        if remaining:
            continue
        if not can_delete_worksets():
            undeletable.append(workset.Name)
            continue
        delete_fixes.append(Fix(KIND_DELETE,
                                 S("fix.delete_empty", workset.Name),
                                 name=workset.Name, workset_id=workset.Id))

    fixes = rename_fixes + move_fixes + delete_fixes
    return fixes, undeletable, (default.Name if default is not None else None)


def apply_fixes(doc, fixes):
    """Carry out the chosen fixes as one undoable step.

    Args:
        doc (DB.Document): the active document.
        fixes (list[Fix]): the fixes the user kept ticked.

    Returns:
        (Result): what was applied and what was skipped, with the reason.
    """
    result = Result()
    by_kind = dict((kind, [f for f in fixes if f.kind == kind])
                   for kind in APPLY_ORDER)
    steps = (
        (KIND_RENAME, "tx.rename", _rename),
        (KIND_MOVE, "tx.move", _move),
        (KIND_DELETE, "tx.delete", _delete),
    )

    with WrappedTransactionGroup(doc, S("title")):
        for kind, tx_name, handler in steps:
            if not by_kind[kind]:
                continue
            with WrappedTransaction(doc, S(tx_name)):
                for fix in by_kind[kind]:
                    reason = _apply_one(doc, fix, handler)
                    if reason is None:
                        result.applied.append(fix.label)
                    else:
                        result.skipped.append((fix.label, reason))
    return result


def _apply_one(doc, fix, handler):
    """Run one fix in a sub-transaction that is rolled back if it is skipped."""
    sub = DB.SubTransaction(doc)
    sub.Start()
    reason = S("skip.revit_error", u"")
    try:
        reason = handler(doc, fix)
    except Exception as error:
        reason = S("skip.revit_error",
                   getattr(error, "Message", None) or error)
    finally:
        if reason is None:
            sub.Commit()
        else:
            sub.RollBack()
    return reason


def _rename(doc, fix):
    if not DB.WorksetTable.IsWorksetNameUnique(doc, fix.name):
        return S("skip.name_taken")
    DB.WorksetTable.RenameWorkset(doc, fix.workset_id, fix.name)
    return None


def _move(doc, fix):
    target = _find_workset(doc, fix.name)
    to_move = [e for e in fix.link.elements()
               if target is None
               or id_value(e.WorksetId) != id_value(target.Id)]
    if _owned_by_others(doc, to_move):
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


def _delete(doc, fix):
    if not can_delete_worksets():
        return S("skip.cannot_delete")
    remaining = workset_contents(doc, fix.workset_id)
    if remaining:
        return S("skip.not_empty", len(remaining))
    active = doc.GetWorksetTable().GetActiveWorksetId()
    settings = DB.DeleteWorksetSettings(
        DB.DeleteWorksetOption.MoveElementsToWorkset, active)
    if id_value(active) == id_value(fix.workset_id) \
            or not DB.WorksetTable.CanDeleteWorkset(doc, fix.workset_id,
                                                     settings):
        return S("skip.cannot_delete")
    DB.WorksetTable.DeleteWorkset(doc, fix.workset_id, settings)
    return None


def format_summary(result, undeletable, default_name=None):
    """Return the text of the closing dialog.

    Args:
        result (Result): the outcome of :func:`apply_fixes`, or None when
            nothing was applied.
        undeletable (list[str]): empty worksets this Revit cannot delete.
        default_name (str): the name of the default workset, which Revit does
            not allow deleting.

    Returns:
        (str): the report.
    """
    if result is None:
        result = Result()
        lines = [S("done.healthy")]
    else:
        lines = [S("done.applied", len(result.applied))]
        lines.extend(u"- {}".format(label) for label in result.applied)
    if result.skipped:
        lines.append(u"")
        lines.append(S("done.skipped", len(result.skipped)))
        lines.extend(u"- {}: {}".format(label, reason)
                     for label, reason in result.skipped)
    if undeletable:
        lines.append(u"")
        lines.append(S("done.no_delete_api", u", ".join(undeletable)))
    if default_name:
        lines.append(u"")
        lines.append(S("done.default_kept", default_name))
    return u"\n".join(lines)
