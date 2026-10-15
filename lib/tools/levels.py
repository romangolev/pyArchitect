# -*- coding: utf-8 -*-
# pylint: skip-file
# by Roman Golev

"""Re-level selected elements without moving them in Z.

Revit does not store the position of a level-based element as an absolute
elevation.  It stores a level plus an offset, and resolves the base of the
element to ``Level.Elevation + offset``.  Writing a new level therefore drags
the element up or down by the difference between the two levels, which is why
Replacing a Level, or a plain "change level" from a schedule, moves whatever it
touches.  To change the level and still land on the same elevation, the offset
has to absorb exactly that difference::

    new_offset = (old_level.Elevation + old_offset) - new_level.Elevation

Neither the level parameter nor the offset parameter is shared across
categories, the names differ per category *and* per Revit version, and an
element will happily accept a value on a parameter that means nothing for it --
a door, a column and a desk all expose a writable
``FLOOR_HEIGHTABOVELEVEL_PARAM``.  So the two are looked up as a pair, from
:data:`LEVEL_OFFSET_PAIRS`, and an element is only re-levelled when it exposes
both halves of a pair and both are writable.

The parameter arithmetic is not trusted on its own either: after writing, the
bottom of the element is read back from its geometry, and the change is undone
and reported as skipped if the element moved in Z anyway.  That guard is what
catches the cases the table cannot know about -- a category Revit adds
parameters to, or a family that redefines what its own elevation means.

Everything the tool cannot re-level without moving is reported as skipped
rather than silently moved:

* rooms -- ``ROOM_LEVEL_ID`` is read-only because a room's level follows the
  boundary and the walls around it;
* curtain panels, grids, and most annotation and view-adjacent elements -- the
  level is either not a parameter of theirs or is not writable;
* family instances whose family defines its own height above the level: a
  level-based family such as a desk exposes ``INSTANCE_ELEVATION_PARAM`` as a
  read-only composite, because the real value lives in a parameter only that
  family has, so preserving its Z is not possible from here;
* members of a model group, which cannot be edited outside group edit mode, and
  the group itself, whose ``GROUP_LEVEL`` moves its members rather than the
  group's own geometry.

Doors and windows hosted in a wall *are* re-levelled: on 2021 they expose a
writable ``FAMILY_LEVEL_PARAM`` and ``INSTANCE_ELEVATION_PARAM``, and writing
both leaves them in their opening at exactly the same Z, which is the promise
this tool makes.  On versions where a hosted instance's level is read-only
instead, they fall into the read-only case above and are skipped.

What reaches the transaction is decided by :func:`has_own_level`, not by the
category of the element.  A model category is far wider than "has a level":
Revit files materials and material assets under the model category type, and
family types, wall types and view types are element types rather than
instances, so picking them would either change a template or change nothing at
all.  :class:`LevelBasedElementFilter` applies that test to PickObjects, and
:func:`split_selection` applies it again to a pre-selection made in the ribbon,
which PickObjects never sees, so neither can put one of those into a run.
"""

import Autodesk.Revit.DB as DB
from Autodesk.Revit.UI.Selection import ISelectionFilter

from core.localization import StringTable
from core.selectionhelpers import id_value
from core.transaction import WrappedTransaction


