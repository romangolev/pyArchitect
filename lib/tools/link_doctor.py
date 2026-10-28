# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Diagnose and repair Revit links and the worksets they live on.

The ribbon command applies every fix by default; Shift+click lists them first
so the user can untick the ones to leave alone.

Every link is expected to sit, type and instances alike, on a workset of its
own named after the linked file by :func:`file2ws_name`, e.g. ``AR_Model.rvt``
goes on ``##_RVT_AR_MODEL``.  Worksets that follow an older team convention
(``A_LNK``, ``00_``, ``01_``, a leading dot) are accepted as they are.

A workset that starts with ``##`` is treated as owned by this tool, so it has to
carry exactly the expected name.  That is what catches a link that was reloaded
from a renamed file: its type takes the new file name, while it is still sitting
on the workset named after the old one.  :func:`diagnose` turns everything it
finds into a list of :class:`Fix` objects, without touching the model:

* ``rename`` -- the stale ``##`` workset holds nothing but this link and the
  expected name is free, so the workset is renamed in place and keeps its
  ownership, visibility settings and history;
* ``move`` -- the link is on a foreign or shared workset, so it is moved to the
  expected one, which is created when it does not exist yet;
* ``pin`` -- an instance of the link is not pinned;
* ``delete`` -- a ``##`` workset is empty, or will be once the moves are done,
  which is what an old, removed or renamed link leaves behind.

