# -*- coding: utf-8 -*-
"""Draw the Review Worksets icon pair from scratch.

Same contract as ``make_level_icon.py``: a 96x96 transparent glyph, written
twice, tinted black for the light ribbon and white for the dark one.

The glyph is a list of worksets with a check mark over it: three horizontal
rows on the left, a bold check on the right.  Two mark groups, nothing else,
because at 16px anything more turns into a grey smear.  Requires Pillow
(CPython, build time only).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

SIZE = 96
SCALE = 8

# The workset rows: three bars of the same length, one per row of a list.
ROWS = (
    (6, 18, 42, 28),
    (6, 43, 42, 53),
    (6, 68, 42, 78),
)

# The check mark, drawn as a polyline with a round joint.  It is big on
# purpose: at 16px a small check turns into a blob, so it takes the space
# the rows leave and reads as a check on its own.
CHECK = ((50, 48), (62, 63), (89, 24))
CHECK_WIDTH = 12


def scaled(points):
    return [(x * SCALE, y * SCALE) for x, y in points]


def build_mask():
    big = SIZE * SCALE
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)

    for x0, y0, x1, y1 in ROWS:
        draw.rectangle(scaled([(x0, y0), (x1, y1)]), fill=255)

    points = scaled(CHECK)
    draw.line(points, fill=255, width=CHECK_WIDTH * SCALE, joint="curve")
    for x, y in points:
        radius = CHECK_WIDTH * SCALE / 2.0
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=255)

    # Just enough blur to take the staircase off the downscaled edge.
    mask = mask.filter(ImageFilter.GaussianBlur(SCALE * 0.25))
    return mask.resize((SIZE, SIZE), Image.LANCZOS)


def colored(mask, rgb):
    image = Image.new("RGBA", mask.size, rgb + (0,))
    image.putalpha(mask)
    return image


def main(output_dir):
    mask = build_mask()
    colored(mask, (0, 0, 0)).save(os.path.join(output_dir, "icon.png"))
    colored(mask, (255, 255, 255)).save(os.path.join(output_dir, "icon.dark.png"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python make_workset_icon.py <output_dir>")
    main(sys.argv[1])
