"""The area being fought in: its size, what blocks movement and sight (wrecks, buildings), where
the infected start and come in, what lies around, and the way out. Bodies slide along blocks one
axis at a time.

Two kinds of area (settings.AREA): "test", the hand-made street of wrecks below, or an area built
from a real map (2026-11-16 map plan C, tools/map/osm_area.py) read from assets/areas/<name>/area.json
with its own ground.png. Every module reads the same names either way.
"""
import json

from settings import AREA, ROOT

# --- the hand-made test street ---------------------------------------------------------------
ROOM_W, ROOM_H = 1000, 640
# wrecked cars and rubble: (left, bottom, right, top) on the ground plane
BLOCKS = [(260, 300, 360, 340), (520, 120, 600, 160), (640, 420, 740, 460), (150, 500, 210, 560)]
BLOCK_LOOKS = ["wreck_0", "wreck_1", "wreck_2", "wreck_3"]   # per block: its picture, or "building"
ZOMBIE_STARTS = [(520, 380), (820, 200), (380, 560)]
# Gaps in the area's edge (alley mouths, doorways) where more infected come in: (x, y) on the
# edge and which side it is on, for drawing.
ENTRANCES = [((12, 420), "left"), ((988, 300), "right"), ((988, 90), "right"),
             ((520, 628), "top"), ((120, 628), "top"), ((760, 12), "bottom")]
HERO_START = (100.0, 300.0)
# Weapons lying around (weapons.py): E swaps one for the weapon in hand, which is left there.
WEAPONS_LYING = [(300, 200, "knife"), (820, 380, "bat"), (620, 250, "pipe"), (420, 560, "axe")]
# Supplies lying around: (x, y, kind) - see supplies.py
SUPPLIES = [(330, 380, "can"), (560, 200, "pill"), (700, 500, "bandage"), (180, 470, "can"),
            (880, 140, "pill"), (450, 90, "bandage"), (760, 320, "can")]   # pills only with exposure on
# The way out of this area: a subway entrance in the far corner (left, bottom, right, top).
EXIT = (905, 560, 985, 628)
EXIT_NAME = "지하철 입구"
GROUND = None                    # the area's own ground picture (None: assets/<AREA_DIR>/ground.png)
CREDIT = ""                      # map data credit, shown when the area comes from a real map

# --- or the empty test arena (2026-11-19 "테스트용이니까 주변에 아무것도 없게, 테스트용 맵을 따로") --
# BUSAN_AREA=arena: the test street's ground with nothing on it, the hero in the middle and a
# few infected standing round him to hit (frozen at the start: F4 lets them go), every weapon
# at his feet, nobody coming in, no station people. For trying attacks and pictures.
TEST_ARENA = AREA == "arena"
if TEST_ARENA:
    BLOCKS, BLOCK_LOOKS = [], []
    HERO_START = (500.0, 320.0)
    ZOMBIE_STARTS = [(556, 264), (444, 264), (556, 376), (444, 376), (500, 250)]
    WEAPONS_LYING = [(470, 300, "knife"), (485, 296, "bat"), (500, 292, "pipe"), (515, 296, "axe"),
                     (530, 300, "machete")]
    SUPPLIES = []

# --- or one built from a real map --------------------------------------------------------------
if AREA not in ("test", "arena"):
    _dir = ROOT / "assets" / "areas" / AREA
    _data = json.loads((_dir / "area.json").read_text(encoding="utf-8"))
    ROOM_W, ROOM_H = _data["size"]
    BLOCKS = [tuple(b[:4]) for b in _data["blocks"]]
    BLOCK_LOOKS = [b[4] for b in _data["blocks"]]
    ZOMBIE_STARTS = [tuple(p) for p in _data["zombie_starts"]]
    ENTRANCES = [(tuple(p), side) for p, side in _data["entrances"]]
    HERO_START = tuple(float(v) for v in _data["hero_start"])
    WEAPONS_LYING = [tuple(w) for w in _data["weapons"]]
    SUPPLIES = [tuple(s) for s in _data["supplies"]]
    EXIT = tuple(_data["exit"])
    GROUND = _dir / "ground.png"
    CREDIT = _data.get("credit", "")
    AREA_PATH = _dir
    # Buildings one can go into (2026-11-16 "건물들도 들어갈 수 있게"): their outline, the roof
    # picture drawn over them while the hero is outside, and its box (world l, b, r, t).
    BUILDINGS = [{"poly": [tuple(p) for p in bd["poly"]], "roof": bd["roof"], "box": tuple(bd["box"])}
                 for bd in _data.get("buildings", [])]
else:
    AREA_PATH = None
    BUILDINGS = []


def inside(poly, x, y):
    """Is (x, y) inside the polygon (a list of (x, y))?"""
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def building_at(x, y):
    """The index of the building (x, y) is in, or None."""
    for i, bd in enumerate(BUILDINGS):
        l, b, r, t = bd["box"]
        if l <= x <= r and b <= y <= t and inside(bd["poly"], x, y):
            return i
    return None


