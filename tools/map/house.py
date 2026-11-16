"""The inside of a building one can go into, kept simple (2026-11-16 "필요한 것들만 해서 가능하면 한번
해 보자", references: Zomboid / Darkwood / Stardew interiors, drawn our own way in 3/4 view).

On the 0.5 m wall grid of tools/map/osm_area.py:
  - the outline is a thin wall seen from above, except the north wall, whose inside face shows as a
    1.5 m strip of wallpaper with windows (3/4 view: walls show their south face)
  - a wide house gets one inner wall with a doorway, splitting it into two rooms
  - windows in the south / east / west walls: they stop bodies but not light or sight
  - a few pieces of furniture against the walls, drawn here as pixel art (no downloaded assets)
"""
import sys
from math import ceil
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sprites"))
import house_dots  # noqa: E402  (the hand-placed dot pieces of a house front)

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
FACE_CELLS = 3             # the north wall's inside face: 3 cells = 1.5 m
PART_MIN_WIDTH = 14        # cells (7 m): wider houses get an inner wall
DOORWAY = 2                # cells either side of the middle left open in the inner wall
WALLPAPER, WALL_TOP, BASEBOARD = (146, 134, 112), (40, 34, 32), (70, 58, 48)
GLASS, FRAME = (122, 146, 156), (54, 50, 48)
WOOD, WOOD_LINE, TILE_A, TILE_B = (108, 80, 54), (86, 62, 42), (150, 148, 138), (128, 126, 118)
# name: width, depth, height in metres, and where it stands
FURNITURE = (("fridge", 0.8, 0.7, 1.8, "north"), ("stove", 0.8, 0.7, 0.9, "north"),
             ("shelf", 1.6, 0.5, 1.8, "north"), ("bed", 1.0, 2.0, 0.5, "side"),
             ("table", 1.2, 0.8, 0.75, "middle"), ("sofa", 2.0, 0.8, 0.8, "south"))


