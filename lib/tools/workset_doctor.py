# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Diagnose and repair the worksets of a project.

The Review Links command (:mod:`tools.link_doctor`) looks at the links and at
the worksets they sit on.  This module looks at the worksets themselves: it
gives every linked file a workset of its own, takes the links off every other
workset and deletes the link worksets that are left empty.

The default worksets Revit creates are left as they are.  Autodesk's
documentation on deleting a workset states that the default one cannot be
deleted, only renamed, and its name follows the language Revit runs in.  So the
links sitting on one of them are moved onto worksets of their own, and the
workset itself is neither deleted nor renamed.

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

from core.localization import StringTable
from core.selectionhelpers import id_value
from core.transaction import WrappedTransaction, WrappedTransactionGroup
from tools.link_doctor import collect_links
from tools.worksets import (Fix, Result, apply_one, can_delete_worksets,
                            delete, is_link_workset, move, rename,
                            user_worksets, workset_contents)


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
})


KIND_RENAME = "rename"
KIND_MOVE = "move"
KIND_DELETE = "delete"


class Diagnosis(object):
    """What :func:`diagnose` found.

    Attributes:
        workshared (bool): False when the document has no worksets at all.
        fixes (list[Fix]): the fixes, renames first, then moves, then deletes.
        undeletable (list[str]): empty link worksets this Revit cannot delete.
        defaults_named_as_link (list[str]): default worksets of Revit that
            carry a link workset name, which only the user can rename.
    """

    def __init__(self, workshared=True, fixes=(), undeletable=(),
                 defaults_named_as_link=()):
        self.workshared = workshared
        self.fixes = list(fixes)
        self.undeletable = list(undeletable)
        self.defaults_named_as_link = list(defaults_named_as_link)


def default_workset_keys(worksets):
    """Return the ids of the default worksets, the ones Revit created."""
    return set(key for key, ws in worksets.items() if ws.IsDefaultWorkset)


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
    names = dict((key, ws.Name) for key, ws in worksets.items())
    protected = default_workset_keys(worksets)
    blocked = sorted(names[key] for key in protected
                     if is_link_workset(names[key]))
    links = [link for link in collect_links(doc) if link.target not in blocked]

    hosts = set(id_value(e.WorksetId) for link in links
                for e in link.elements())
    contents = dict((key, workset_contents(doc, ws.Id))
                    for key, ws in worksets.items()
                    if key not in protected
                    and (key in hosts or is_link_workset(ws.Name)))
    homes, renames = plan_homes(links, names, contents, protected)

    fixes = []
    departures = {}
    arrivals = {}
    for link in links:
        if link not in renames:
            continue
        home = renames[link]
        fixes.append(Fix(KIND_RENAME,
                         S("fix.rename", names[home], link.target,
                           link.file_name),
                         link=link, workset_id=worksets[home].Id,
                         name=link.target))

    for link in links:
        home = homes[link]
        to_move = [e for e in link.elements()
                   if home is None or id_value(e.WorksetId) != home]
        if not to_move:
            continue
        sources = sorted(set(names.get(id_value(e.WorksetId), u"?")
                             for e in to_move))
        source_text = u", ".join(u"'{}'".format(s) for s in sources)
        fixes.append(Fix(KIND_MOVE,
                         S("fix.move", link.file_name, source_text, link.target),
                         link=link, name=link.target))
        moved = set(id_value(e.Id) for e in to_move)
        for element in to_move:
            departures.setdefault(id_value(element.WorksetId), set()) \
                .update(moved)
        if home is not None:
            arrivals.setdefault(home, set()).update(moved)

    homes_used = set(homes.values())
    undeletable = []
    for key in sorted(contents, key=lambda k: names[k].lower()):
        if key in homes_used or not is_link_workset(names[key]):
            continue
        remaining = (contents[key] - departures.get(key, set())) \
            | arrivals.get(key, set())
        if remaining:
            continue
        if not can_delete_worksets():
            undeletable.append(names[key])
            continue
        fixes.append(Fix(KIND_DELETE, S("fix.delete_empty", names[key]),
                         workset_id=worksets[key].Id, name=names[key]))

    return Diagnosis(fixes=fixes, undeletable=undeletable,
                     defaults_named_as_link=blocked)


def apply_fixes(doc, fixes):
    """Carry out the chosen fixes as one undoable step.

    The renames run first, so a link moves onto a workset that already carries
    its name, and the deletions run last, once the moves have emptied them.

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
    return result


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
    for name in diagnosis.defaults_named_as_link:
        lines.append(u"")
        lines.append(S("done.default_named_as_link", name))
    return u"\n".join(lines)
