# Icon sources

Source art and the generator used to build the batch-button icon pairs. Kept
here so the shipped `icon.png` / `icon.dark.png` files can be regenerated or
extended to new buttons later.

## Files

| File | What it is |
| --- | --- |
| `batch-overlay.png` | The batch glyph used as the corner overlay (icons8, Windows 11 outline), cropped to its ink, pure black on transparent. |
| `ifc-logo.png` | buildingSMART / IFC knot, 512px. The original download was a "png-clipart" with a *painted* checkerboard instead of real transparency; this copy has the background keyed out and the trailing ® removed. |
| `navisworks-n.png` | The Navisworks **N** taken from `CreateNavisView.pushbutton/icon.png` with its export-cube sub-badge cleared from the bottom-right, kept at the native 96px so it stays aligned. |
| `make_batch_icon.py` | Generator. Requires Pillow (CPython — this is a build-time script, not something pyRevit runs). |

## Usage

```
python make_batch_icon.py <base.png> <output_dir>
```

Writes `icon.png` and `icon.dark.png` into `output_dir`.

Regenerate the two current buttons:

```
python icon-sources/make_batch_icon.py icon-sources/ifc-logo.png \
    pyArchitect.tab/Batch.panel/BatchExportIFC.pushbutton
python icon-sources/make_batch_icon.py icon-sources/navisworks-n.png \
    pyArchitect.tab/Batch.panel/Navis.pushbutton
```

Both commands reproduce the checked-in icons byte-for-byte.

## How the pair is composed

- 96x96 canvas, transparent.
- The base logo keeps its own colors and is **identical** in both files — only
  the overlay flips: black in `icon.png`, white in `icon.dark.png`.
- The overlay sits in the bottom-right, 46px on the 96px canvas, i.e. roughly
  the bottom-right quarter of the icon.
- The base's alpha is knocked out by a 2px dilation of the overlay silhouette,
  so the overlay stays legible against the base on any ribbon background
  without needing a solid plate behind it.
- A base that is already exactly 96x96 is used as-is (assumed pre-composed for
  this canvas); anything else is cropped to its ink and fitted into a 64px box
  anchored top-left. Force the latter with `--scale-base`.

Downscaling goes through premultiplied alpha so edges do not pick up a halo.
