"""Build a game area from an OpenStreetMap extract (2026-11-16, map plan C "섞기": the real place's
streets and buildings as the skeleton; wrecks, supplies and the way out placed on top).

    python tools/map/osm_area.py <extract.osm> <area name> <lat_south> <lon_west> <width_m> <height_m>

Reads an .osm XML file (openstreetmap.org export / API), crops width_m x height_m metres from the
south-west corner given, and writes to assets/areas/<name>/:
  - area.json: size, blocks (walls, solid buildings, wrecks), the enterable buildings (outline and
    roof picture), entrances (where streets leave the area), exit (the real subway entrance farthest
    from the start), hero start, infected, supplies, weapons
  - ground.png: the place from above at the dot look's canvas scale (world units x DOT): asphalt,
    paving, floors and walls of the buildings one can go into, big buildings as roof + south wall
  - roof_<i>.png: the roof of each enterable building, drawn over it while the hero is outside
Real size (2026-11-16 "최대한 크기는 비슷하게, 건물들도 실제로 배치하고 들어갈 수 있게"): the hero
is 54 units for ~1.7 m, so 1 m = 32 units. Small buildings get walls, a door or two and a floor;
big ones (offices, the station) stay solid.
Map data (c) OpenStreetMap contributors, ODbL - the game credits it.
"""
import json
import random
import sys
import xml.etree.ElementTree as ET
from math import cos, hypot, radians
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SCALE = 32                 # world units per metre: the hero's own scale (54 units ~ 1.7 m)
DOT = 32 / 54              # canvas px per world unit (settings.DOT)
GRID = 16                  # walls are laid on a 0.5 m grid
SOLID_GRID = 64            # solid buildings become rectangles on a 2 m grid
ENTER_MAX_M2 = 600         # buildings up to this floor area can be gone into
ENTER_COUNT = 1            # how many of them are made enterable (the rest stay solid)
DOOR = 64                  # a doorway, 2 m (snapped to the game's 32-unit path grid)
FACE_M = 3                 # how much of a building's south wall shows (3/4 view)
ROAD_M = {"motorway": 22, "trunk": 22, "primary": 18, "secondary": 14, "tertiary": 10,
          "unclassified": 7, "residential": 7, "living_street": 6, "service": 5}
ASPHALT, PAVING, GROUT = (58, 60, 66), (98, 96, 90), (78, 76, 72)
WALL, ROOF, ROOF_EDGE, WINDOW = (46, 42, 42), (74, 68, 64), (104, 96, 88), (24, 26, 30)
INNER_WALL = (34, 30, 30)
FLOORS = ((92, 74, 56), (84, 86, 80), (104, 92, 72), (78, 70, 66))   # wood, linoleum, ...


def load(path):
    root = ET.parse(path).getroot()
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.iter("node")}
    ways, points = [], []
    for way in root.iter("way"):
        tags = {t.get("k"): t.get("v") for t in way.iter("tag")}
        ways.append((tags, [nodes[n.get("ref")] for n in way.iter("nd") if n.get("ref") in nodes]))
    for n in root.iter("node"):
        tags = {t.get("k"): t.get("v") for t in n.iter("tag")}
        if tags:
            points.append((tags, (float(n.get("lat")), float(n.get("lon")))))
    return ways, points


def underground(tags):
    layer = tags.get("layer", "0")
    return tags.get("tunnel") not in (None, "no") or tags.get("location") == "underground" \
        or (layer.lstrip("-").isdigit() and int(layer) < 0)


def merge(cells, size):
    """Grid cells (col, row) -> as few rectangles (l, b, r, t) as rows of runs merged upward."""
    rows = {}
    for c, r in cells:
        rows.setdefault(r, []).append(c)
    rects, open_runs = [], {}
    for r in range(min(rows, default=0), max(rows, default=-1) + 2):
        runs, cols = set(), sorted(rows.get(r, []))
        i = 0
        while i < len(cols):
            j = i
            while j + 1 < len(cols) and cols[j + 1] == cols[j] + 1:
                j += 1
            runs.add((cols[i], cols[j] + 1))
            i = j + 1
        for run, r0 in list(open_runs.items()):
            if run not in runs:
                rects.append((run[0] * size, r0 * size, run[1] * size, r * size))
                del open_runs[run]
        for run in runs:
            open_runs.setdefault(run, r)
    return rects