def plan(cells):
    """The walls of the house: (all wall cells, the north face cells, the inner wall cells, the
    inner wall's column or None)."""
    top = {}
    for c, r in cells:
        top[c] = max(top.get(c, r), r)
    outline = {(c, r) for c, r in cells if any((c + dc, r + dr) not in cells for dc, dr in N4)}
    face = {(c, r) for c, r in cells if r > top[c] - FACE_CELLS}
    cs = sorted({c for c, _ in cells})
    part, pc = set(), None
    if len(cs) >= PART_MIN_WIDTH:
        pc = cs[int(len(cs) * 0.45)]
        column = sorted(r for c, r in cells if c == pc and (c, r) not in face and (c, r) not in outline)
        if len(column) >= 8:
            mid = column[len(column) // 2]
            part = {(pc, r) for r in column if abs(r - mid) > DOORWAY}
        else:
            pc = None
    return outline | face | part, face, part, pc


def outward(cells, c, r):
    return next(((dc, dr) for dc, dr in N4 if (c + dc, r + dr) not in cells), None)


def windows(cells, wall, face, doors, grid):
    """Window cells in the outer walls (not the north one), 1.5 m wide, every 4 m along a wall."""
    found = set()
    for c, r in wall:
        side = outward(cells, c, r)
        if side is None or (c, r) in face or side == (0, 1):
            continue
        run = c if side[1] else r                          # position along the wall
        ahead, behind = ((c + 1, r), (c - 1, r)) if side[1] else ((c, r + 1), (c, r - 1))
        if run % 8 in (3, 4, 5) and ahead in wall and behind in wall \
                and all(abs((c + 0.5) * grid - x) > 56 or abs((r + 0.5) * grid - y) > 56 for x, y in doors):
            found.add((c, r))
    return found


def furnish(cells, wall, face, doors, grid, rng):
    """Furniture pieces as (name, l, b, r, t) in world units: against the north wall, a side wall, the
    south wall, or in the middle - never in a doorway's way."""
    taken = set(wall)
    for x, y in doors:                                     # keep 2.5 m in front of every doorway clear
        taken |= {(c, r) for c, r in cells if abs((c + 0.5) * grid - x) < 80 and abs((r + 0.5) * grid - y) < 80}
    pieces = []
    for name, w_m, d_m, h_m, where in FURNITURE:
        wc, dc_ = ceil(w_m * 2), ceil(d_m * 2)
        spots = []
        for c0, r0 in cells:
            block = {(c0 + i, r0 + j) for i in range(wc) for j in range(dc_)}
            if not block <= cells or block & taken:
                continue
            ring = {(c + dx, r + dy) for c, r in block for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - block
            touches = {"north": any((c, r0 + dc_) in face for c in range(c0, c0 + wc)),
                       "south": any((c, r0 - 1) in wall and (c, r0 - 1) not in face for c in range(c0, c0 + wc)),
                       "side": any((c0 - 1, r) in wall or (c0 + wc, r) in wall for r in range(r0, r0 + dc_)),
                       "middle": not (ring & wall)}[where]
            if touches and not (ring & taken - wall):
                spots.append((c0, r0))
        if not spots:
            continue
        c0, r0 = rng.choice(spots)
        block = {(c0 + i, r0 + j) for i in range(wc) for j in range(dc_)}
        taken |= block | {(c + dx, r + dy) for c, r in block for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        pieces.append((name, c0 * grid, r0 * grid, (c0 + wc) * grid, (r0 + dc_) * grid, h_m))
    return pieces


def paint(d, cells, wall, face, part, pc, glass, to_px, grid):
    """Floor, the north wall's face, thin walls and windows into the ground picture."""
    def rect(c, r, colour, inset=0):
        x0, y0 = to_px((c * grid, (r + 1) * grid))
        x1, y1 = to_px(((c + 1) * grid, r * grid))
        d.rectangle((round(x0) + inset, round(y0), round(x1) - 1 - inset, round(y1) - 1), fill=colour)

    for c, r in cells:                                     # floors: wood west of the inner wall, tiles east
        if pc is not None and c > pc:
            rect(c, r, TILE_A if (c + r) % 2 else TILE_B)
        else:
            rect(c, r, WOOD)
            x0, y0 = to_px((c * grid, (r + 1) * grid))
            x1, y1 = to_px(((c + 1) * grid, r * grid))
            d.line((round(x0), round(y1) - 1, round(x1) - 1, round(y1) - 1), fill=WOOD_LINE)
            if (c * 3 + r) % 5 == 0:
                d.line((round(x0), round(y0), round(x0), round(y1) - 1), fill=WOOD_LINE)
    tops = {}
    for c, r in face:
        tops[c] = max(tops.get(c, r), r)
    for c, r in face:                                      # the north wall seen from inside
        rect(c, r, WALLPAPER)
        if r == tops[c]:
            rect(c, r, WALL_TOP)
        elif r == tops[c] - FACE_CELLS + 1:
            x0, y0 = to_px((c * grid, (r + 1) * grid))
            x1, y1 = to_px(((c + 1) * grid, r * grid))
            d.rectangle((round(x0), round(y1) - 3, round(x1) - 1, round(y1) - 1), fill=BASEBOARD)
    for c in tops:                                         # windows in it, 1 m wide, every 3 m
        if c % 6 in (2, 3) and (c - 1, tops[c]) in face and (c + 2, tops[c]) in face:
            x0, y0 = to_px((c * grid, tops[c] * grid))
            x1, y1 = to_px(((c + 1) * grid, (tops[c] - 1) * grid))
            d.rectangle((round(x0), round(y0) + 1, round(x1) - 1, round(y1) - 1), fill=GLASS)
            d.line((round(x0), round(y0) + 1, round(x0), round(y1) - 1), fill=FRAME)
    for c, r in (wall - face) | part:
        rect(c, r, WALL_TOP)
    for c, r in glass:
        rect(c, r, GLASS)
        x0, y0 = to_px((c * grid, (r + 1) * grid))
        x1, y1 = to_px(((c + 1) * grid, r * grid))
        d.rectangle((round(x0), round(y0), round(x1) - 1, round(y1) - 1), outline=FRAME)


PLASTER, ROOF_TILE, ROOF_LINE, DOOR_WOOD = (150, 140, 124), (104, 66, 56), (78, 48, 42), (84, 58, 40)


def front(img, mask, face_px, box, cells, glass, doors, to_px, grid):
    """The house seen from outside (its roof picture, box = its canvas-px box): a tiled roof and a
    plaster south wall with the house's real windows and door."""
    from PIL import ImageChops
    w, h = img.size
    shifted = mask.transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, face_px))
    roof = ImageChops.multiply(mask, shifted)
    wallm = ImageChops.subtract(mask, roof)
    # hand-placed dot pieces (tools/sprites/house_dots.py): red brick, barred windows, steel door,
    # a green flat roof (2026-11-16 "이대로 가자")
    img.paste(house_dots.flat_roof(roof, seed=w * 7 + h), (0, 0), roof)
    img.paste(house_dots.brick_wall(w, h, seed=w + h), (0, 0), wallm)
    bottom = {}
    for c, r in cells:
        bottom[c] = min(bottom.get(c, r), r)

    def x_px(c):
        return round(to_px((c * grid, 0))[0]) - box[0]

    def y_px(r):
        return round(to_px((0, r * grid))[1]) - box[1]

    runs = {}                                              # windows of the south wall, run by run
    for c, r in sorted(glass):
        if r == bottom.get(c) and (c, r - 1) not in cells:
            runs.setdefault(r, []).append(c)
    for r, cols_ in runs.items():
        group = [cols_[0]]
        for c in cols_[1:] + [None]:
            if c is not None and c == group[-1] + 1:
                group.append(c)
                continue
            x0, x1 = x_px(group[0]), x_px(group[-1] + 1)
            win = house_dots.window(x1 - x0, round(face_px * 0.36))
            img.alpha_composite(win, (x0, y_px(r) - round(face_px * 0.72)))
            group = [c] if c is not None else []
    for x, y in doors:                                     # the front door
        c0, c1 = int((x - 32) // grid), int((x + 32) // grid)
        r = min(bottom.get(c, 1 << 30) for c in range(c0, c1))
        if r == 1 << 30:
            continue
        dw, dh = x_px(c1) - x_px(c0) - 4, round(face_px * 0.72)
        img.alpha_composite(house_dots.door(dw, dh), (x_px(c0), y_px(r) - dh - 4))


def sprite(name, w, dep, h):
    """A piece of furniture in 3/4 view, w x dep top face over an h tall front face (canvas px)."""
    w, dep, h = max(4, round(w)), max(3, round(dep)), max(2, round(h))
    img = Image.new("RGBA", (w, dep + h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (28, 24, 22, 255)

    def box(top, front, line=ink):
        d.rectangle((0, 0, w - 1, dep - 1), fill=top, outline=line)
        d.rectangle((0, dep - 1, w - 1, dep + h - 1), fill=front, outline=line)

    if name == "bed":
        box((92, 66, 46, 255), (70, 50, 36, 255))
        d.rectangle((2, 2, w - 3, dep - 3), fill=(196, 192, 180, 255))                    # mattress
        d.rectangle((3, 3, w - 4, 3 + max(2, dep // 6)), fill=(222, 220, 210, 255))       # pillow
        d.rectangle((2, dep // 3 + 2, w - 3, dep - 3), fill=(90, 104, 122, 255))           # blanket
        d.line((2, dep // 3 + 2, w - 3, dep // 3 + 2), fill=(120, 136, 156, 255))
    elif name == "table":
        d.rectangle((0, 0, w - 1, dep - 1), fill=(126, 94, 62, 255), outline=ink)
        d.rectangle((0, dep - 1, w - 1, dep + 1), fill=(96, 70, 46, 255), outline=ink)
        for x in (1, w - 3):
            d.rectangle((x, dep + 1, x + 1, dep + h - 1), fill=(80, 58, 38, 255))           # legs
    elif name == "shelf":
        box((98, 74, 50, 255), (84, 62, 42, 255))
        colours = ((150, 60, 50), (70, 100, 130), (170, 150, 80), (90, 120, 70), (140, 140, 132))
        for k, y in enumerate(range(dep + 2, dep + h - 2, max(3, h // 4))):
            d.line((1, y + 2, w - 2, y + 2), fill=(60, 44, 30, 255))
            for i, x in enumerate(range(2, w - 3, 3)):
                d.rectangle((x, y, x + 1, y + 1), fill=colours[(i + k) % len(colours)] + (255,))
    elif name == "fridge":
        box((196, 198, 192, 255), (176, 178, 172, 255))
        d.line((1, dep + h // 3, w - 2, dep + h // 3), fill=(120, 122, 118, 255))
        d.line((w - 4, dep + 3, w - 4, dep + h // 3 - 2), fill=(90, 92, 90, 255))
        d.line((w - 4, dep + h // 3 + 3, w - 4, dep + h - 4), fill=(90, 92, 90, 255))
    elif name == "stove":
        box((150, 150, 146, 255), (128, 128, 124, 255))
        for x, y in ((w // 4, dep // 3), (3 * w // 4, dep // 3), (w // 4, 2 * dep // 3), (3 * w // 4, 2 * dep // 3)):
            d.rectangle((x - 1, y - 1, x, y), fill=(40, 40, 42, 255))
        d.rectangle((2, dep + 2, w - 3, dep + h - 3), fill=(46, 44, 44, 255))              # oven door
    elif name == "sofa":
        box((86, 104, 86, 255), (70, 86, 70, 255))
        d.rectangle((0, 0, w - 1, max(2, dep // 3)), fill=(66, 82, 66, 255), outline=ink)  # back
        d.rectangle((0, 0, 2, dep - 1), fill=(66, 82, 66, 255), outline=ink)               # arms
        d.rectangle((w - 3, 0, w - 1, dep - 1), fill=(66, 82, 66, 255), outline=ink)
        d.line((w // 2, dep // 3 + 1, w // 2, dep - 2), fill=(60, 74, 60, 255))
    else:
        box((120, 110, 100, 255), (96, 88, 80, 255))
    return img
