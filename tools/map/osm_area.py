"""Build a game area from an OpenStreetMap extract (2026-11-16, map plan C "섞기": the real place's
streets and buildings as the skeleton, scaled down; wrecks, supplies and the way out placed on top).

    python tools/map/osm_area.py <extract.osm> <area name> <lat_south> <lon_west> <width_m> <height_m>

Reads an .osm XML file (from openstreetmap.org's export / API), crops width_m x height_m metres
from the south-west corner given, and writes to assets/areas/<name>/:
  - area.json: size, blocks (building footprints as rectangles, wrecks), entrances (where streets
    leave the area), exit (the nearest real subway entrance), hero start, infected, supplies, weapons
  - ground.png: the street seen from above at the dot look's canvas scale (world units x DOT):
    asphalt roads, paved sidewalks, buildings as a roof with its south wall showing
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
SCALE = 8                  # world units per metre: a quarter of the hero's own scale (~32/m), so
                           # a 20 m road is 160 units - three bodies wide - and a block fits a screen
DOT = 32 / 54              # canvas px per world unit (settings.DOT)
CELL_M = 2                 # building footprints become rectangles on a 2 m grid
WALL_M = 3                 # how much of a building's south wall shows (3/4 view)
ROAD_M = {"motorway": 22, "trunk": 22, "primary": 18, "secondary": 14, "tertiary": 10,
          "unclassified": 7, "residential": 7, "living_street": 6, "service": 5}
WALK_M = {"pedestrian": 6, "footway": 3, "steps": 3, "path": 2, "cycleway": 3}
ASPHALT, PAVING, GROUT = (58, 60, 66), (98, 96, 90), (78, 76, 72)
WALL, ROOF, ROOF_EDGE, WINDOW = (46, 42, 42), (74, 68, 64), (104, 96, 88), (24, 26, 30)


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
    return tags.get("tunnel") not in (None, "no") or tags.get("location") == "underground" \
        or tags.get("layer", "0").lstrip("-").isdigit() and int(tags.get("layer", "0")) < 0


def main(src, name, lat0, lon0, width_m, height_m):
    mx, my = 111320 * cos(radians(lat0)), 110540           # metres per degree here
    W, H = round(width_m * SCALE), round(height_m * SCALE)
    cw, ch = round(W * DOT), round(H * DOT)                # the ground image, canvas px

    def world(ll):                                         # (lat, lon) -> world units, y up
        return (ll[1] - lon0) * mx * SCALE, (ll[0] - lat0) * my * SCALE

    def canvas_xy(p):                                      # world -> image px, y down
        return p[0] * DOT, (H - p[1]) * DOT

    ways, points = load(src)
    rng = random.Random(16)

    # --- the ground image -------------------------------------------------------------------
    img = Image.new("RGB", (cw, ch), PAVING)
    d = ImageDraw.Draw(img)
    step = 2 * SCALE * DOT                                 # paving slabs, 2 m, rows offset
    for row in range(int(ch / step) + 1):
        y = row * step
        d.line((0, y, cw, y), fill=GROUT)
        off = step / 2 if row % 2 else 0
        for col in range(int(cw / step) + 2):
            x = col * step + off
            d.line((x, y, x, y + step), fill=GROUT)
    roads = Image.new("L", (cw, ch), 0)                    # where asphalt goes
    rd = ImageDraw.Draw(roads)
    car_roads = []
    for tags, lls in ways:
        hw = tags.get("highway")
        if hw is None or underground(tags) or len(lls) < 2:
            continue
        pts = [canvas_xy(world(ll)) for ll in lls]
        if hw in ROAD_M:
            metres = float(tags["lanes"]) * 3.3 if tags.get("lanes", "").isdigit() else ROAD_M[hw]
            rd.line(pts, fill=255, width=max(2, round(metres * SCALE * DOT)), joint="curve")
            car_roads.append([world(ll) for ll in lls])
    noise = Image.effect_noise((cw, ch), 6).convert("L").point(lambda v: max(0, min(12, (v - 128) // 2 + 6)))
    asphalt = Image.merge("RGB", [ImageChops.add(Image.new("L", (cw, ch), c - 6), noise) for c in ASPHALT])
    img.paste(asphalt, (0, 0), roads)
    cracks = ImageDraw.Draw(img)                           # a few cracks in the asphalt
    for _ in range(int(cw * ch / 2500)):
        x, y = rng.uniform(0, cw), rng.uniform(0, ch)
        if roads.getpixel((int(x), int(y))) == 0:
            continue
        pts = [(x, y)]
        for _ in range(rng.randint(2, 6)):
            x, y = x + rng.uniform(-4, 4), y + rng.uniform(-4, 4)
            pts.append((x, y))
        cracks.line(pts, fill=(36, 36, 40))

    # buildings: the footprint is the wall, the roof is the footprint moved north by WALL_M
    shift = WALL_M * SCALE * DOT
    footprint = Image.new("L", (cw, ch), 0)
    fd = ImageDraw.Draw(footprint)
    for tags, lls in ways:
        if "building" in tags and len(lls) >= 3 and not underground(tags):
            fd.polygon([canvas_xy(world(ll)) for ll in lls], fill=255)
    roof = ImageChops.multiply(footprint, footprint.transform(footprint.size, Image.AFFINE, (1, 0, 0, 0, 1, shift)))
    wall = ImageChops.subtract(footprint, roof)
    windows = Image.new("RGB", (cw, ch), WALL)
    wd = ImageDraw.Draw(windows)
    for y in range(0, ch, 4):
        for x in range(1, cw, 5):
            wd.rectangle((x, y + 1, x + 1, y + 2), fill=WINDOW)
    img.paste(windows, (0, 0), wall)
    img.paste(Image.new("RGB", (cw, ch), ROOF), (0, 0), roof)
    edge = ImageChops.subtract(roof, roof.filter(ImageFilter.MinFilter(3)))
    img.paste(Image.new("RGB", (cw, ch), ROOF_EDGE), (0, 0), edge)

    # --- blocks: footprints on a CELL_M grid, merged into rectangles ---------------------------
    cell = CELL_M * SCALE                                  # world units
    cols, rows = int(W / cell), int(H / cell)
    solid = [[footprint.getpixel((min(cw - 1, int((c + 0.5) * cell * DOT)),
                                  min(ch - 1, int(ch - (r + 0.5) * cell * DOT)))) > 127
              for c in range(cols)] for r in range(rows)]
    blocks, open_runs = [], {}
    for r in range(rows + 1):
        runs, c = set(), 0
        while r < rows and c < cols:
            if solid[r][c]:
                start = c
                while c < cols and solid[r][c]:
                    c += 1
                runs.add((start, c))
            c += 1
        for run, r0 in list(open_runs.items()):            # a run that stops: one rectangle
            if run not in runs:
                blocks.append([run[0] * cell, r0 * cell, run[1] * cell, r * cell, "building"])
                del open_runs[run]
        for run in runs:
            open_runs.setdefault(run, r)

    def walkable(x, y, pad=24):
        return pad <= x <= W - pad and pad <= y <= H - pad and not any(
            l - pad <= x <= r + pad and b - pad <= y <= t + pad for l, b, r, t, _ in blocks)

    def on_road(x, y):
        return roads.getpixel((min(cw - 1, int(x * DOT)), min(ch - 1, int((H - y) * DOT)))) > 127

    # --- wrecked cars on the roads (the old area's four renders, reused) ----------------------
    sizes = {"wreck_0": (100, 40), "wreck_1": (80, 40), "wreck_2": (100, 40), "wreck_3": (60, 60)}
    for _ in range(400):
        if sum(1 for b in blocks if b[4] != "building") >= 9:
            break
        look = rng.choice(list(sizes))
        w, h = sizes[look]
        x, y = rng.uniform(80, W - 80), rng.uniform(80, H - 80)
        corners = [(x - w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2), (x + w / 2, y - h / 2)]
        if all(on_road(*p) for p in corners) and walkable(x, y, pad=w):
            blocks.append([round(x - w / 2), round(y - h / 2), round(x + w / 2), round(y + h / 2), look])

    # --- entrances: where a street leaves the area ---------------------------------------------
    entrances = []
    for line in car_roads:
        for (x1, y1), (x2, y2) in zip(line, line[1:]):
            for side, axis, value in (("left", 0, 0), ("right", 0, W), ("bottom", 1, 0), ("top", 1, H)):
                a1, a2 = (x1, x2) if axis == 0 else (y1, y2)
                if (a1 - value) * (a2 - value) < 0:
                    t = (value - a1) / (a2 - a1)
                    p = (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)
                    q = p[1] if axis == 0 else p[0]
                    if 30 < q < (H if axis == 0 else W) - 30:
                        e = [round(min(max(p[0], 12), W - 12)), round(min(max(p[1], 12), H - 12))]
                        if all(hypot(e[0] - o[0][0], e[1] - o[0][1]) > 120 for o in entrances):
                            entrances.append([e, side])

    # --- the hero comes in on the west; the way out is the real subway entrance farthest off ----
    hero = next((x, H / 2 + dy) for x in range(60, W, 20) for dy in (0, 40, -40, 80, -80, 120, -120)
                if walkable(x, H / 2 + dy))
    subway = [world(ll) for tags, ll in points if tags.get("railway") == "subway_entrance"]
    subway = [p for p in subway if 60 < p[0] < W - 60 and 60 < p[1] < H - 60]
    ex, ey = max(subway, key=lambda p: hypot(p[0] - hero[0], p[1] - hero[1])) if subway else (W - 100, H - 100)
    exit_rect = [round(ex - 40), round(ey - 34), round(ex + 40), round(ey + 34)]
    blocks = [b for b in blocks if not (b[0] < exit_rect[2] and exit_rect[0] < b[2]
                                        and b[1] < exit_rect[3] and exit_rect[1] < b[3]) or b[4] == "building"]

    def scatter(count, far=0):
        out = []
        while len(out) < count:
            x, y = rng.uniform(40, W - 40), rng.uniform(40, H - 40)
            if walkable(x, y) and hypot(x - hero[0], y - hero[1]) > far \
                    and all(hypot(x - o[0], y - o[1]) > 90 for o in out):
                out.append((round(x), round(y)))
        return out

    kinds = ["can", "bandage", "can", "bandage", "pill", "can", "bandage", "pill", "can", "bandage"]
    data = {
        "source": "OpenStreetMap", "credit": "Map data (c) OpenStreetMap contributors, ODbL",
        "size": [W, H], "blocks": blocks, "entrances": entrances, "exit": exit_rect,
        "hero_start": [round(hero[0]), round(hero[1])],
        "zombie_starts": [list(p) for p in scatter(7, far=350)],
        "supplies": [[x, y, k] for (x, y), k in zip(scatter(len(kinds)), kinds)],
        "weapons": [[x, y, k] for (x, y), k in zip(scatter(4), ("knife", "bat", "pipe", "axe"))],
    }
    out = ROOT / "assets" / "areas" / name
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "ground.png")
    (out / "area.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {W}x{H}, {len(blocks)} blocks, {len(entrances)} entrances, exit {exit_rect}, hero {hero}")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], float(a[3]), float(a[4]), float(a[5]), float(a[6]))
