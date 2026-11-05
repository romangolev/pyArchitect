# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Diagnose and repair the worksets of a project.

The Review Links command (:mod:`tools.link_doctor`) looks at the links and at
the worksets they sit on.  This module looks at the worksets themselves: it
gives every linked file a workset of its own, takes the links off every other
workset and deletes the link worksets that are left empty.  Linked CAD files
share one workset per format, ``##_DWG`` for DWG files
(:mod:`tools.cad_links`).

The default workset -- the one Revit calls ``Workset1`` -- is the odd one out.
Autodesk's documentation on deleting a workset states that it cannot be
deleted, only renamed, so the script empties it instead.  When the user has
renamed it, it gets ``Workset1`` back and a new workset takes over the name it
had, together with everything that sat on it.  When it is still called
``Workset1``, its elements go to a ``Model`` workset.  Either way the links on
it move to worksets of their own.  Revit flags this workset as the default
one and gives it the id 0.

Every level and grid belongs on ``Shared Levels and Grids``, which is created
when it is missing.  They move there before the default workset is emptied.

This tool is the strict one.  It puts every link on the workset named after
its file, even when the team keeps its links on a shared workset of an older
convention, which the link doctor tolerates.  Both tools name a link's workset
with :func:`tools.link_doctor.file2ws_name`, and two links whose files map to
the same name share that workset, so neither tool undoes the other.

