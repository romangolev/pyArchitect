# -*- coding: utf-8 -*-
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SIZE = 96
SCALE = 8
STROKE = 6

CUBE_TOP = (42, 6)
CUBE_UPPER_RIGHT = (72, 23)
CUBE_LOWER_RIGHT = (72, 58)
CUBE_BOTTOM = (42, 75)
CUBE_LOWER_LEFT = (12, 58)
CUBE_UPPER_LEFT = (12, 23)
CUBE_CENTER = (42, 40)

BADGE_CENTER = (71, 71)
BADGE_RADIUS = 22
BADGE_GAP = 4

ARROW_SHAFT = [(59, 71), (77, 71)]
ARROW_SHAFT_WIDTH = 6
ARROW_HEAD = [(73, 60), (85, 71), (73, 82)]


def scaled(points):
    return [(x * SCALE, y * SCALE) for x, y in points]


def stroke(draw, points, closed=False):
    if closed:
        points = points + points[:1]
    width = STROKE * SCALE
    draw.line(scaled(points), fill=255, width=width, joint="curve")
    radius = width / 2.0
    for x, y in scaled(points):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)


def circle(draw, center, radius, fill):
    x, y = center[0] * SCALE, center[1] * SCALE
    r = radius * SCALE
    draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def build_mask():
    big = SIZE * SCALE

    cube = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(cube)
    stroke(draw, [CUBE_TOP, CUBE_UPPER_RIGHT, CUBE_LOWER_RIGHT, CUBE_BOTTOM,
                  CUBE_LOWER_LEFT, CUBE_UPPER_LEFT], closed=True)
    stroke(draw, [CUBE_UPPER_LEFT, CUBE_CENTER, CUBE_UPPER_RIGHT])
    stroke(draw, [CUBE_CENTER, CUBE_BOTTOM])

    knockout = Image.new("L", (big, big), 0)
    circle(ImageDraw.Draw(knockout), BADGE_CENTER, BADGE_RADIUS + BADGE_GAP, 255)
    cube = ImageChops.subtract(cube, knockout)

    badge = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(badge)
    circle(draw, BADGE_CENTER, BADGE_RADIUS, 255)
    draw.line(scaled(ARROW_SHAFT), fill=0, width=ARROW_SHAFT_WIDTH * SCALE)
    draw.polygon(scaled(ARROW_HEAD), fill=0)

    mask = ImageChops.lighter(cube, badge)
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
        sys.exit("usage: python make_convert_icon.py <output_dir>")
    main(sys.argv[1])