def inside(poly, x, y):
    hit = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def main(src, name, lat0, lon0, width_m, height_m):
    mx, my = 111320 * cos(radians(lat0)), 110540           # metres per degree here
    W, H = round(width_m * SCALE), round(height_m * SCALE)
    cw, ch = round(W * DOT), round(H * DOT)                # the ground image, canvas px
    cols, rows = W // GRID, H // GRID
    out = ROOT / "assets" / "areas" / name
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("roof_*.png"):
        old.unlink()

    def world(ll):                                         # (lat, lon) -> world units, y up
        return (ll[1] - lon0) * mx * SCALE, (ll[0] - lat0) * my * SCALE

    def canvas_xy(p):                                      # world -> image px, y down
        return p[0] * DOT, (H - p[1]) * DOT

    ways, points = load(src)
    rng = random.Random(16)

    # --- streets and paving --------------------------------------------------------------------
    img = Image.new("RGB", (cw, ch), PAVING)
    d = ImageDraw.Draw(img)
    step = 1 * SCALE * DOT                                 # 1 m paving slabs, rows offset
    for row in range(int(ch / step) + 1):
        y = row * step
        d.line((0, y, cw, y), fill=GROUT)
        off = step / 2 if row % 2 else 0
        for col in range(int(cw / step) + 2):
            d.line((col * step + off, y, col * step + off, y + step), fill=GROUT)
    roads = Image.new("L", (cw, ch), 0)
    rd = ImageDraw.Draw(roads)
    car_roads = []
    for tags, lls in ways:
        hw = tags.get("highway")
        if hw in ROAD_M and not underground(tags) and len(lls) >= 2:
            metres = float(tags["lanes"]) * 3.3 if tags.get("lanes", "").isdigit() else ROAD_M[hw]
            rd.line([canvas_xy(world(ll)) for ll in lls], fill=255, width=max(2, round(metres * SCALE * DOT)),
                    joint="curve")
            car_roads.append([world(ll) for ll in lls])
    noise = Image.effect_noise((cw, ch), 6).convert("L").point(lambda v: max(0, min(12, (v - 128) // 2 + 6)))
    img.paste(Image.merge("RGB", [ImageChops.add(Image.new("L", (cw, ch), c - 6), noise) for c in ASPHALT]),
              (0, 0), roads)
    for _ in range(int(cw * ch / 2500)):                   # cracks in the asphalt
        x, y = rng.uniform(0, cw), rng.uniform(0, ch)
        if roads.getpixel((int(x), int(y))) == 0:
            continue
        pts = [(x, y)]
        for _ in range(rng.randint(2, 6)):
            x, y = x + rng.uniform(-4, 4), y + rng.uniform(-4, 4)
            pts.append((x, y))
        d.line(pts, fill=(36, 36, 40))

    # --- buildings -----------------------------------------------------------------------------
    polys = []
    for tags, lls in ways:
        if "building" in tags and len(lls) >= 3 and not underground(tags):
            poly = [world(ll) for ll in lls]
            if poly[0] == poly[-1]:
                poly = poly[:-1]
            area_m2 = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2 / SCALE ** 2
            if max(x for x, _ in poly) > 0 and min(x for x, _ in poly) < W and max(y for _, y in poly) > 0 \
                    and min(y for _, y in poly) < H:
                polys.append((poly, area_m2))
    all_fp = Image.new("L", (cw, ch), 0)                   # every footprint, canvas px
    for poly, _ in polys:
        ImageDraw.Draw(all_fp).polygon([canvas_xy(p) for p in poly], fill=255)
    shift = FACE_M * SCALE * DOT

    def roof_and_face(mask):
        """The footprint split into the roof (moved north by FACE_M) and the south wall under it."""
        roof = ImageChops.multiply(mask, mask.transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, shift)))
        return roof, ImageChops.subtract(mask, roof)

    windows = Image.new("RGB", (cw, ch), WALL)
    wd = ImageDraw.Draw(windows)
    for y in range(0, ch, 8):
        for x in range(2, cw, 9):
            wd.rectangle((x, y + 2, x + 3, y + 5), fill=WINDOW)

    def paint_roof(target, mask, offset=(0, 0)):
        roof, face = roof_and_face(mask)
        target.paste(windows.crop((offset[0], offset[1], offset[0] + mask.width, offset[1] + mask.height)), (0, 0), face)
        target.paste(ROOF, (0, 0, mask.width, mask.height), roof)
        edge = ImageChops.subtract(roof, roof.filter(ImageFilter.MinFilter(3)))
        target.paste(ROOF_EDGE, (0, 0, mask.width, mask.height), edge)

    blocks, buildings = [], []
    occupied = set()                                       # grid cells inside any footprint
    # For now one building to go into (2026-11-16 "건물은 우선 1개만 임시로"): the house that fits
    # nearest the middle of the area; the rest stay solid.
    fits = [i for i, (poly, area_m2) in enumerate(polys) if 60 <= area_m2 <= ENTER_MAX_M2]
    mid = lambda poly: (sum(x for x, _ in poly) / len(poly), sum(y for _, y in poly) / len(poly))
    enter = set(sorted(fits, key=lambda i: hypot(mid(polys[i][0])[0] - W / 2, mid(polys[i][0])[1] - H / 2))[:ENTER_COUNT])
    for i, (poly, area_m2) in enumerate(polys):
        gmask = Image.new("L", (cols, rows), 0)            # this footprint on the wall grid (y down)
        ImageDraw.Draw(gmask).polygon([(x / GRID, rows - y / GRID) for x, y in poly], fill=255)
        cells = {(c, rows - 1 - r) for r in range(rows) for c in range(cols) if gmask.getpixel((c, r)) > 127}
        occupied |= cells
        if not cells:
            continue
        mask = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(mask).polygon([canvas_xy(p) for p in poly], fill=255)
        if i not in enter or len(cells) < 40:              # not one to go into: a solid block
            solid = {(int(x * GRID // SOLID_GRID), int(y * GRID // SOLID_GRID)) for x, y in cells}
            blocks += [list(r) + ["building"] for r in merge(solid, SOLID_GRID)]
            paint_roof(img, mask)
            continue
        polys[i] = (poly, area_m2, cells)
    # enterable buildings, now that every footprint is known (a door must not open into a neighbour)
    rooms = []
    for i, entry in enumerate(polys):
        if len(entry) != 3:
            continue
        poly, area_m2, cells = entry
        wall = {(c, r) for c, r in cells
                if any((c + dc, r + dr) not in cells for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        doors = []
        for c, r in sorted(wall, key=lambda cell: (cell[1], cell[0])):          # south first
            for dc, dr in ((0, -1), (1, 0), (-1, 0), (0, 1)):
                if (c + dc, r + dr) in cells:
                    continue
                ox, oy = c + dc * 4, r + dr * 4                                # 2 m out: open ground?
                if 0 <= ox < cols and 0 <= oy < rows and (ox, oy) not in occupied:
                    doors.append((round((c + 0.5) * GRID / 32) * 32, round((r + 0.5) * GRID / 32) * 32, (dc, dr)))
                break
        rng.shuffle(doors)
        doors.sort(key=lambda dd: {(0, -1): 0, (1, 0): 1, (-1, 0): 1, (0, 1): 2}[dd[2]])
        rooms.append({"i": i, "poly": poly, "area": area_m2, "wall": wall, "doors": doors, "chosen": []})

    def cut(room, door):
        x, y, _ = door
        room["chosen"].append(door)                         # knock the doorway out of the wall
        room["wall"] = {(c, r) for c, r in room["wall"]
                        if not (abs((c + 0.5) * GRID - x) < DOOR / 2 and abs((r + 0.5) * GRID - y) < DOOR / 2)}

    for room in rooms:
        for door in room["doors"]:
            if len(room["chosen"]) >= (2 if room["area"] > 200 else 1):
                break
            if all(hypot(door[0] - c[0], door[1] - c[1]) > 300 for c in room["chosen"]):
                cut(room, door)

    def open_region(rects):
        """The cells of the game's path grid (32 units, 10 clear) one can walk to from the open
        street - a courtyard shut in by buildings is not in it."""
        def free(c, r):
            x, y = (c + 0.5) * 32, (r + 0.5) * 32
            return 10 <= x <= W - 10 and 10 <= y <= H - 10 and not any(
                l - 10 <= x <= rr + 10 and b - 5 <= y <= t + 5 for l, b, rr, t in rects)
        best = set()
        left = {(c, r) for c in range(W // 32) for r in range(H // 32) if free(c, r)}
        while left:                                         # the biggest connected piece
            start = left.pop()
            seen, todo = {start}, [start]
            for c, r in todo:
                for n in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
                    if n in left:
                        left.discard(n)
                        seen.add(n)
                        todo.append(n)
            if len(seen) > len(best):
                best = seen
        return best

    def unreachable():
        """Rooms none of whose floor can be walked to from the open street."""
        seen = open_region([tuple(b[:4]) for b in blocks] + [r for room in rooms for r in merge(room["wall"], GRID)])
        return [room for room in rooms
                if not any(inside(room["poly"], (c + 0.5) * 32, (r + 0.5) * 32) for c, r in seen)]

    for _ in range(6):                                      # a room no one can get into: one more door
        shut = unreachable()
        if not shut:
            break
        for room in shut:
            spare = [dd for dd in room["doors"] if dd not in room["chosen"]
                     and all(hypot(dd[0] - c[0], dd[1] - c[1]) > 96 for c in room["chosen"])]
            if spare:
                cut(room, spare[0])
    print("rooms no one can get into:", [room["i"] for room in unreachable()])

    for room in rooms:
        i, poly, area_m2, wall, chosen = room["i"], room["poly"], room["area"], room["wall"], room["chosen"]
        blocks += [list(r) + ["wall"] for r in merge(wall, GRID)]
        # floor and walls into the ground; the roof into its own picture
        floor = FLOORS[i % len(FLOORS)]
        flat = [canvas_xy(p) for p in poly]
        d.polygon(flat, fill=floor)
        for c, r in wall:
            x0, y0 = canvas_xy((c * GRID, (r + 1) * GRID))
            x1, y1 = canvas_xy(((c + 1) * GRID, r * GRID))
            d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=INNER_WALL)
        l, b = min(x for x, _ in poly), min(y for _, y in poly)
        r_, t = max(x for x, _ in poly), max(y for _, y in poly)
        box = (int(l * DOT), int((H - t) * DOT), int(r_ * DOT) + 1, int((H - b) * DOT) + 1)
        mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
        ImageDraw.Draw(mask).polygon([(x - box[0], y - box[1]) for x, y in flat], fill=255)
        roof_img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        paint_roof(roof_img, mask, offset=box[:2])
        roof_img.putalpha(mask)
        roof_img.save(out / f"roof_{len(buildings)}.png")
        buildings.append({"poly": [[round(x), round(y)] for x, y in poly], "roof": f"roof_{len(buildings)}",
                          "box": [box[0] / DOT, H - box[3] / DOT, box[2] / DOT, H - box[1] / DOT],
                          "doors": [[x, y] for x, y, _ in chosen]})

    region = None                                           # set once the blocks are all placed

    def walkable(x, y, pad=24):
        if region is not None and (int(x // 32), int(y // 32)) not in region:
            return False                                    # shut in: no one can get there
        return pad <= x <= W - pad and pad <= y <= H - pad and not any(
            l - pad <= x <= r + pad and b - pad <= y <= t + pad for l, b, r, t, _ in blocks)

    def indoors(x, y):
        return any(inside([tuple(p) for p in bd["poly"]], x, y) for bd in buildings)

    def on_road(x, y):
        return roads.getpixel((min(cw - 1, int(x * DOT)), min(ch - 1, int((H - y) * DOT)))) > 127 \
            and all_fp.getpixel((min(cw - 1, int(x * DOT)), min(ch - 1, int((H - y) * DOT)))) == 0

    # --- wrecked cars on the roads (the old area's renders, reused) ----------------------------
    sizes = {"wreck_0": (100, 40), "wreck_1": (80, 40), "wreck_2": (100, 40), "wreck_3": (60, 60)}
    want = max(3, round(W * H / 900000))
    for _ in range(600):
        if sum(1 for b in blocks if b[4] in sizes) >= want:
            break
        look = rng.choice(list(sizes))
        w, h = sizes[look]
        x, y = rng.uniform(80, W - 80), rng.uniform(80, H - 80)
        corners = [(x - w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2), (x + w / 2, y - h / 2)]
        if all(on_road(*p) for p in corners) and walkable(x, y, pad=w):
            blocks.append([round(x - w / 2), round(y - h / 2), round(x + w / 2), round(y + h / 2), look])

    region = open_region([tuple(b[:4]) for b in blocks])

    # --- entrances: where a street leaves the area ---------------------------------------------
    entrances = []
    for line in car_roads:
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            for side, axis, value in (("left", 0, 0), ("right", 0, W), ("bottom", 1, 0), ("top", 1, H)):
                a1, a2 = (x1, x2) if axis == 0 else (y1, y2)
                if (a1 - value) * (a2 - value) < 0:
                    t = (value - a1) / (a2 - a1)
                    p = (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
                    e = [round(min(max(p[0], 12), W - 12)), round(min(max(p[1], 12), H - 12))]
                    if walkable(*e, pad=12) and all(hypot(e[0] - o[0][0], e[1] - o[0][1]) > 400 for o in entrances):
                        entrances.append([e, side])

    # --- the way out is a real subway entrance; the hero comes in by the street end farthest off --
    subway = [world(ll) for tags, ll in points if tags.get("railway") == "subway_entrance"]
    subway = [p for p in subway if 60 < p[0] < W - 60 and 60 < p[1] < H - 60] or [(W - 100, H - 100)]
    starts = [(e[0] + {"left": 60, "right": -60}.get(s, 0), e[1] + {"bottom": 60, "top": -60}.get(s, 0))
              for e, s in entrances]
    starts = [p for p in starts if walkable(*p)] or [(60, H / 2)]
    hero, (ex, ey) = max(((h, s) for h in starts for s in subway),
                         key=lambda hs: hypot(hs[0][0] - hs[1][0], hs[0][1] - hs[1][1]))
    exit_rect = [round(ex - 40), round(ey - 34), round(ex + 40), round(ey + 34)]
    blocks = [b for b in blocks if b[4] not in sizes or not (b[0] < exit_rect[2] and exit_rect[0] < b[2]
                                                             and b[1] < exit_rect[3] and exit_rect[1] < b[3])]

    def scatter(count, far=0, indoor_share=0.0):
        found = []
        for _ in range(20000):
            if len(found) >= count:
                break
            x, y = rng.uniform(40, W - 40), rng.uniform(40, H - 40)
            want_in = len(found) < count * indoor_share
            if walkable(x, y) and indoors(x, y) == want_in and hypot(x - hero[0], y - hero[1]) > far \
                    and all(hypot(x - o[0], y - o[1]) > 90 for o in found):
                found.append((round(x), round(y)))
        return found

    kinds = ["can", "bandage", "can", "bandage", "pill", "can", "bandage", "pill", "can", "bandage"]
    data = {
        "source": "OpenStreetMap", "credit": "Map data (c) OpenStreetMap contributors, ODbL",
        "size": [W, H], "blocks": blocks, "buildings": buildings, "entrances": entrances,
        "exit": exit_rect, "hero_start": [round(hero[0]), round(hero[1])],
        "zombie_starts": [list(p) for p in scatter(7, far=500, indoor_share=0.15)],
        "supplies": [[x, y, k] for (x, y), k in zip(scatter(len(kinds), indoor_share=0.3), kinds)],
        "weapons": [[x, y, k] for (x, y), k in zip(scatter(4, indoor_share=0.25), ("knife", "bat", "pipe", "axe"))],
    }
    img.save(out / "ground.png")
    (out / "area.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {W}x{H}, {len(blocks)} blocks, {len(buildings)} enterable buildings, "
          f"{len(entrances)} entrances, exit {exit_rect}, hero {hero}")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], float(a[3]), float(a[4]), float(a[5]), float(a[6]))
