"""Compose a pyRevit light/dark icon pair from a base logo plus the batch overlay.

Usage:
    python make_batch_icon.py <base.png> <output_dir> [--scale-base] [--badge N]

Writes <output_dir>/icon.png (black overlay) and <output_dir>/icon.dark.png
(white overlay). The base logo keeps its own colors in both files; only the
overlay flips.
"""
import argparse
import os

from PIL import Image, ImageChops, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.join(HERE, "batch-overlay.png")

SIZE = 96
BASE_BOX = 64
BADGE_BOX = 46
KNOCKOUT = 5


def resize_rgba(im, size):
    w, h = im.size
    r, g, b, a = im.split()
    prem = Image.merge("RGB", (r, g, b))
    px = prem.load()
    apx = a.load()
    for y in range(h):
        for x in range(w):
            al = apx[x, y] / 255.0
            pr, pg, pb = px[x, y]
            px[x, y] = (int(pr * al), int(pg * al), int(pb * al))
    prem = prem.resize(size, Image.LANCZOS)
    an = a.resize(size, Image.LANCZOS)
    ppx, anpx = prem.load(), an.load()
    out = Image.new("RGBA", size)
    opx = out.load()
    for y in range(size[1]):
        for x in range(size[0]):
            al = anpx[x, y]
            if al == 0:
                opx[x, y] = (0, 0, 0, 0)
                continue
            f = 255.0 / al
            pr, pg, pb = ppx[x, y]
            opx[x, y] = (min(255, int(pr * f)), min(255, int(pg * f)),
                         min(255, int(pb * f)), al)
    return out


def fit(im, box):
    w, h = im.size
    s = min(box / float(w), box / float(h))
    return resize_rgba(im, (max(1, int(round(w * s))), max(1, int(round(h * s)))))


def build(base, badge, dark):
    pos = (SIZE - badge.size[0], SIZE - badge.size[1])

    knock = Image.new("L", (SIZE, SIZE), 0)
    knock.paste(badge.split()[3], pos)
    knock = knock.filter(ImageFilter.MaxFilter(KNOCKOUT))
    knock = knock.filter(ImageFilter.GaussianBlur(0.6))
    knock = Image.eval(knock, lambda v: 255 if v > 40 else 0)

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(base, (0, 0))
    canvas.putalpha(ImageChops.multiply(canvas.split()[3], ImageChops.invert(knock)))

    tint = (255, 255, 255) if dark else (0, 0, 0)
    glyph = Image.new("RGBA", badge.size, tint + (0,))
    glyph.putalpha(badge.split()[3])
    canvas.alpha_composite(glyph, pos)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("output_dir")
    ap.add_argument("--scale-base", action="store_true",
                    help="shrink the base into the top-left instead of keeping it full canvas")
    ap.add_argument("--badge", type=int, default=BADGE_BOX)
    args = ap.parse_args()

    base = Image.open(args.base).convert("RGBA")
    if args.scale_base or base.size != (SIZE, SIZE):
        base = base.crop(base.split()[3].getbbox())
        base = fit(base, BASE_BOX)

    badge = Image.open(OVERLAY).convert("RGBA")
    badge = badge.crop(badge.split()[3].getbbox())
    badge = fit(badge, args.badge)

    build(base, badge, False).save(os.path.join(args.output_dir, "icon.png"))
    build(base, badge, True).save(os.path.join(args.output_dir, "icon.dark.png"))
    print("wrote icon.png and icon.dark.png to " + args.output_dir)


if __name__ == "__main__":
    main()