Only worksets named like a link workset (``##``) are ever deleted, the same
rule the link doctor follows, so worksets a template prepares for later use
survive while they are still empty.

:func:`diagnose` turns everything it finds into a :class:`Diagnosis` without
touching the model.  :func:`apply_fixes` runs the chosen fixes in one
transaction group, so a single undo reverts the whole run, and a fix that
cannot be carried out is skipped and listed without undoing the others.
"""

import Autodesk.Revit.DB as DB

from core.localization import StringTable
from core.selectionhelpers import id_value
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from tools.cad_links import collect_cad_links
from tools.link_doctor import collect_links
from tools.worksets import S as WS
from tools.worksets import (Fix, Result, apply_one, can_delete_worksets,
                            delete, find_workset, is_link_workset, move,
                            rename, user_worksets, workset_contents)


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
        "en_us": u"Rename the default workset '{}' back to '{}'",
        "ru": u"Вернуть рабочему набору по умолчанию «{}» имя «{}»",
        "es_es": u"Devolver al subproyecto predeterminado '{}' el nombre '{}'",
    },
    "fix.empty_default": {
        "en_us": u"Move the elements of the default workset '{}' to '{}'",
        "ru": u"Перенести элементы рабочего набора по умолчанию «{}» в «{}»",
        "es_es": u"Mover los elementos del subproyecto predeterminado '{}' a "
                 u"'{}'",
    },
    "fix.move_datums": {
        "en_us": u"Move {} level(s) and grid(s) to '{}'",
        "ru": u"Перенести уровни и оси ({}) в «{}»",
        "es_es": u"Mover {} nivel(es) y rejilla(s) a '{}'",
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
    "tx.datums": {
        "en_us": u"Workset Doctor - move levels and grids",
        "ru": u"Доктор рабочих наборов - перенос уровней и осей",
        "es_es": u"Doctor de subproyectos - mover niveles y rejillas",
    },
    "tx.empty": {
        "en_us": u"Workset Doctor - empty the default workset",
        "ru": u"Доктор рабочих наборов - очистка набора по умолчанию",
        "es_es": u"Doctor de subproyectos - vaciar el subproyecto predeterminado",
    },
    "tx.delete": {
        "en_us": u"Workset Doctor - delete worksets",
        "ru": u"Доктор рабочих наборов - удаление наборов",
        "es_es": u"Doctor de subproyectos - eliminar subproyectos",
    },

    "done.healthy": {
        "en_us": u"Every link has a workset of its own and no empty link "
                 u"workset is left over. Nothing to fix.",
        "ru": u"У каждой связи есть свой рабочий набор, и пустых наборов "
               u"связей не осталось. Исправлять нечего.",
        "es_es": u"Cada vínculo tiene su propio subproyecto y no queda ningún "
                 u"subproyecto de vínculos vacío. No hay nada que corregir.",
    },
    "done.no_delete_api": {
        "en_us": u"Empty link worksets were found, but Revit only allows "
                 u"deleting worksets from version 2023: {}",
        "ru": u"Найдены пустые наборы связей, но удалять рабочие наборы Revit "
               u"позволяет только с версии 2023: {}",
        "es_es": u"Se encontraron subproyectos de vínculos vacíos, pero Revit "
                 u"solo permite eliminarlos desde la versión 2023: {}",
    },
    "done.default_named_as_link": {
        "en_us": u"'{}' is one of Revit's default worksets, which cannot be "
                 u"deleted, so it was left as it is. Rename it in Manage "
                 u"Worksets to free its name for the link.",
        "ru": u"«{}» — один из рабочих наборов Revit по умолчанию, его нельзя "
               u"удалить, поэтому он оставлен как есть. Переименуйте его в "
               u"диалоге «Рабочие наборы», чтобы освободить имя для связи.",
        "es_es": u"'{}' es uno de los subproyectos predeterminados de Revit, "
                 u"que no se pueden eliminar, por lo que se ha dejado como "
                 u"está. Cámbiele el nombre en Gestionar subproyectos para "
                 u"liberar el nombre para el vínculo.",
    },
    "done.workset1_taken": {
        "en_us": u"The default workset '{}' was left as it is: another workset "
                 u"is already called '{}'. Rename that one in Manage Worksets "
                 u"and run Review Worksets again.",
        "ru": u"Рабочий набор по умолчанию «{}» оставлен как есть: другой "
               u"набор уже называется «{}». Переименуйте его в диалоге "
               u"«Рабочие наборы» и запустите проверку ещё раз.",
        "es_es": u"El subproyecto predeterminado '{}' se ha dejado como está: "
                 u"otro subproyecto ya se llama '{}'. Cámbiele el nombre en "
                 u"Gestionar subproyectos y vuelva a ejecutar la revisión.",
    },
    "done.default_left": {
        "en_us": u"The default workset still holds {} element(s) that Revit "
                 u"did not let move.",
        "ru": u"В рабочем наборе по умолчанию осталось элементов, которые "
               u"Revit не дал перенести: {}.",
        "es_es": u"El subproyecto predeterminado todavía contiene {} "
                 u"elemento(s) que Revit no permitió mover.",
    },
    "done.failed": {
        "en_us": u"Workset Doctor could not finish:\n{}",
        "ru": u"Доктор рабочих наборов не смог завершить работу:\n{}",
        "es_es": u"El doctor de subproyectos no pudo terminar:\n{}",
    },
    "skip.still_named": {
        "en_us": u"the default workset still carries that name",
        "ru": u"рабочий набор по умолчанию всё ещё носит это имя",
        "es_es": u"el subproyecto predeterminado todavía lleva ese nombre",
    },
    "done.not_workshared": {
        "en_us": u"The file is not workshared, so it has no worksets to review.",
        "ru": u"Файл не является совместным, поэтому в нём нет рабочих "
               u"наборов для проверки.",
        "es_es": u"El archivo no es compartido, por lo que no tiene subproyectos "
                 u"que revisar.",
    },
})


DEFAULT_WORKSET_NAME = u"Workset1"
FIRST_WORKSET_ID = 0
LEFTOVER_WORKSET_NAME = u"Model"
DATUM_WORKSET_NAME = u"Shared Levels and Grids"

MOVED_ELSEWHERE = (DB.RevitLinkInstance, DB.RevitLinkType, DB.ImportInstance,
                   DB.Level, DB.Grid)

KIND_RENAME = "rename"
KIND_MOVE = "move"
KIND_DATUMS = "datums"
KIND_EMPTY = "empty"
KIND_DELETE = "delete"


class Diagnosis(object):
    """What :func:`diagnose` found.

    Attributes:
        workshared (bool): False when the document has no worksets at all.
        fixes (list[Fix]): the fixes in the order they are applied.
        undeletable (list[str]): empty link worksets this Revit cannot delete.
        notes (list[str]): what only the user can sort out.
    """

    def __init__(self, workshared=True, fixes=(), undeletable=(), notes=()):
        self.workshared = workshared
        self.fixes = list(fixes)
        self.undeletable = list(undeletable)
        self.notes = list(notes)


def collect_datums(doc):
    """Return every level and grid of the project."""
    categories = (DB.BuiltInCategory.OST_Levels, DB.BuiltInCategory.OST_Grids)
    return [element for category in categories
            for element in DB.FilteredElementCollector(doc)
            .OfCategory(category).WhereElementIsNotElementType().ToElements()]


def placed_model_elements(doc, workset_id):
    """Return the elements placed in the model on a workset.

    Revit keeps internal elements on the default workset too, such as legend
    components, sketch planes and the default HVAC zone.  They have no
    bounding box or no model category, and they are left where they are.
    """
    elements = DB.FilteredElementCollector(doc) \
        .WherePasses(DB.ElementWorksetFilter(workset_id, False)) \
        .WhereElementIsNotElementType().ToElements()
    return [e for e in elements if e.Category is not None
            and e.Category.CategoryType == DB.CategoryType.Model
            and e.get_BoundingBox(None) is not None]


def placed_model_ids(doc, workset_id):
    """Return the ids of the elements placed in the model on a workset."""
    return set(id_value(e.Id) for e in placed_model_elements(doc, workset_id))


def default_workset(worksets):
    """Return the workset Revit will not let be deleted, or None.

    Revit flags only that workset as the default one, and it is the first
    workset Revit creates, with the id 0.  Should more than one carry the flag,
    the id decides; without it, None is returned so that no workset is touched
    by mistake.

    Args:
        worksets (dict): the user worksets, keyed by their id.
    """
    flagged = [ws for ws in worksets.values() if ws.IsDefaultWorkset]
    if len(flagged) == 1:
        return flagged[0]
    first = [ws for ws in flagged if id_value(ws.Id) == FIRST_WORKSET_ID]
    return first[0] if first else None


def plan_homes(links, names, contents, protected):
    """Work out the workset every link ends up on.

    A link belongs on the workset named after the file it comes from.  When no
    workset carries that name yet and a workset holds nothing but this link, it
    is renamed into place, which keeps its ownership and its visibility
    settings.  It is only renamed when the name it gives up belongs to no other
    link.  Links whose files map to the same name share one workset.

    Args:
        links (list[Link]): the links of the project.
        names (dict): the current workset names, keyed by workset id.
        contents (dict): the element ids on the worksets that may be renamed.
        protected (set): the ids of the worksets that are never renamed or
            used as a link's home.

    Returns:
        (tuple): ``{link: destination id or None}``, where None means a new
        workset, and ``{link: workset id}`` for the worksets renamed into place.
    """
    reserved = set(link.target for link in links)
    planned = dict(names)
    homes = {}
    renames = {}
    for link in links:
        home = _named(planned, link.target, protected)
        if home is None:
            home = _rename_candidate(link, planned, contents, reserved,
                                     renames.values())
            if home is not None:
                renames[link] = home
                planned[home] = link.target
        homes[link] = home
    return homes, renames


def _named(names, name, protected):
    for key, workset_name in names.items():
        if workset_name == name and key not in protected:
            return key
    return None


def _rename_candidate(link, names, contents, reserved, renamed):
    own = link.element_ids()
    current = sorted(set(id_value(e.WorksetId) for e in link.elements()))
    for key in current:
        held = contents.get(key)
        if not held or not held <= own:
            continue
        if key in renamed or names[key] in reserved:
            continue
        return key
    return None


def diagnose(doc):
    """Find what is wrong with the worksets of the project, without changing it.

    Args:
        doc (DB.Document): the active document.

    Returns:
        (Diagnosis): the fixes and what the user has to know about.
    """
    if not doc.IsWorkshared:
        return Diagnosis(workshared=False)

    worksets = user_worksets(doc)
    default, notes = _default_to_clean(worksets)
    blocked = _blocked_names(worksets, default)
    notes.extend(S("done.default_named_as_link", name) for name in blocked)
    links = [link for link in collect_links(doc) + collect_cad_links(doc)
             if link.target not in blocked]
    contents = _candidate_contents(doc, worksets, links)
    homes, renames = plan_homes(links, _planned_names(worksets, default),
                                contents, _protected(worksets))

    datums = collect_datums(doc)
    traffic = _Traffic()
    fixes = _default_rename_fixes(default)
    fixes.extend(_link_rename_fixes(worksets, links, renames))
    fixes.extend(_move_fixes(worksets, links, homes, traffic))
    fixes.extend(_datum_fixes(worksets, datums, traffic))
    fixes.extend(_empty_default_fixes(doc, default, links, datums))
    delete_fixes, undeletable = _delete_fixes(worksets, contents, homes,
                                              traffic)
    fixes.extend(delete_fixes)
    return Diagnosis(fixes=fixes, undeletable=undeletable, notes=notes)


class _Traffic(object):
    """The elements the planned moves take off and put on every workset."""

    def __init__(self):
        self._departures = {}
        self._arrivals = {}

    def record(self, elements, home):
        """Note that `elements` leave their worksets for `home`."""
        moved = set(id_value(e.Id) for e in elements)
        for element in elements:
            self._departures.setdefault(id_value(element.WorksetId), set()) \
                .update(moved)
        if home is not None:
            self._arrivals.setdefault(home, set()).update(moved)

    def remaining(self, key, held):
        """Return what workset `key`, holding `held` now, holds after the moves."""
        return (held - self._departures.get(key, set())) \
            | self._arrivals.get(key, set())


def _needs_rename(default):
    return default is not None and default.Name != DEFAULT_WORKSET_NAME


def _protected(worksets):
    return set(key for key, ws in worksets.items() if ws.IsDefaultWorkset)


def _default_to_clean(worksets):
    default = default_workset(worksets)
    if not _needs_rename(default):
        return default, []
    if any(ws.Name == DEFAULT_WORKSET_NAME for ws in worksets.values()):
        return None, [S("done.workset1_taken", default.Name,
                        DEFAULT_WORKSET_NAME)]
    return default, []


def _blocked_names(worksets, default):
    renamed = id_value(default.Id) if _needs_rename(default) else None
    return sorted(ws.Name for key, ws in worksets.items()
                  if ws.IsDefaultWorkset and is_link_workset(ws.Name)
                  and key != renamed)


def _planned_names(worksets, default):
    names = dict((key, ws.Name) for key, ws in worksets.items())
    if _needs_rename(default):
        names[id_value(default.Id)] = DEFAULT_WORKSET_NAME
    return names


def _candidate_contents(doc, worksets, links):
    protected = _protected(worksets)
    hosts = set(id_value(e.WorksetId) for link in links
                for e in link.elements())
    return dict((key, workset_contents(doc, ws.Id))
                for key, ws in worksets.items()
                if key not in protected
                and (key in hosts or is_link_workset(ws.Name)))


def _default_rename_fixes(default):
    if not _needs_rename(default):
        return []
    return [Fix(KIND_RENAME,
                S("fix.rename_default", default.Name, DEFAULT_WORKSET_NAME),
                workset_id=default.Id, name=DEFAULT_WORKSET_NAME)]


def _link_rename_fixes(worksets, links, renames):
    return [Fix(KIND_RENAME,
                S("fix.rename", worksets[renames[link]].Name, link.target,
                  link.file_name),
                link=link, workset_id=worksets[renames[link]].Id,
                name=link.target)
            for link in links if link in renames]


def _move_fixes(worksets, links, homes, traffic):
    fixes = []
    for link in links:
        home = homes[link]
        to_move = [e for e in link.elements()
                   if home is None or id_value(e.WorksetId) != home]
        if to_move:
            traffic.record(to_move, home)
            fixes.append(_move_fix(worksets, link, to_move))
    return fixes


def _move_fix(worksets, link, to_move):
    sources = sorted(set(_workset_name(worksets, e.WorksetId) for e in to_move))
    source_text = u", ".join(u"'{}'".format(s) for s in sources)
    return Fix(KIND_MOVE,
               S("fix.move", link.file_name, source_text, link.target),
               link=link, name=link.target)


def _workset_name(worksets, workset_id):
    workset = worksets.get(id_value(workset_id))
    return workset.Name if workset is not None else u"?"


def _datum_fixes(worksets, datums, traffic):
    home = _named(_planned_names(worksets, None), DATUM_WORKSET_NAME, ())
    stray = [d for d in datums if id_value(d.WorksetId) != home]
    if not stray:
        return []
    traffic.record(stray, home)
    return [Fix(KIND_DATUMS,
                S("fix.move_datums", len(stray), DATUM_WORKSET_NAME),
                name=DATUM_WORKSET_NAME)]


def _empty_default_fixes(doc, default, links, datums):
    if default is None:
        return []
    moved_elsewhere = set(id_value(d.Id) for d in datums)
    for link in links:
        moved_elsewhere |= link.element_ids()
    if not placed_model_ids(doc, default.Id) - moved_elsewhere:
        return []
    keeps_name = _needs_rename(default) and not is_link_workset(default.Name)
    destination = default.Name if keeps_name else LEFTOVER_WORKSET_NAME
    return [Fix(KIND_EMPTY,
                S("fix.empty_default", default.Name, destination),
                workset_id=default.Id, name=destination)]


def _delete_fixes(worksets, contents, homes, traffic):
    homes_used = set(homes.values())
    fixes = []
    undeletable = []
    for key in sorted(contents, key=lambda k: worksets[k].Name.lower()):
        name = worksets[key].Name
        if key in homes_used or not is_link_workset(name) \
                or traffic.remaining(key, contents[key]):
            continue
        if not can_delete_worksets():
            undeletable.append(name)
            continue
        fixes.append(Fix(KIND_DELETE, S("fix.delete_empty", name),
                         workset_id=worksets[key].Id, name=name))
    return fixes, undeletable


def apply_fixes(doc, fixes):
    """Carry out the chosen fixes as one undoable step.

    The renames run first, so a link moves onto a workset that already carries
    its name and the default workset frees the name it had.  The default
    workset is emptied once the links, levels and grids are off it, and the
    deletions run last.

    Args:
        doc (DB.Document): the active document.
        fixes (list[Fix]): the fixes the user kept ticked.

    Returns:
        (Result): what was applied and what was skipped, with the reason.
    """
    result = Result()
    steps = (
        (KIND_RENAME, "tx.rename", rename),
        (KIND_MOVE, "tx.move", move),
        (KIND_DATUMS, "tx.datums", _move_datums),
        (KIND_EMPTY, "tx.empty", _empty_default),
        (KIND_DELETE, "tx.delete", delete),
    )

    with WrappedTransactionGroup(doc, S("title")):
        for kind, tx_name, handler in steps:
            chosen = [fix for fix in fixes if fix.kind == kind]
            if not chosen:
                continue
            with WrappedTransaction(doc, S(tx_name)):
                for fix in chosen:
                    result.record(fix, apply_one(doc, fix, handler))
            if kind == KIND_EMPTY:
                result.notes.extend(_leftovers(doc, chosen))
    return result


def _leftovers(doc, fixes):
    notes = []
    for fix in fixes:
        left = len(placed_model_ids(doc, fix.workset_id))
        if left:
            notes.append(S("done.default_left", left))
    return notes


def _move_datums(doc, fix):
    target = find_workset(doc, fix.name)
    target_key = id_value(target.Id) if target is not None else None
    stray = [d for d in collect_datums(doc)
             if id_value(d.WorksetId) != target_key]
    return _move_onto(doc, _movable_params(doc, stray), fix.name)


def _empty_default(doc, fix):
    default = doc.GetWorksetTable().GetWorkset(fix.workset_id)
    if default.Name == fix.name:
        return S("skip.still_named")
    kept = [e for e in placed_model_elements(doc, fix.workset_id)
            if not isinstance(e, MOVED_ELSEWHERE)]
    return _move_onto(doc, _movable_params(doc, kept), fix.name)


def _move_onto(doc, params, name):
    if not params:
        return WS("skip.read_only")
    target = find_workset(doc, name) or DB.Workset.Create(doc, name)
    target_id = id_value(target.Id)
    for param in params:
        try:
            param.Set(target_id)
        except Exception:
            continue
    return None


def _movable_params(doc, elements):
    params = []
    for element in elements:
        param = element.get_Parameter(DB.BuiltInParameter.ELEM_PARTITION_PARAM)
        if param is None or param.IsReadOnly:
            continue
        if DB.WorksharingUtils.GetCheckoutStatus(doc, element.Id) \
                == DB.CheckoutStatus.OwnedByOtherUser:
            continue
        params.append(param)
    return params


def format_summary(result, diagnosis):
    """Return the text of the closing dialog.

    Args:
        result (Result): the outcome of :func:`apply_fixes`, or None when
            nothing was applied.
        diagnosis (Diagnosis): what :func:`diagnose` found.

    Returns:
        (str): the report.
    """
    if not diagnosis.workshared:
        return S("done.not_workshared")
    lines = [S("done.healthy")] if result is None else result.lines()
    if diagnosis.undeletable:
        lines.append(u"")
        lines.append(S("done.no_delete_api", u", ".join(diagnosis.undeletable)))
    for note in diagnosis.notes:
        lines.append(u"")
        lines.append(note)
    return u"\n".join(lines)