S = StringTable({
    "transaction": {
        "en_us": u"Swap Level",
        "ru": u"Сменить уровень",
        "es_es": u"Cambiar de nivel",
    },

    "dialog.title": {
        "en_us": u"Target level",
        "ru": u"Целевой уровень",
        "es_es": u"Nivel de destino",
    },
    "dialog.button": {
        "en_us": u"Swap Level",
        "ru": u"Сменить уровень",
        "es_es": u"Cambiar nivel",
    },
    "dialog.no_levels": {
        "en_us": u"The project has no levels to work with.",
        "ru": u"В проекте нет уровней.",
        "es_es": u"El proyecto no tiene niveles.",
    },

    "done.moved": {
        "en_us": u"Changed the level of {} element(s) to '{}'. They did not "
                 u"move up or down.",
        "ru": u"Уровень изменён у {} элем. на «{}». Высота не изменилась.",
        "es_es": u"Se cambió el nivel de {} elemento(s) a '{}'. Su altura no se ha "
                 u"modificado.",
    },
    "done.none": {
        "en_us": u"Nothing to do: no element of the selection can change level "
                 u"without moving up or down.",
        "ru": u"Нечего делать: ни один элемент выделения не может сменить "
               u"уровень без сдвига по высоте.",
        "es_es": u"No hay nada que hacer: ningún elemento de la selección puede "
                 u"cambiar de nivel sin moverse en altura.",
    },
    "done.no_selection": {
        "en_us": u"No elements were selected.",
        "ru": u"Не выбрано ни одного элемента.",
        "es_es": u"No se ha seleccionado ningún elemento.",
    },
    "done.skipped": {
        "en_us": u"Skipped {} element(s):",
        "ru": u"Пропущено элем. ({}):",
        "es_es": u"Se han omitido {} elemento(s):",
    },
    "done.more": {
        "en_us": u"... and {} more",
        "ru": u"... и ещё {}",
        "es_es": u"... y {} más",
    },
    "done.unchanged": {
        "en_us": u"{} element(s) were already on that level.",
        "ru": u"{} элем. уже находились на этом уровне.",
        "es_es": u"{} elemento(s) ya estaban en ese nivel.",
    },
    "done.ignored": {
        "en_us": u"Ignored {} selected object(s) that have no level of their own "
                 u"(materials, family types, grids, project information and the "
                 u"like).",
        "ru": u"Пропущено {} выбранных объект. без собственного уровня "
               u"(материалы, типы семейств, сетки, сведения о проекте и т. п.).",
        "es_es": u"Se han omitido {} objeto(s) seleccionados que no tienen nivel "
                 u"propio (materiales, tipos de familia, retículas, información "
                 u"del proyecto y similares).",
    },
    "done.none_selected": {
        "en_us": u"None of the selected objects has a level, so there is "
                 u"nothing to move.",
        "ru": u"Ни у одного из выбранных объектов нет уровня — перемещать "
               u"нечего.",
        "es_es": u"Ninguno de los objetos seleccionados tiene nivel, así que no "
                 u"hay nada que mover.",
    },
    "done.failed": {
        "en_us": u"The level change could not be completed:\n{}",
        "ru": u"Не удалось выполнить смену уровня:\n{}",
        "es_es": u"No se ha podido completar el cambio de nivel:\n{}",
    },

    "skip.no_level": {
        "en_us": u"it has no level parameter to set",
        "ru": u"нет параметра уровня",
        "es_es": u"no tiene parámetro de nivel",
    },
    "skip.read_only_level": {
        "en_us": u"its level is read-only, driven by a host, a room boundary "
                 u"or a system",
        "ru": u"уровень только для чтения — задан host-элементом, границей "
               u"помещения или системой",
        "es_es": u"su nivel es de solo lectura: lo define un anfitrión, un "
                 u"límite de estancia o un sistema",
    },
    "skip.no_offset": {
        "en_us": u"its height above the level cannot be adjusted, so the level "
                 u"change would move it",
        "ru": u"высоту над уровнем отрегулировать нельзя, смена уровня сдвинула "
               u"бы элемент",
        "es_es": u"su altura sobre el nivel no se puede ajustar, así que el "
                 u"cambio de nivel lo movería",
    },
    "skip.unplaced": {
        "en_us": u"it is not assigned to a level",
        "ru": u"не привязан к уровню",
        "es_es": u"no está asignado a un nivel",
    },
    "skip.grouped": {
        "en_us": u"it belongs to a model group and can only change level inside "
                 u"group edit",
        "ru": u"принадлежит модели-группе, уровень меняется только в режиме "
               u"редактирования группы",
        "es_es": u"pertenece a un modelo de grupo y solo puede cambiar de nivel "
                 u"editando el grupo",
    },
    "skip.is_group": {
        "en_us": u"it is a model group, whose level moves its members",
        "ru": u"это модель-группа, её уровень перемещает содержимое",
        "es_es": u"es un modelo de grupo, cuyo nivel mueve sus miembros",
    },
    "skip.would_move": {
        "en_us": u"Revit still moved it up or down, so the change was undone",
        "ru": u"Revit всё равно сдвинул его по высоте, поэтому изменение отменено",
        "es_es": u"Revit lo movió igualmente en altura, así que se deshizo el cambio",
    },
    "skip.same_level": {
        "en_us": u"already on the target level",
        "ru": u"уже на целевом уровне",
        "es_es": u"ya está en el nivel de destino",
    },
})


