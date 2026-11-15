"""Backpack screen options after UI v2 (2026-11-16): "인벤토리 부분이 종이에 있다는 게 살짝
부자연스럽다". The items are things in a bag, so they are shown as things, not a written list:
  A. the opened backpack seen from above, the items lying inside it
  B. a tarp spread on the ground, the items laid out on it
Both keep v2's rules (640x360 pixel canvas, no anti-aliasing, Galmuri, world colours, no rounded
cards / pills / side stripes / glass) and share the body column and the key row.

usage: python tools/ui/ui_mockup_bag.py <frame dir with bg_play.png> <out dir>
"""
import random
import sys

from PIL import Image, ImageDraw, ImageFont

from ui_mockup_v2 import (BLOOD, BOLD, GREY, H, INK, LIGHT, PENCIL, REG, ROAD, W, crisp, f,
                          outlined, over, pix_icon)

CANVAS = (98, 86, 64)          # backpack canvas
CANVAS_DARK = (78, 68, 50)
CANVAS_LIGHT = (122, 108, 80)
INSIDE = (40, 35, 30)
INSIDE_FOLD = (52, 46, 38)
TARP = (84, 90, 66)            # olive ground sheet
TARP_DARK = (66, 72, 52)
TARP_LIGHT = (108, 114, 86)
ASPHALT_HI = (58, 60, 62)
METAL = (150, 152, 156)


def dim(d):
    """Dither the world darker (no smooth glass layer)."""
    for y in range(H):
        for x in range(W):
            if (x + y) % 2 == 0 or y % 2 == 0:
                d.point((x, y), fill=(6, 6, 8, 255))


def big_icon(img, name, x, y, shadow=True):
    """A 16 px icon drawn at twice the size on the same pixel grid (each icon pixel = 2x2)."""
    one = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    pix_icon(crisp(ImageDraw.Draw(one)), name, 0, 0)
    two = one.resize((32, 32), Image.NEAREST)
    if shadow:                                  # a hard shadow on what it lies on
        sh = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        sh.paste((14, 12, 10, 255), (0, 0), two)
        img.alpha_composite(sh, (x + 2, y + 2))
    img.alpha_composite(two, (x, y))


