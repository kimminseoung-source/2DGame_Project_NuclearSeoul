"""A Korean back-street house front as hand-placed dot art (2026-11-16, after the furniture: "이대로
가자"): red brick walls, windows with security bars (방범창), a steel front door under a small
canopy, a flat roof in green waterproof paint behind a concrete parapet - the 다세대 / 단독 look of
Dongja-dong. Pieces are drawn pixel by pixel at ~19 px a metre; tools/map/house.py lays them out.
"""
import random

from PIL import Image, ImageChops, ImageFilter

INK = (28, 24, 22)
BRICK = ((146, 74, 54), (128, 62, 46), (112, 54, 40), (98, 46, 34))
MORTAR = (92, 80, 70)
CONCRETE = ((150, 146, 136), (124, 120, 112), (98, 94, 88))
ROOF_GREEN = ((96, 128, 100), (78, 108, 84), (64, 90, 70))
FRAME_AL = ((196, 198, 196), (150, 152, 152))
PANE = ((70, 84, 96), (52, 62, 74), (104, 122, 136))
BARS = (58, 58, 60)
STEEL = ((110, 104, 98), (88, 82, 78), (68, 64, 60))
BRASS = (186, 166, 110)


def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((x, y), c + (255,))


def rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            put(img, x, y, c)


