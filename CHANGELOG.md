# Changelog

This file highlights changes that affect pyArchitect users. Technical commit
and pull-request details are added automatically to each GitHub release.

## [Unreleased]

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