# A level parameter and the offset that goes with it, as a pair.
#
# They have to be matched together, never one at a time: Revit's built-in
# parameter list is full of parameters that an element exposes and happily
# accepts a value on without them meaning anything for that element.  A door,
# a column and a desk all expose a writable FLOOR_HEIGHTABOVELEVEL_PARAM,
# which has no effect on any of them, and all three also expose the offset
# that does belong to them.  Looking the two up independently therefore picks
# the wrong offset for most categories and silently changes nothing while the
# element still moves.  A pair is used only when the element exposes *both*
# halves and both are writable.
#
# The names are given as strings and resolved at import, because they are not
# the same on every Revit version -- ELEVATION_ATTR does not exist on 2021,
# STAIRS_BASE_OFFSET_PARAM is absent there too, and older revisions spell the
# wall offset WALL_BASE_OFFSET rather than WALL_BASE_OFFSET_PARAM.  A pair the
# running version does not have is simply dropped.
def _existing(pairs):
    """Resolve ``(level, offset)`` name pairs this Revit version actually has."""
    resolved = []
    for level_name, offset_name in pairs:
        if hasattr(DB.BuiltInParameter, level_name) \
                and hasattr(DB.BuiltInParameter, offset_name):
            resolved.append((getattr(DB.BuiltInParameter, level_name),
                             getattr(DB.BuiltInParameter, offset_name)))
    return tuple(resolved)


LEVEL_OFFSET_PAIRS = _existing((
    # walls: "Base Constraint" + "Base Offset"
    ("WALL_BASE_CONSTRAINT", "WALL_BASE_OFFSET"),
    # roofs: "Base Level" + "Base Offset From Level"
    ("ROOF_BASE_LEVEL_PARAM", "ROOF_LEVEL_OFFSET_PARAM"),
    # columns: "Base Level" + "Base Offset"
    ("FAMILY_BASE_LEVEL_PARAM", "FAMILY_BASE_LEVEL_OFFSET_PARAM"),
    # family instances: "Level" + "Elevation from Level"
    ("FAMILY_LEVEL_PARAM", "INSTANCE_ELEVATION_PARAM"),
    # floors and ceilings: "Level" + the height above it
    ("LEVEL_PARAM", "FLOOR_HEIGHTABOVELEVEL_PARAM"),
    ("LEVEL_PARAM", "CEILING_HEIGHTABOVELEVEL_PARAM"),
    # stairs
    ("STAIRS_BASE_LEVEL_PARAM", "STAIRS_BASE_OFFSET_PARAM"),
    ("STAIRS_BASE_LEVEL_PARAM", "STAIRS_BASE_LEVEL_OFFSET_PARAM"),
))

# Level parameters that exist but can never be written, listed only so the skip
# reason can tell "this is not a level-based element" apart from "this one is,
# but its level is driven by something else".  A room is the classic case:
# ROOM_LEVEL_ID is read-only because the level follows the room boundary.
READ_ONLY_LEVEL_PARAMS = tuple(
    getattr(DB.BuiltInParameter, name)
    for name in ("ROOM_LEVEL_ID", "SPACE_LEVEL_ID", "AREA_LEVEL_ID")
    if hasattr(DB.BuiltInParameter, name)
)

# Feet.  Well below any offset Revit can store, but far enough above the noise
# of the round-trip through the parameter.
TOLERANCE = 0.000001

# How far the base of an element is allowed to drift before the change is
# undone, in feet.  0.1 mm.
Z_TOLERANCE = 0.0004