def brick_wall(w, h, seed=0):
    """Running-bond brick, 6 x 3 px bricks with 1 px mortar, each brick a shade of its own; the top
    rows in the eave's shadow, a concrete plinth at the bottom, rain streaks."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, h), MORTAR + (255,))
    for row, y in enumerate(range(0, h, 3)):
        off = 3 if row % 2 else 0
        for x in range(-off, w, 6):
            shade = rng.choices(BRICK, weights=(1, 5, 4, 1))[0]
            rect(img, x, y, x + 4, y + 1, shade)
            if rng.random() < 0.15:                         # a lighter chipped corner
                put(img, x, y, BRICK[0])
    for y in range(min(4, h)):                              # under the eave: in shadow
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            img.putpixel((x, y), (r * 6 // 10, g * 6 // 10, b * 6 // 10, a))
    rect(img, 0, h - 4, w - 1, h - 1, CONCRETE[1])          # plinth
    rect(img, 0, h - 4, w - 1, h - 4, CONCRETE[0])
    rect(img, 0, h - 1, w - 1, h - 1, CONCRETE[2])
    return img


def window(w, h):
    """An aluminium window with two panes, a sill, and security bars over it."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rect(img, 0, 0, w - 1, h - 3, FRAME_AL[1])
    rect(img, 1, 1, w - 2, h - 4, PANE[1])
    rect(img, w // 2, 1, w // 2, h - 4, FRAME_AL[1])        # the middle rail
    for x in range(2, w - 2):                               # a sky reflection, top left of each pane
        if x < w // 2 - 1:
            put(img, x, 2, PANE[2])
    put(img, 2, 3, PANE[2]); put(img, w // 2 + 2, 2, PANE[2])
    rect(img, 1, h - 5, w - 2, h - 4, PANE[0])
    for x in range(2, w - 1, 3):                            # 방범창: bars in front
        rect(img, x, 0, x, h - 3, BARS)
    rect(img, 0, 0, w - 1, 0, BARS); rect(img, 0, (h - 3) // 2, w - 1, (h - 3) // 2, BARS)
    rect(img, -0, h - 2, w - 1, h - 2, CONCRETE[0])         # sill
    rect(img, 0, h - 1, w - 1, h - 1, CONCRETE[2])
    return img


def door(w, h):
    """A steel front door in its frame, a small concrete canopy over it and a step under it."""
    img = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
    rect(img, 0, 0, w + 3, 1, CONCRETE[0])                  # canopy
    rect(img, 0, 2, w + 3, 2, CONCRETE[2])
    rect(img, 1, 3, w + 2, 3, (40, 34, 30))                 # its shadow
    rect(img, 2, 3, w + 1, h + 1, INK)                      # frame
    rect(img, 3, 4, w, h + 1, STEEL[1])
    rect(img, 3, 4, 3, h + 1, STEEL[0])                     # lit edge
    rect(img, w, 4, w, h + 1, STEEL[2])
    for y in (h // 3 + 2, 2 * h // 3 + 2):                  # pressed panels
        rect(img, 5, y, w - 2, y, STEEL[2])
    put(img, w - 2, h // 2 + 3, BRASS); put(img, w - 2, h // 2 + 4, BRASS)    # handle and lock
    put(img, w - 2, h // 2 + 1, (60, 56, 50))
    rect(img, 0, h + 2, w + 3, h + 3, CONCRETE[1])          # step
    rect(img, 0, h + 2, w + 3, h + 2, CONCRETE[0])
    return img


CONC_WALL = ((168, 164, 154), (146, 142, 134), (122, 118, 112), (96, 92, 88))
ROOF_GREY = ((132, 130, 124), (116, 114, 108), (96, 94, 90))


def office_wall(w, h, seed=0):
    """A big building's front (campus halls, offices): concrete panels with bands of windows,
    each floor 3.2 m (~60 px), the ground floor darker."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (w, h), CONC_WALL[1] + (255,))
    for y in range(0, h, 12):                               # panel joints
        rect(img, 0, y, w - 1, y, CONC_WALL[2])
    for x in range(0, w, 19):
        rect(img, x, 0, x, h - 1, CONC_WALL[2])
    floor_px, band = 61, 26                                 # a floor is 3.2 m; its windows 1.4 m tall
    band_top = h - 4 - floor_px + 14                        # from the ground floor up
    while band_top >= 3:
        rect(img, 0, band_top, w - 1, band_top + band - 1, PANE[1])
        rect(img, 0, band_top, w - 1, band_top, CONC_WALL[3])          # the shadow under the slab
        for x in range(0, w, 10):                           # mullions, a pane about half a metre
            rect(img, x, band_top, x, band_top + band - 1, FRAME_AL[1])
        rect(img, 0, band_top + band // 2, w - 1, band_top + band // 2, FRAME_AL[1])   # transom
        for x in range(2, w - 2, 10):                       # sky in some panes, a few broken
            if rng.random() < 0.5:
                rect(img, x, band_top + 2, x + 3, band_top + 2, PANE[2])
            if rng.random() < 0.06:
                rect(img, x + 1, band_top + band // 2 + 2, x + 6, band_top + band - 3, (24, 26, 30))
        rect(img, 0, band_top + band, w - 1, band_top + band, CONC_WALL[0])  # the sill
        band_top -= floor_px
    for y in range(min(3, h)):                              # under the roof edge: in shadow
        for x in range(w):
            r, g, b, a = img.getpixel((x, y))
            img.putpixel((x, y), (r * 7 // 10, g * 7 // 10, b * 7 // 10, a))
    rect(img, 0, h - 3, w - 1, h - 1, CONC_WALL[3])         # plinth
    return img


def office_roof(mask, seed=0):
    """A big flat roof: grey membrane, a parapet, an air vent box or two."""
    rng = random.Random(seed)
    w, h = mask.size
    img = flat_roof(mask, seed)
    grey = Image.new("RGBA", (w, h), ROOF_GREY[1] + (255,))
    for _ in range(w * h // 300):
        x, y = rng.randrange(w), rng.randrange(h)
        rect(grey, x, y, x + rng.randint(2, 6), y, rng.choice((ROOF_GREY[0], ROOF_GREY[2])))
    padded = Image.new("L", (w + 6, h + 6), 0)
    padded.paste(mask, (3, 3))
    inner = padded.filter(ImageFilter.MinFilter(5)).crop((3, 3, w + 3, h + 3))
    img.paste(grey, (0, 0), inner)                          # grey inside the parapet
    for _ in range(max(1, w * h // 6000)):                  # vent boxes on the roof
        x, y = rng.randrange(6, max(7, w - 14)), rng.randrange(6, max(7, h - 12))
        if inner.getpixel((min(w - 1, x + 8), min(h - 1, y + 7))):
            rect(img, x, y, x + 7, y + 3, CONCRETE[0])
            rect(img, x, y + 4, x + 7, y + 6, CONCRETE[2])
            rect(img, x + 8, y + 1, x + 9, y + 6, (60, 58, 56))   # its shadow
    return img


def flat_roof(mask, seed=0):
    """A flat roof: green waterproof paint inside a concrete parapet, a few stains."""
    rng = random.Random(seed)
    w, h = mask.size
    img = Image.new("RGBA", (w, h), ROOF_GREEN[1] + (255,))
    for _ in range(w * h // 400):                           # a few patches of worn paint
        x, y = rng.randrange(w), rng.randrange(h)
        c = rng.choice((ROOF_GREEN[0], ROOF_GREEN[2]))
        rect(img, x, y, x + rng.randint(2, 5), y + rng.randint(0, 1), c)
    padded = Image.new("L", (w + 6, h + 6), 0)             # so the edge of the picture counts as outside
    padded.paste(mask, (3, 3))

    def shrink(m, k):
        return m.filter(ImageFilter.MinFilter(k))
    inner = shrink(padded, 5).crop((3, 3, w + 3, h + 3))
    rim = ImageChops.subtract(mask, inner)                  # the parapet, 2 px
    img.paste(CONCRETE[0] + (255,), (0, 0, w, h), rim)
    outer = ImageChops.subtract(mask, shrink(padded, 3).crop((3, 3, w + 3, h + 3)))
    img.paste(CONCRETE[1] + (255,), (0, 0, w, h), outer)    # its outer edge a step darker
    edge = ImageChops.subtract(inner, shrink(padded, 7).crop((3, 3, w + 3, h + 3)))
    img.paste(ROOF_GREEN[2] + (255,), (0, 0, w, h), edge)   # the parapet's shadow on the roof
    drain_x, drain_y = w - 6, 4                             # a rusty drain in a corner
    rect(img, drain_x, drain_y, drain_x + 1, drain_y + 1, (60, 48, 40))
    return img
