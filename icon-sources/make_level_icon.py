# -*- coding: utf-8 -*-
"""Draw the Swap Level icon pair from scratch.

Same contract as ``make_convert_icon.py``: a 96x96 transparent glyph, written
twice, tinted black for the light ribbon and white for the dark one.

The glyph is three marks and nothing else: two level lines with a solid element
floating between them, clear of both.  The first version also drew an outlined
box and a double-headed measurement arrow, which is four marks competing at
16px -- in the ribbon it collapsed into two grey stripes.  Fewer, fatter,
filled marks are what survive a 16px downscale, and the tooltip is where the
detail belongs.  Requires Pillow (CPython, build time only).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFilter

SIZE = 96
SCALE = 8

# The vertical budget, in 96ths of the canvas.  Downscale to 16px and these
# become a 1.3px line, a 2px gap and a 5px block -- which is the least a ribbon
# icon can be made of and still read.  Widen the gaps and the block disappears
# into the lines; narrow them and they merge at 16px.
BAR = 8               # thickness of a level line
GAP = 12              # clear space the block has to keep from both lines
BLOCK = 32            # the element itself
BAR_TOP = 12          # distance from the top of the canvas to the first line
LEVEL_X0 = 10
LEVEL_X1 = 86

LEVEL_Y = (BAR_TOP + BAR // 2,
           BAR_TOP + BAR + GAP + BLOCK + GAP + BAR // 2)
BLOCK_BOX = ((SIZE - BLOCK) // 2,
             BAR_TOP + BAR + GAP,
             (SIZE - BLOCK) // 2 + BLOCK,
             BAR_TOP + BAR + GAP + BLOCK)


def scaled(points):
    return [(x * SCALE, y * SCALE) for x, y in points]


def build_mask():
    big = SIZE * SCALE
    mask = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(mask)

    for y in LEVEL_Y:
        draw.line(scaled([(LEVEL_X0, y), (LEVEL_X1, y)]), fill=255, width=BAR * SCALE)

    x0, y0, x1, y1 = BLOCK_BOX
    draw.rectangle(scaled([(x0, y0), (x1, y1)]), fill=255)

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
        sys.exit("usage: python make_level_icon.py <output_dir>")
    main(sys.argv[1])