REASON_NO_LEVEL = "skip.no_level"
REASON_READ_ONLY_LEVEL = "skip.read_only_level"
REASON_NO_OFFSET = "skip.no_offset"
REASON_UNPLACED = "skip.unplaced"
REASON_GROUPED = "skip.grouped"
REASON_IS_GROUP = "skip.is_group"
REASON_WOULD_MOVE = "skip.would_move"
REASON_SAME_LEVEL = "skip.same_level"


class ReLevelResult(object):
    """What one run of the tool did: the moved count and why the rest stayed.

    Attributes:
        moved (int): number of elements put on the new level.
        unchanged (int): number already on the new level.
        skipped (list): ``(label, reason)`` pairs for everything left alone.
    """

    def __init__(self):
        self.moved = 0
        self.unchanged = 0
        self.skipped = []


def collect_levels(doc):
    """Return every level of the project, base to top.

    Collected by class, and without an element-type filter: a Level is an
    instance, so asking for types drops every level.  A category-based
    collector is no good either, because ``OST_Levels`` also covers level head
    symbols, and that returns symbol types instead of levels.

    Args:
        doc (DB.Document): the active document.

    Returns:
        (list[DB.Level]): levels ordered by elevation.
    """
    levels = DB.FilteredElementCollector(doc) \
        .OfClass(DB.Level) \
        .ToElements()
    return sorted(levels, key=level_elevation)


def level_elevation(level):
    """Return the elevation of a level in feet, from its own parameter.

    Read from the parameter rather than the ``Elevation`` property, because a
    level head symbol collected by category is a ``LevelType``, which has the
    parameter but not the property.

    Args:
        level (DB.Level): the level to measure.

    Returns:
        (float): elevation in feet.
    """
    return level.get_Parameter(
        DB.BuiltInParameter.LEVEL_ELEV).AsDouble()


def format_level_label(level):
    """Return ``Name  (elevation)`` so the picker can be read at a glance.

    Args:
        level (DB.Level): the level to describe.

    Returns:
        (str): display label for the level picker.
    """
    try:
        text = level.get_Parameter(
            DB.BuiltInParameter.LEVEL_ELEV).AsValueString()
    except Exception:
        text = '{:.2f} ft'.format(level_elevation(level))
    return u'{}  ({})'.format(level.Name, text)


def _writable(element, candidates, storage_type):
    """Return the first candidate parameter that exists, is writable and typed.

    Args:
        element (DB.Element): the element to inspect.
        candidates (tuple): BuiltInParameter values in order of preference.
        storage_type (DB.StorageType): type the parameter has to report.

    Returns:
        (DB.Parameter): the parameter, or None when the element has none.
    """
    for candidate in candidates:
        parameter = _readable(element, candidate)
        if parameter is not None and not parameter.IsReadOnly:
            try:
                if parameter.StorageType == storage_type:
                    return parameter
            except Exception:
                continue
    return None


def _readable(element, candidate):
    """Return the element's parameter for a BuiltInParameter, or None."""
    try:
        return element.get_Parameter(candidate)
    except Exception:
        return None


def _level_offset_pair(element):
    """Return the ``(level, offset)`` parameter pair that governs this element.

    Args:
        element (DB.Element): the element to inspect.

    Returns:
        (tuple): the two writable parameters, or None when the element has no
        complete pair.
    """
    for level_bip, offset_bip in LEVEL_OFFSET_PAIRS:
        level_param = _writable(element, (level_bip,), DB.StorageType.ElementId)
        if level_param is None:
            continue
        offset_param = _writable(element, (offset_bip,), DB.StorageType.Double)
        if offset_param is not None:
            return level_param, offset_param
    return None


def _has_level_param(element):
    """True when the element has a level parameter, writable or not.

    Covers the pairs above plus the parameters that are read-only by design, so
    that a room is reported as "its level is read-only" rather than as "it has
    no level".
    """
    for level_bip, _ in LEVEL_OFFSET_PAIRS:
        if _readable(element, level_bip) is not None:
            return True
    for candidate in READ_ONLY_LEVEL_PARAMS:
        if _readable(element, candidate) is not None:
            return True
    return False