def brackets(d, box, colour=ROAD):
    """The chosen thing: four square corner marks, not a rounded highlight or a side stripe."""
    l, t, r, b = box
    for (cx, cy, sx, sy) in ((l, t, 1, 1), (r, t, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
        d.line((cx, cy, cx + 5 * sx, cy), fill=colour)
        d.line((cx, cy, cx, cy + 5 * sy), fill=colour)


def lay(img, d, name, label, n, x, y, small, chosen=False):
    """One thing lying there: the icon, its count beside it, its name under it."""
    big_icon(img, name, x, y)
    outlined(d, (x + 33, y + 19), n, small, LIGHT)
    outlined(d, (x + 16, y + 36), label, small, ROAD if chosen else LIGHT, anchor="ma")
    if chosen:
        brackets(d, (x - 7, y - 5, x + 46, y + 51))


def nearby(img, d, small, bold, rnd, nx=452, ny=110):
    """Things on the ground around the hero: still on the asphalt, beside the bag."""
    outlined(d, (nx, ny - 20), "근처", bold, LIGHT)
    d.rectangle((nx - 4, ny - 4, nx + 96, ny + 62), fill=(30, 32, 36), outline=ASPHALT_HI)
    for _ in range(110):
        d.point((rnd.randint(nx - 3, nx + 95), rnd.randint(ny - 3, ny + 61)), fill=ASPHALT_HI)
    lay(img, d, "can", "통조림", "x1", nx + 14, ny + 6, small)


def body_column(d, small, bold):
    """Left: the body, drawn in light pixel lines on the dimmed world (not on paper)."""
    l, t = 22, 42
    outlined(d, (l, t), "몸", bold, LIGHT)
    outlined(d, (l + 112, t), "58%", bold, BLOOD, anchor="ra")
    cx, cy, o = l + 30, t + 26, GREY
    d.ellipse((cx - 7, cy, cx + 7, cy + 14), outline=o)
    d.rectangle((cx - 12, cy + 17, cx + 12, cy + 58), outline=o)
    d.rectangle((cx - 19, cy + 18, cx - 14, cy + 54), outline=o)
    d.rectangle((cx + 14, cy + 18, cx + 19, cy + 54), outline=o)
    d.rectangle((cx - 11, cy + 60, cx - 2, cy + 100), outline=o)
    d.rectangle((cx + 2, cy + 60, cx + 11, cy + 100), outline=o)
    for (wx, wy) in ((cx + 16, cy + 38), (cx - 17, cy + 28)):
        d.rectangle((wx - 2, wy - 2, wx + 2, wy + 2), fill=BLOOD)
    outlined(d, (l + 62, t + 58), "오른팔", small, LIGHT)
    outlined(d, (l + 62, t + 72), "물림·피", small, BLOOD)
    outlined(d, (l + 62, t + 98), "왼팔", small, LIGHT)
    outlined(d, (l + 62, t + 112), "긁힘", small, GREY)
    outlined(d, (l, t + 146), "손", small, GREY)
    pix_icon(d, "machete", l + 18, t + 143)
    outlined(d, (l + 44, t + 146), "마체테", small, LIGHT)


def footer(d, small, bold, name, line, weight):
    """The chosen thing, its use, the keys. Square key caps, no pills."""
    y = H - 50
    outlined(d, (150, y), name, bold, ROAD)
    outlined(d, (150 + int(d.textlength(name, font=bold)) + 8, y), line, small, LIGHT)
    outlined(d, (W - 22, y), weight, small, GREY, anchor="ra")
    kx, ky = 150, y + 18
    for key, label in (("Enter", "쓰기"), ("X", "버리기"), ("F", "다 줍기"), ("WASD", "고르기"), ("Tab", "닫기")):
        kw = int(d.textlength(key, font=small)) + 5
        d.rectangle((kx, ky, kx + kw, ky + 12), fill=LIGHT, outline=INK)
        d.text((kx + 3, ky + 1), key, font=small, fill=INK)
        outlined(d, (kx + kw + 4, ky + 1), label, small, LIGHT)
        kx += kw + int(d.textlength(label, font=small)) + 16


def option_a():
    """The backpack opened, seen from above: flap thrown back, items in the dark inside."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    dim(d)
    small, bold = f(REG), f(BOLD)
    body_column(d, small, bold)
    rnd = random.Random(7)
    # the bag: straps, body, a rolled top, the flap thrown back above it
    l, t, r, b = 196, 96, 418, 272          # sized to the bag's capacity, not the screen
    d.rectangle((l + 4, t + 4, r + 4, b + 4), fill=(4, 4, 6))                    # hard drop shadow
    d.rectangle((l - 10, t + 40, l - 2, b - 30), fill=CANVAS_DARK, outline=INK)    # side straps
    d.rectangle((r + 2, t + 40, r + 10, b - 30), fill=CANVAS_DARK, outline=INK)
    d.rectangle((l, t, r, b), fill=CANVAS, outline=INK)
    for _ in range((r - l) * (b - t) // 9):                                       # canvas weave
        x, y = rnd.randint(l + 1, r - 1), rnd.randint(t + 1, b - 1)
        d.point((x, y), fill=CANVAS_DARK if (x + y) % 3 else CANVAS_LIGHT)
    for x in range(l + 4, r - 3, 2):                                              # stitching
        d.point((x, t + 4), fill=CANVAS_LIGHT)
        d.point((x, b - 4), fill=CANVAS_LIGHT)
    for y in range(t + 4, b - 3, 2):
        d.point((l + 4, y), fill=CANVAS_LIGHT)
        d.point((r - 4, y), fill=CANVAS_LIGHT)
    # the flap thrown back over the top edge, with its buckle
    d.polygon([(l + 30, t + 1), (r - 30, t + 1), (r - 44, t - 30), (l + 44, t - 30)], fill=CANVAS_DARK, outline=INK)
    d.rectangle(((l + r) // 2 - 7, t - 26, (l + r) // 2 + 7, t - 18), outline=METAL)
    # the opening: dark inside with cloth folds
    il, it, ir, ib = l + 14, t + 14, r - 14, b - 14
    d.rectangle((il, it, ir, ib), fill=INSIDE, outline=INK)
    for k in range(4):
        y0 = it + 12 + k * 34
        d.line((il + 4, y0, il + 40 + k * 9, y0 + 6), fill=INSIDE_FOLD)
        d.line((ir - 4, y0 + 10, ir - 50 - k * 7, y0 + 14), fill=INSIDE_FOLD)
    d.line((il + 1, it + 1, ir - 1, it + 1), fill=(20, 18, 16))                  # rim shade
    outlined(d, (l, t - 46), "배낭", bold, LIGHT)
    outlined(d, (r, t - 46), "0.6 / 2.0", small, GREY, anchor="ra")
    # items lying inside (as things, not words): two bandages, a can
    lay(img, d, "bandage", "붕대", "x2", il + 20, it + 18, small, chosen=True)
    lay(img, d, "can", "통조림", "x1", il + 96, it + 30, small)
    nearby(img, d, small, bold, rnd)
    footer(d, small, bold, "붕대", "피를 멈추고 체력 +15%", "개당 0.1")
    return img


def option_b():
    """A tarp spread on the ground, the bag at its corner and the items laid out on it."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    dim(d)
    small, bold = f(REG), f(BOLD)
    body_column(d, small, bold)
    rnd = random.Random(9)
    l, t, r, b = 190, 86, 426, 262
    # the sheet: not quite square (spread by hand), hemmed, grommets, one fold line
    pts = [(l, t + 3), (r - 2, t), (r, b - 2), (l + 3, b)]
    d.polygon([(x + 3, y + 3) for x, y in pts], fill=(4, 4, 6))
    d.polygon(pts, fill=TARP, outline=INK)
    for _ in range((r - l) * (b - t) // 10):
        x, y = rnd.randint(l + 2, r - 2), rnd.randint(t + 3, b - 3)
        d.point((x, y), fill=TARP_DARK if (x * y) % 5 else TARP_LIGHT)
    for x in range(l + 6, r - 5, 3):                                              # hem stitch
        d.point((x, t + 6), fill=TARP_LIGHT)
        d.point((x, b - 5), fill=TARP_LIGHT)
    for (gx, gy) in ((l + 6, t + 7), (r - 8, t + 5), (r - 6, b - 8), (l + 8, b - 7)):
        d.rectangle((gx - 2, gy - 2, gx + 2, gy + 2), outline=METAL)
    for x in range(l + 2, r - 1):                                                 # a fold
        y = t + 104 + (x - l) // 30
        d.point((x, y), fill=TARP_DARK)
        d.point((x, y + 1), fill=TARP_LIGHT)
    outlined(d, (l, t - 18), "배낭에서 꺼낸 것", bold, LIGHT)
    outlined(d, (r, t - 18), "0.6 / 2.0", small, GREY, anchor="ra")
    # the emptied bag lying at the corner, flap open
    big_icon(img, "backpack", r - 52, t + 14)
    # items laid out in a loose row, each a little turned / apart (laid by hand, not a grid)
    lay(img, d, "bandage", "붕대", "x2", l + 26, t + 30, small, chosen=True)
    lay(img, d, "can", "통조림", "x1", l + 100, t + 40, small)
    nearby(img, d, small, bold, rnd)
    footer(d, small, bold, "붕대", "피를 멈추고 체력 +15%", "개당 0.1")
    return img


CELL = 34                      # one cell of the sheet = 0.1 weight (2.0 = 5 x 4 cells)
GRID = (5, 4)
NEAR_GRID = (3, 2)
ORANGE = (214, 128, 52)


def cells(d, x0, y0, cols, rows, dark, light):
    """Faint stitched squares: every free place reads as room left."""
    for c in range(cols):
        for r in range(rows):
            l, t = x0 + c * CELL, y0 + r * CELL
            for k in range(0, CELL - 3, 2):
                d.point((l + 2 + k, t + 2), fill=dark)
                d.point((l + 2 + k, t + CELL - 2), fill=dark)
                d.point((l + 2, t + 2 + k), fill=dark)
                d.point((l + CELL - 2, t + 2 + k), fill=dark)
            d.point((l + 3, t + 3), fill=light)


def put(img, d, name, x0, y0, col, row, w, h, chosen=False, small=None, label=None):
    """A thing taking w x h cells (its weight); the chosen one gets a lighter cell and corners."""
    l, t = x0 + col * CELL, y0 + row * CELL
    r, b = l + w * CELL, t + h * CELL
    d.rectangle((l + 2, t + 2, r - 2, b - 2), fill=TARP_LIGHT if chosen else (74, 80, 58),
                outline=(50, 54, 38))                    # its footprint: the cells it takes
    big_icon(img, name, l + (w * CELL - 32) // 2, t + (h * CELL - 32) // 2)
    if label:
        outlined(d, (r - 3, b - 13), label, small, LIGHT, anchor="ra")
    if chosen:
        brackets(d, (l, t, r, b))


def weight_bar(d, x, y, used, cap=2.0):
    """20 segments of 0.1; orange past 1.6, red past the limit (Zomboid's heavy load)."""
    colour = BLOOD if used > cap else ORANGE if used > 1.6 else ROAD
    for i in range(20):
        sx = x + i * 9
        d.rectangle((sx, y, sx + 7, y + 5), fill=colour if i < round(used * 10) else (40, 40, 38),
                    outline=INK)


def option_b_grid():
    """B refined from the ground-inventory research (GROUND_INVENTORY_UI_RESEARCH.md 2-4):
    the sheet is a 5x4 grid of 0.1 cells, things take as many cells as they weigh, a 20-segment
    weight bar, counts not names on the sheet, the ground beside it on the same grid."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    dim(d)
    small, bold = f(REG), f(BOLD)
    body_column(d, small, bold)
    rnd = random.Random(9)
    gx, gy = 212, 96                                     # grid origin on the sheet
    l, t = gx - 12, gy - 12
    r, b = gx + GRID[0] * CELL + 12, gy + GRID[1] * CELL + 12
    pts = [(l, t + 2), (r - 1, t), (r, b - 1), (l + 2, b)]
    d.polygon([(x + 3, y + 3) for x, y in pts], fill=(4, 4, 6))
    d.polygon(pts, fill=TARP, outline=INK)
    for _ in range((r - l) * (b - t) // 12):
        x, y = rnd.randint(l + 2, r - 2), rnd.randint(t + 3, b - 3)
        d.point((x, y), fill=TARP_DARK if (x * y) % 5 else TARP_LIGHT)
    for (cx, cy) in ((l + 5, t + 5), (r - 6, t + 4), (r - 5, b - 6), (l + 6, b - 5)):
        d.rectangle((cx - 2, cy - 2, cx + 2, cy + 2), outline=METAL)
    cells(d, gx, gy, *GRID, (50, 54, 38), TARP_LIGHT)
    pix_icon(d, "backpack", l, t - 30)
    outlined(d, (l + 20, t - 27), "배낭", bold, LIGHT)
    outlined(d, (r, t - 27), "0.6 / 2.0", small, LIGHT, anchor="ra")
    weight_bar(d, l + 8, b + 6, 0.6)
    put(img, d, "bandage", gx, gy, 0, 0, 1, 1, chosen=True)
    put(img, d, "bandage", gx, gy, 1, 0, 1, 1)
    put(img, d, "can", gx, gy, 2, 0, 2, 2)
    # the ground beside the sheet, same cell size, one place at a time (more with < >)
    nx, ny = r + 26, gy
    outlined(d, (nx, ny - 39), "근처", bold, LIGHT)
    outlined(d, (nx, ny - 23), "< 바닥 >", small, GREY)
    d.rectangle((nx - 4, ny - 4, nx + NEAR_GRID[0] * CELL + 4, ny + NEAR_GRID[1] * CELL + 4),
                fill=(30, 32, 36), outline=ASPHALT_HI)
    for _ in range(140):
        d.point((rnd.randint(nx - 3, nx + NEAR_GRID[0] * CELL + 3),
                 rnd.randint(ny - 3, ny + NEAR_GRID[1] * CELL + 3)), fill=ASPHALT_HI)
    cells(d, nx, ny, *NEAR_GRID, (70, 72, 76), ASPHALT_HI)
    d.rectangle((nx + 2, ny + 2, nx + 2 * CELL - 2, ny + 2 * CELL - 2), fill=(40, 42, 46), outline=(70, 72, 76))
    big_icon(img, "can", nx + (2 * CELL - 32) // 2, ny + (2 * CELL - 32) // 2)
    # the chosen thing and the keys (two rows: F picks the same kind, Shift+F everything)
    y = H - 56
    outlined(d, (150, y), "붕대", bold, ROAD)
    outlined(d, (186, y), "피를 멈추고 체력 +15%", small, LIGHT)
    outlined(d, (W - 22, y), "칸 1 · 0.1", small, GREY, anchor="ra")
    for row, keys in enumerate(((("Enter", "쓰기"), ("X", "내려놓기"), ("F", "같은 것 줍기"),
                                 ("Shift+F", "모두 줍기")),
                                (("WASD", "고르기 (D: 근처로)"), ("끌어 놓기", "옮기기"), ("Tab", "닫기")))):
        kx, ky = 150, y + 16 + row * 16
        for key, label in keys:
            kw = int(d.textlength(key, font=small)) + 5
            d.rectangle((kx, ky, kx + kw, ky + 12), fill=LIGHT, outline=INK)
            d.text((kx + 3, ky + 1), key, font=small, fill=INK)
            outlined(d, (kx + kw + 4, ky + 1), label, small, LIGHT)
            kx += kw + int(d.textlength(label, font=small)) + 14
    return img


def main(frames, out):
    bg = Image.open(frames + "/bg_play.png")
    a, b = over(bg, option_a()), over(bg, option_b())
    a.save(out + "/v3_bag_a_open_pack.png")
    b.save(out + "/v3_bag_b_ground_sheet.png")
    v2 = Image.open(out + "/v2_bag.png")
    lab = ImageFont.truetype(BOLD, 24)
    c = Image.new("RGB", (1280 * 2 + 20, 720 * 2 + 120), (24, 24, 26))
    cd = ImageDraw.Draw(c)
    cd.fontmode = "1"
    for (im, x, y, title, colour) in ((v2, 0, 50, "2차: 수첩 (종이가 어색)", (200, 200, 200)),
                                      (a, 1300, 50, "A. 펼친 배낭 속 보기", ROAD),
                                      (b, 650, 820, "B. 바닥 천에 늘어놓기", ROAD)):
        c.paste(im, (x, y))
        cd.text((x + 16, y - 38), title, font=lab, fill=colour)
    c.save(out + "/compare_bag_v2_a_b.png")
    g = over(bg, option_b_grid())
    g.save(out + "/v4_bag_b_grid.png")
    c = Image.new("RGB", (1280 * 2 + 20, 770), (24, 24, 26))
    cd = ImageDraw.Draw(c)
    cd.fontmode = "1"
    for (im, x, title, colour) in ((b, 0, "B 첫 시안", (200, 200, 200)), (g, 1300, "B 다듬음 (조사 적용)", ROAD)):
        c.paste(im, (x, 50))
        cd.text((x + 16, 12), title, font=lab, fill=colour)
    c.save(out + "/compare_bag_b_v3_v4.png")
    print("ok")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
