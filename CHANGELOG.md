# Changelog

This file highlights changes that affect pyArchitect users. Technical commit
and pull-request details are added automatically to each GitHub release.

## [Unreleased]

## [1.4.6]

### Changed

- Review Links is now a link doctor. Besides pinning links and moving them to
  their own `##_` workset, it renames a link's workset when the linked file
  was renamed, and creates one when the old workset is shared with other
  links. It also deletes empty link worksets left behind by old links (Revit
  2022 and newer). A click applies every fix and lists what it did;
  Shift+click shows the fixes first so you can untick the ones you don't
  want. A single undo reverts the whole run. A fix that cannot be applied,
  for example on a link another user is editing, is skipped and listed
  without undoing the others.

### Fixed

- Wall finishing closes its corners at any angle, not only at right angles,
  with no gaps and nothing sticking into the room. Sharp outside corners and
  the tips of thin walls are wrapped with a mitred corner.
- Host walls now cut the wall finishing joined to them, instead of the
  finishing cutting into the wall at corners.
- Floor, ceiling and wall finishing work on Revit 2026.
- Floor finishing door notches use the room's own phase.
- Ceiling finishing on Revit 2021 is placed at the room height.
- Floor and ceiling finishing no longer stop with an error when Revit
  removes one of the new elements.
- Swap Level moves elements between two levels at the same elevation.
- Batch export reuses a model that is already open instead of opening it
  again, and removes its temporary copy when a model fails to open.
- Batch IFC Export exports each linked model once, and no longer saves
  models opened without their links, since only a temporary copy is open.

## [1.4.5]

### Added

- Batch IFC Export accepts a Revit IFC setup file globally or per model; a
  per-model property set file overrides the one in the setup.
- The batch IFC options show the IFC version and export settings read from
  the selected setup file, and restore your own settings when it is cleared.

### Changed

- Batch IFC Export no longer skips a model whose default export view is
  missing: it exports with another 3D view in the model, or with a temporary
  3D view that is deleted afterwards when the model has none.

### Fixed

- IFC setup files load on Revit 2027.
- Text boxes and drop-downs in the batch export options are the same height
  as the folder and file pickers next to them.

- Batch IFC Export validates saved setup paths before closing settings, keeps
  per-view exports filtered, and rejects conflicting linked-model options.
- Conflicting linked-model export options report whether links are unloaded
  or already exported by the saved IFC setup.
- Linked IFC exports no longer inherit host-only property set overrides or
  document IDs from the saved setup.
- IFC setup loading searches user-installed exporters and custom Revit install
  folders, prefers a loaded bundle override, and reports unsupported exporter
  document context instead of silently omitting property sets.

## [1.4.4]

### Added

- Swap Level: moves the selected elements to another level and adjusts their
  offset so they stay at exactly the same height. Works on walls, floors,
  ceilings, roofs, columns, stairs, and family instances, including doors and
  windows hosted in a wall. Rooms, model groups and their members, and
  anything whose level or offset cannot be changed are left alone and listed
  at the end, and any element Revit would still have moved is put back.

## [1.4.3]

### Fixed

- Wall, floor, and ceiling finishing no longer fail with "'FamilySymbol'
  object has no attribute 'Kind'" in projects that contain in-place or
  loadable families of those categories.

## [1.4.2]

### Added

- Convert In-Place to Family: turns one model-in-place component into a
  loadable family with its final solid geometry, places it at the same
  position and level, keeps its phase, workset, Mark, and Comments, and only
  then removes the original. It uses the Generic Model family template by
  default; Shift+Click chooses a different default family template.
- Finishing floors, walls, and ceilings can write the source room number or
  name into a text parameter of your choice.
- Wall finishing options to join the new walls with their host walls (on by
  default) and to allow wall joins at their ends.

### Changed

- Batch IFC Export and Batch NavisView interfaces and messages are now
  available in English, Spanish, and Russian.
- Batch IFC Export and Batch NavisView results now appear in the pyRevit
  output window, with warnings sent to pyRevit's standard log.
- Wall finishing creates one wall per straight run of the same host type
  instead of one per boundary fragment.
- Floor finishing door notches use the larger of the door's Width and Rough
  Width, so the floor always covers the opening.
- Wall finishing walls are no longer room-bounding, so room areas and
  boundaries stay at the structural walls.

### Fixed

- Wall finishing no longer raises "Can't keep elements joined", and its
  corners join cleanly with each other and with the perpendicular host walls
  instead of leaving one corner unjoined, overlapping, or notched.
- Floor and ceiling finishing in rooms that already have wall finishing now
  reach the structural walls and keep their door notches, and are joined with
  any wall finishing they overlap.

### Removed

- Custom batch report files and the report-folder option.