def has_own_level(element):
    """True when this element has a level of its own that belongs to it.

    This is what decides whether the element may be picked at all.  A level
    parameter is the mark of a level-based element, and plenty of things share
    a *model* category without being one:

    * materials and the material assets, which Revit files under the model
      category type even though they are not geometry;
    * family types, wall types, level types and every other element type --
      picking a type would change the template, not the model;
    * project information, view settings, grids, and elements whose level is
      only an annotation, none of which carry an elevation.

    An element that has a level but cannot be re-levelled -- a room, whose
    level follows its boundary, a desk from a level-based family, or a model
    group, whose level moves its members -- still passes, so the user can
    select it and be told why it was left alone.
    """
    try:
        if isinstance(element, DB.ElementType):
            return False
    except Exception:
        pass
    try:
        if element.Category is None:
            return False
    except Exception:
        return False
    if _is_model_group(element):
        return True
    return _has_level_param(element)


def _is_model_group(element):
    """True for a model group, as opposed to a detail group or a member."""
    if not isinstance(element, DB.Group):
        return False
    try:
        return id_value(element.Category.Id)             == int(DB.BuiltInCategory.OST_IOSModelGroups)
    except Exception:
        return False


class LevelBasedElementFilter(ISelectionFilter):
    """Pick filter allowing only elements that have a level of their own.

    Used by PickObjects so that the cursor cannot land on a material, a family
    type, a grid or a view, which would otherwise come back in the selection
    and be reported as skips.
    """

    def AllowElement(self, element):
        return has_own_level(element)

    def AllowReference(self, reference, position):
        return False


def split_selection(doc, element_ids):
    """Split a selection into the elements this tool can work on and the rest.

    A pre-selection made in the ribbon is not filtered by PickObjects, so it can
    still contain materials or types; this drops them here instead of letting
    them turn into a wall of skip messages.

    Args:
        doc (DB.Document): the active document.
        element_ids (iterable): ElementIds to sort out.

    Returns:
        (tuple): the ElementIds to re-level, and how many were left out.
    """
    usable = []
    ignored = 0
    for element_id in element_ids:
        element = doc.GetElement(element_id)
        if element is None:
            continue
        if has_own_level(element):
            usable.append(element_id)
        else:
            ignored += 1
    return usable, ignored


def _missing_pair_reason(element):
    """Explain why no level/offset pair could be used on this element.

    Args:
        element (DB.Element): the element to inspect.

    Returns:
        (str): the reason key for the skip.
    """
    if not _has_level_param(element):
        return REASON_NO_LEVEL
    for level_bip, offset_bip in LEVEL_OFFSET_PAIRS:
        level_param = _readable(element, level_bip)
        if level_param is None:
            continue
        if level_param.IsReadOnly:
            return REASON_READ_ONLY_LEVEL
        offset_param = _readable(element, offset_bip)
        if offset_param is None or offset_param.IsReadOnly:
            return REASON_NO_OFFSET
    return REASON_READ_ONLY_LEVEL


def element_base_z(element):
    """Return the lowest Z of an element, used to prove it did not move.

    Args:
        element (DB.Element): the element to measure.

    Returns:
        (float): the bottom of the element's model extents, or None when the
        element has no usable bounding box.
    """
    try:
        box = element.get_BoundingBox(None)
    except Exception:
        return None
    if box is None:
        return None
    try:
        return box.Min.Z
    except Exception:
        return None


def element_label(element):
    """Best available human name for an element, for the skip report.

    Args:
        element (DB.Element): the element to name.

    Returns:
        (str): the element name, else its category, else its id.
    """
    try:
        if element.Name:
            return element.Name
    except Exception:
        pass
    try:
        return element.Category.Name
    except Exception:
        return str(id_value(element.Id))