# The blocks by place (a real-map area has hundreds of wall pieces): each BUCKET square lists the
# blocks touching it, so a question about one spot only looks at the few nearby.
# Windows and furniture stop bodies but not light or sight (2026-11-16 house interiors): the sight
# index leaves them out.
def see_through(look):
    return look == "window" or look.startswith("f_")


BUCKET = 128
_buckets, _sight_buckets = {}, {}
for _b, _look in zip(BLOCKS, BLOCK_LOOKS):
    for _i in range(int((_b[0] - 32) // BUCKET), int((_b[2] + 32) // BUCKET) + 1):
        for _j in range(int((_b[1] - 32) // BUCKET), int((_b[3] + 32) // BUCKET) + 1):
            _buckets.setdefault((_i, _j), []).append(_b)
            if not see_through(_look):
                _sight_buckets.setdefault((_i, _j), []).append(_b)


def near_blocks(l, b, r, t, sight=False):
    """The blocks that may touch the box (l, b, r, t); sight: only those that block the view."""
    index, found = _sight_buckets if sight else _buckets, set()
    for i in range(int(l // BUCKET), int(r // BUCKET) + 1):
        for j in range(int(b // BUCKET), int(t // BUCKET) + 1):
            found.update(index.get((i, j), ()))
    return list(found)


def sight_blocks(l, b, r, t):
    return near_blocks(l, b, r, t, sight=True)


def blocks_between(x1, y1, x2, y2, sight=False):
    """The blocks that may stand between two points (sight: for the view and light)."""
    return near_blocks(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), sight)


# Bodies are points at the feet; a wall keeps them this far off its sides (half a body's width)
# and half that off its front and back (seen from above at a slant, depth reads shorter).
BODY_PAD = 8


def blocked(x, y, pad=BODY_PAD):
    return (not (pad <= x <= ROOM_W - pad and pad <= y <= ROOM_H - pad)
            or any(l - pad <= x <= r + pad and b - pad / 2 <= y <= t + pad / 2
                   for l, b, r, t in _buckets.get((int(x // BUCKET), int(y // BUCKET)), ())))


# Ways around blocks (2026-11-16: on the real map the infected walked straight into buildings and
# stayed there). The area is a grid of PATH_CELL cells; for a goal, a breadth-first search gives each
# open cell its number of steps to the goal, and a body steps to the neighbour with fewer. A few
# goals are kept, so many infected after the same hero share one search.
PATH_CELL = 32
_open = None
_fields = {}


def _cell(x, y):
    return int(x // PATH_CELL), int(y // PATH_CELL)


def _is_open(c, r):
    global _open
    if _open is None:
        cols, rows = int(ROOM_W // PATH_CELL) + 1, int(ROOM_H // PATH_CELL) + 1
        _open = {(i, j) for i in range(cols) for j in range(rows)
                 if not blocked((i + 0.5) * PATH_CELL, (j + 0.5) * PATH_CELL, pad=10)}
    return (c, r) in _open


def _neighbours(c, r):
    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        if _is_open(c + dc, r + dr) and (dc == 0 or dr == 0 or (_is_open(c + dc, r) and _is_open(c, r + dr))):
            yield c + dc, r + dr


def waypoint(x, y, tx, ty):
    """Where to walk next on the shortest way around the blocks from (x, y) to (tx, ty)."""
    goal = _cell(tx, ty)
    field = _fields.get(goal)
    if field is None:
        field, todo = {goal: 0}, [goal]
        for c, r in todo:                                  # breadth first: todo grows as it goes
            for n in _neighbours(c, r):
                if n not in field:
                    field[n] = field[(c, r)] + 1
                    todo.append(n)
        if len(_fields) > 8:
            _fields.pop(next(iter(_fields)))
        _fields[goal] = field
    here = _cell(x, y)
    options = [n for n in _neighbours(*here) if n in field]
    if not options or here == goal:
        return tx, ty
    c, r = min(options, key=lambda n: (field[n], (n[0] - here[0]) ** 2 + (n[1] - here[1]) ** 2))
    if field[(c, r)] >= field.get(here, 1 << 30):
        return tx, ty
    return (c + 0.5) * PATH_CELL, (r + 0.5) * PATH_CELL


def kept_out(body, x, y):
    """A body with `keep_out` rects (l, b, r, t) may not step into them from outside (2026-11-18:
    the station is closed to the infected until the defense). One already inside may move."""
    for l, b, r, t in getattr(body, "keep_out", ()):
        if l <= x <= r and b <= y <= t and not (l <= body.x <= r and b <= body.y <= t):
            return True
    return False


def move_body(body, dx, dy):
    """Slide along obstacles one axis at a time."""
    if not blocked(body.x + dx, body.y) and not kept_out(body, body.x + dx, body.y):
        body.x += dx
    if not blocked(body.x, body.y + dy) and not kept_out(body, body.x, body.y + dy):
        body.y += dy
