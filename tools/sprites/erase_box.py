"""Erase a baked-in effect from a generated frame (2026-11-19: PixelLab drew a white impact puff
into the hero's strike frame; the game draws its own impact now, and the puff looked odd).

    python tools/sprites/erase_box.py <in.png> <out.png> L T R B [--keep-warm]

Removes every pixel inside the box (picture px, inclusive), except warm skin/orange ones with
--keep-warm (the fist reaching into the box), then closes the cut edge: an emptied pixel next to
what is left becomes the frame's own outline colour, so the body keeps a clean dark edge.
Nothing new is drawn: only pixels taken away and the existing outline colour extended.
"""

import colorsys
import sys
from collections import Counter

from PIL import Image


def warm(rgba):
    r, g, b, a = rgba
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return h < 0.12 and s > 0.3 and v > 0.5


def main(src, dst, l, t, r, b, keep_warm):
    im = Image.open(src).convert("RGBA")
    px = im.load()
    darks = Counter(px[x, y] for x in range(im.width) for y in range(im.height)
                    if px[x, y][3] > 200 and sum(px[x, y][:3]) < 90)
    outline = darks.most_common(1)[0][0] if darks else (20, 16, 20, 255)
    emptied = []
    for y in range(t, b + 1):
        for x in range(l, r + 1):
            if px[x, y][3] and not (keep_warm and warm(px[x, y])):
                px[x, y] = (0, 0, 0, 0)
                emptied.append((x, y))
    for x, y in emptied:
        if any(0 <= x + dx < im.width and 0 <= y + dy < im.height and px[x + dx, y + dy][3] > 200
               and px[x + dx, y + dy] != outline and (x + dx, y + dy) not in emptied
               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            px[x, y] = outline
    im.save(dst)
    print(f"{len(emptied)} px removed -> {dst}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], *map(int, a[2:6]), keep_warm="--keep-warm" in a)