def change_level(doc, element, target_level):
    """Put one element on `target_level`, compensating its offset so Z holds.

    Args:
        doc (DB.Document): the active document.
        element (DB.Element): the element to re-level.
        target_level (DB.Level): the level to move it to.

    Returns:
        (str): None when the element moved, otherwise the skip reason key.
    """
    # A group moves its members when its level is written, and a member cannot
    # be written at all outside group edit mode.
    if isinstance(element, DB.Group):
        return REASON_IS_GROUP
    if id_value(element.GroupId) > 0:
        return REASON_GROUPED

    pair = _level_offset_pair(element)
    if pair is None:
        return _missing_pair_reason(element)
    level_param, offset_param = pair

    try:
        level_id = level_param.AsElementId()
        if id_value(level_id) < 0:
            return REASON_UNPLACED
        current_level = doc.GetElement(level_id)
        current_offset = offset_param.AsDouble()
    except Exception:
        return REASON_UNPLACED

    if current_level is None:
        return REASON_UNPLACED
    # ElementId does not overload ==, so compare the value, not the reference.
    if id_value(current_level.Id) == id_value(target_level.Id):
        return REASON_SAME_LEVEL

    # The base has to land on the same absolute elevation, so the offset takes
    # up whatever the level change took away.
    new_offset = (level_elevation(current_level) + current_offset) \
        - level_elevation(target_level)
    if abs(new_offset - current_offset) < TOLERANCE:
        return REASON_SAME_LEVEL

    base_before = element_base_z(element)
    if _write(level_param, offset_param, target_level.Id, new_offset) is None:
        _restore(level_param, offset_param, level_id, current_offset)
        return REASON_NO_OFFSET

    if base_before is not None:
        doc.Regenerate()
        base_after = element_base_z(element)
        if base_after is not None and abs(base_after - base_before) > Z_TOLERANCE:
            # The parameters said one thing and the geometry another: the
            # element would have moved in Z, so undo it rather than lie.
            _restore(level_param, offset_param, level_id, current_offset)
            return REASON_WOULD_MOVE
    return None


def _write(level_param, offset_param, level_id, offset):
    """Write the level and the offset, returning the offset that stuck.

    Returns:
        (float): the offset Revit actually stored, or None when it refused.
    """
    try:
        level_param.Set(level_id)
    except Exception:
        return None
    try:
        offset_param.Set(offset)
        return offset_param.AsDouble()
    except Exception:
        return None


def _restore(level_param, offset_param, level_id, offset):
    """Undo a level change that did not hold its Z, or was only half written.

    The two writes are independent, so a refused offset still gets its level
    put back.
    """
    try:
        level_param.Set(level_id)
    except Exception:
        pass
    try:
        offset_param.Set(offset)
    except Exception:
        pass


def change_levels(doc, target_level, element_ids):
    """Re-level a whole selection in one transaction.

    Args:
        doc (DB.Document): the active document.
        target_level (DB.Level): the level to move the elements to.
        element_ids (iterable): ElementIds to re-level.

    Returns:
        (ReLevelResult): what moved, what was already there, and what was
        skipped and why.
    """
    result = ReLevelResult()
    with WrappedTransaction(doc, S("transaction"), warning_suppressor=True):
        for element_id in element_ids:
            element = doc.GetElement(element_id)
            if element is None:
                continue
            reason = change_level(doc, element, target_level)
            if reason is None:
                result.moved += 1
            elif reason == REASON_SAME_LEVEL:
                result.unchanged += 1
            else:
                result.skipped.append((element_label(element), reason))
    return result


def format_summary(result, target_level, ignored=0, limit=8):
    """Build the message shown once the transaction is done.

    Args:
        result (ReLevelResult): the outcome of the run.
        target_level (DB.Level): the level the elements were sent to.
        ignored (int): selected objects dropped for having no level.
        limit (int): how many skipped elements to name before counting the rest.

    Returns:
        (str): the localized report.
    """
    lines = []
    if result.moved:
        lines.append(S("done.moved", result.moved, target_level.Name))
    else:
        lines.append(S("done.none"))
    if result.unchanged:
        lines.append(S("done.unchanged", result.unchanged))
    if ignored:
        lines.append(S("done.ignored", ignored))

    if result.skipped:
        lines.append('')
        lines.append(S("done.skipped", len(result.skipped)))
        for label, reason in result.skipped[:limit]:
            lines.append(u'- {}: {}'.format(label, S(reason)))
        remaining = len(result.skipped) - limit
        if remaining > 0:
            lines.append(S("done.more", remaining))
    return '\n'.join(lines)