:func:`apply_fixes` runs the chosen fixes in that order inside one transaction
group, so a single undo reverts the whole run.  Everything is checked again at
that point: a workset is only deleted when it really holds no element any more,
so unticking a move in the list can never delete the link sitting on it.
"""

import os
import re

import Autodesk.Revit.DB as DB

from core.localization import StringTable
from core.selectionhelpers import id_value
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from tools.worksets import S as WS
from tools.worksets import (Fix, Result, apply_one, can_delete_worksets,
                            delete, is_link_workset, move, owned_by_others,
                            rename, user_worksets, workset_contents)


S = StringTable({
    "title": {
        "en_us": u"Link Doctor",
        "ru": u"Доктор связей",
        "es_es": u"Doctor de vínculos",
    },
    "dialog.button": {
        "en_us": u"Apply selected fixes",
        "ru": u"Исправить выбранное",
        "es_es": u"Aplicar las correcciones seleccionadas",
    },

    "fix.rename": {
        "en_us": u"Rename workset '{}' to '{}' ({})",
        "ru": u"Переименовать рабочий набор «{}» в «{}» ({})",
        "es_es": u"Renombrar el subproyecto '{}' a '{}' ({})",
    },
    "fix.move": {
        "en_us": u"Move '{}' from {} to '{}'",
        "ru": u"Перенести «{}» из {} в «{}»",
        "es_es": u"Mover '{}' de {} a '{}'",
    },
    "fix.move_new": {
        "en_us": u"Move '{}' from {} to new workset '{}'",
        "ru": u"Перенести «{}» из {} в новый рабочий набор «{}»",
        "es_es": u"Mover '{}' de {} al nuevo subproyecto '{}'",
    },
    "fix.pin": {
        "en_us": u"Pin {} instance(s) of '{}'",
        "ru": u"Закрепить экземпляры «{1}» ({0})",
        "es_es": u"Fijar {} ejemplar(es) de '{}'",
    },
    "fix.delete_empty": {
        "en_us": u"Delete empty workset '{}'",
        "ru": u"Удалить пустой рабочий набор «{}»",
        "es_es": u"Eliminar el subproyecto vacío '{}'",
    },
    "fix.delete_emptied": {
        "en_us": u"Delete workset '{}' (empty once the links are moved)",
        "ru": u"Удалить рабочий набор «{}» (опустеет после переноса связей)",
        "es_es": u"Eliminar el subproyecto '{}' (quedará vacío al mover los "
                 u"vínculos)",
    },

    "tx.rename": {
        "en_us": u"Link Doctor - rename worksets",
        "ru": u"Доктор связей - переименование наборов",
        "es_es": u"Doctor de vínculos - renombrar subproyectos",
    },
    "tx.move": {
        "en_us": u"Link Doctor - move links",
        "ru": u"Доктор связей - перенос связей",
        "es_es": u"Doctor de vínculos - mover vínculos",
    },
    "tx.pin": {
        "en_us": u"Link Doctor - pin links",
        "ru": u"Доктор связей - закрепление связей",
        "es_es": u"Doctor de vínculos - fijar vínculos",
    },
    "tx.delete": {
        "en_us": u"Link Doctor - delete worksets",
        "ru": u"Доктор связей - удаление наборов",
        "es_es": u"Doctor de vínculos - eliminar subproyectos",
    },

    "done.healthy": {
        "en_us": u"All links are pinned and sit on their own worksets. "
                 u"Nothing to fix.",
        "ru": u"Все связи закреплены и находятся на своих рабочих наборах. "
               u"Исправлять нечего.",
        "es_es": u"Todos los vínculos están fijados y en su propio subproyecto. "
                 u"No hay nada que corregir.",
    },
    "done.no_delete_api": {
        "en_us": u"{} empty link workset(s) were found, but Revit only allows "
                 u"deleting worksets from version 2023: {}",
        "ru": u"Найдено пустых наборов связей: {}, но удалять рабочие наборы "
               u"Revit позволяет только с версии 2023: {}",
        "es_es": u"Se encontraron {} subproyecto(s) de vínculos vacíos, pero "
                 u"Revit solo permite eliminarlos desde la versión 2023: {}",
    },
    "done.failed": {
        "en_us": u"Link Doctor could not finish:\n{}",
        "ru": u"Доктор связей не смог завершить работу:\n{}",
        "es_es": u"El doctor de vínculos no pudo terminar:\n{}",
    },

})


LEGACY_WORKSET_PATTERN = re.compile(r"(A[-_]{1}LNK|\.|00[-_]{1}|01[-_]{1})", re.I)

CYRILLIC = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
            u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")

TRANSLITERATION = {ord(a): ord(b) for a, b in zip(*CYRILLIC)}

KIND_RENAME = "rename"
KIND_MOVE = "move"
KIND_PIN = "pin"
KIND_DELETE = "delete"

APPLY_ORDER = (KIND_RENAME, KIND_MOVE, KIND_PIN, KIND_DELETE)


def file2ws_name(filename):
    """Return the workset name a link to `filename` belongs on.

    Args:
        filename (str): the link type name, i.e. the linked file name.

    Returns:
        (str): ``##_<EXT>_<NAME>``, transliterated and upper-cased.
    """
    name, ext = os.path.splitext(filename)
    ext = ext.replace(u'.', u'')
    name = re.sub(u'[^a-zA-Zа-яА-Я0-9_-]', u'_', name)
    name = name.translate(TRANSLITERATION)
    return u"##_{}_{}".format(ext, name).upper()


class Link(object):
    """A non-nested link type with its instances and the workset it wants.

    Attributes:
        link_type (DB.RevitLinkType): the type.
        instances (list[DB.RevitLinkInstance]): its placed instances.
        file_name (str): the type name, which is the linked file name.
        target (str): the workset name it belongs on.
    """

    def __init__(self, link_type, instances, nested_ids=()):
        self.link_type = link_type
        self.instances = instances
        self.nested_ids = set(nested_ids)
        self.file_name = link_type.get_Parameter(
            DB.BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString() or u""
        self.target = file2ws_name(self.file_name)

    def elements(self):
        """Return the type followed by its instances."""
        return [self.link_type] + list(self.instances)

    def element_ids(self):
        """Return the ids of the type, its instances and its nested links."""
        return set(id_value(e.Id) for e in self.elements()) | self.nested_ids


def collect_links(doc):
    """Return every non-nested link type of the project with its instances.

    Types without an instance are kept: an unplaced or removed link still holds
    its workset and would keep a stale one from ever becoming empty.

    Args:
        doc (DB.Document): the active document.

    Returns:
        (list[Link]): links sorted by file name.
    """
    instances = {}
    for instance in DB.FilteredElementCollector(doc) \
            .OfClass(DB.RevitLinkInstance).ToElements():
        instances.setdefault(id_value(instance.GetTypeId()), []).append(instance)

    link_types = DB.FilteredElementCollector(doc) \
        .OfClass(DB.RevitLinkType).ToElements()

    nested = {}
    for link_type in link_types:
        if link_type.IsNestedLink:
            type_id = id_value(link_type.Id)
            ids = nested.setdefault(id_value(link_type.GetRootId()), set())
            ids.add(type_id)
            ids.update(id_value(i.Id) for i in instances.get(type_id, []))

    links = []
    for link_type in link_types:
        if link_type.IsNestedLink:
            continue
        type_id = id_value(link_type.Id)
        links.append(Link(link_type, instances.get(type_id, []),
                          nested.get(type_id, ())))
    return sorted(links, key=lambda link: link.file_name.lower())


def is_acceptable(workset_name, target):
    """True when a link may stay on `workset_name`."""
    if workset_name == target:
        return True
    if is_link_workset(workset_name):
        return False
    return LEGACY_WORKSET_PATTERN.match(workset_name) is not None


def diagnose(doc):
    """Find what is wrong with the links of the project, without changing it.

    Args:
        doc (DB.Document): the active document.

    Returns:
        (tuple): the list of :class:`Fix` objects in apply order, and the names
        of empty link worksets this Revit version cannot delete.
    """
    links = collect_links(doc)
    fixes = []
    undeletable = []

    if doc.IsWorkshared:
        workset_fixes, undeletable = _diagnose_worksets(doc, links)
        fixes.extend(workset_fixes)

    for link in links:
        unpinned = [i for i in link.instances if not i.Pinned]
        if unpinned:
            fixes.append(Fix(KIND_PIN, S("fix.pin", len(unpinned), link.file_name),
                             link=link))

    fixes.sort(key=lambda fix: APPLY_ORDER.index(fix.kind))
    return fixes, undeletable


def _diagnose_worksets(doc, links):
    """Plan the renames, moves and deletes that put every link in its place."""
    worksets = user_worksets(doc)
    names = dict((key, ws.Name) for key, ws in worksets.items())
    contents = dict((key, workset_contents(doc, ws.Id))
                    for key, ws in worksets.items() if is_link_workset(ws.Name))

    existing_names = set(names.values())
    claimed_names = set()
    renamed = set()
    receiving = set()
    moved_away = {}
    fixes = []

    for link in links:
        elements = link.elements()
        current = [id_value(e.WorksetId) for e in elements]
        if all(is_acceptable(names.get(key, u""), link.target) for key in current):
            continue

        own_ids = link.element_ids()
        rename_from = None
        if link.target not in existing_names and link.target not in claimed_names:
            candidates = [key for key in set(current)
                          if key in contents and key not in renamed
                          and contents[key] and contents[key] <= own_ids]
            if candidates:
                rename_from = max(candidates, key=lambda key: len(contents[key]))

        if rename_from is not None:
            renamed.add(rename_from)
            fixes.append(Fix(KIND_RENAME,
                             S("fix.rename", names[rename_from], link.target,
                               link.file_name),
                             link=link, workset_id=worksets[rename_from].Id,
                             name=link.target))

        to_move = [e for e, key in zip(elements, current)
                   if names.get(key) != link.target and key != rename_from]
        if to_move:
            sources = sorted(set(names.get(id_value(e.WorksetId), u"?")
                                 for e in to_move))
            source_text = u", ".join(u"'{}'".format(s) for s in sources)
            is_new = rename_from is None \
                and link.target not in existing_names \
                and link.target not in claimed_names
            label_key = "fix.move_new" if is_new else "fix.move"
            leftover = worksets[rename_from].Id if rename_from is not None else None
            fixes.append(Fix(KIND_MOVE,
                             S(label_key, link.file_name, source_text, link.target),
                             link=link, workset_id=leftover, name=link.target))
            moved_ids = set(id_value(e.Id) for e in to_move)
            for key in set(id_value(e.WorksetId) for e in to_move):
                moved_away.setdefault(key, set()).update(
                    contents.get(key, set()) & moved_ids)

        claimed_names.add(link.target)
        for key, name in names.items():
            if name == link.target:
                receiving.add(key)

    undeletable = []
    for key in sorted(contents, key=lambda k: names[k].lower()):
        if key in renamed or key in receiving or names[key] in claimed_names:
            continue
        remaining = contents[key] - moved_away.get(key, set())
        if remaining:
            continue
        if not can_delete_worksets():
            undeletable.append(names[key])
            continue
        label_key = "fix.delete_empty" if not contents[key] else "fix.delete_emptied"
        fixes.append(Fix(KIND_DELETE, S(label_key, names[key]),
                         workset_id=worksets[key].Id, name=names[key]))

    return fixes, undeletable


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
        (KIND_RENAME, "tx.rename", rename),
        (KIND_MOVE, "tx.move", move),
        (KIND_PIN, "tx.pin", _pin),
        (KIND_DELETE, "tx.delete", delete),
    )

    applied = []
    with WrappedTransactionGroup(doc, S("title")):
        for kind, tx_name, handler in steps:
            if kind == KIND_DELETE:
                by_kind[kind].extend(_leftover_deletes(doc, applied, by_kind[kind]))
            if not by_kind[kind]:
                continue
            with WrappedTransaction(doc, S(tx_name)):
                for fix in by_kind[kind]:
                    reason = apply_one(doc, fix, handler)
                    result.record(fix, reason)
                    if reason is None:
                        applied.append(fix)
    return result


def _leftover_deletes(doc, applied, deletes):
    """Plan deletes for stale worksets a move emptied while the rename was off.

    A move fix carries the workset its rename would have taken over.  When that
    rename was unticked or skipped, the move leaves the workset behind empty.
    """
    if not can_delete_worksets():
        return []
    renamed = set(id_value(f.workset_id) for f in applied
                  if f.kind == KIND_RENAME)
    planned = set(id_value(f.workset_id) for f in deletes)
    table = doc.GetWorksetTable()
    extra = []
    for fix in applied:
        if fix.kind != KIND_MOVE or fix.workset_id is None:
            continue
        key = id_value(fix.workset_id)
        if key in renamed or key in planned:
            continue
        planned.add(key)
        if workset_contents(doc, fix.workset_id):
            continue
        name = table.GetWorkset(fix.workset_id).Name
        extra.append(Fix(KIND_DELETE, S("fix.delete_emptied", name),
                         workset_id=fix.workset_id, name=name))
    return extra


def _pin(doc, fix):
    unpinned = [i for i in fix.link.instances if not i.Pinned]
    if owned_by_others(doc, unpinned):
        return WS("skip.borrowed")
    for instance in unpinned:
        instance.Pinned = True
    return None


def format_summary(result, undeletable):
    """Return the text of the closing dialog.

    Args:
        result (Result): the outcome of :func:`apply_fixes`, or None when
            nothing was applied.
        undeletable (list[str]): empty link worksets this Revit cannot delete.

    Returns:
        (str): the report.
    """
    lines = [S("done.healthy")] if result is None else result.lines()
    if undeletable:
        lines.append(u"")
        lines.append(S("done.no_delete_api", len(undeletable),
                       u", ".join(undeletable)))
    return u"\n".join(lines)
