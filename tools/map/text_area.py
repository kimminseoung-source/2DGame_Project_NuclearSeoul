"""Draw a text map (tools/map/osm_to_text.py, or written by hand) as the game's ground and blocks
(2026-11-16 "실제 지리를 글자 지도로", "건물별로 렌더링이랑 막히는 판정이 다른 부분 → 디테일").

    python tools/map/text_area.py <map.txt> <out.png> [debug.png]

One character is one metre (32 world units, ~19 canvas px). Buildings are the connected runs of
the same building character; each is drawn from its own cells and blocks exactly those cells, so
what is seen and what stops the body cannot disagree - the old builder drew a building from its
outline polygon but blocked a 2 m grid of it, and they drifted apart at slanted edges.
    =  road  .  pavement  #  brick house  B  big building  X  subway entrance
The picture: paving, asphalt with a faded centre line and curbs, each building a roof over its
south wall (3/4 view: the wall shows on the bottom rows of each column, 3 m for a house, 4 m for
a big building). debug.png adds the block rectangles in red over it.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sprites"))
import house_dots as hd  # noqa: E402

M = 32                     # world units per metre (per character)
DOT = 32 / 54              # canvas px per world unit
FACE_M = {"#": 3, "B": 7}  # how much of the south wall shows (a big building: two floors)
BUILDINGS = "#B"
PAVING, GROUT = (98, 96, 90), (78, 76, 72)


def read(path):
    rows = [r.rstrip("\n") for r in Path(path).read_text(encoding="utf-8").splitlines() if r.strip()]
    width = max(len(r) for r in rows)
    return [r.ljust(width, ".") for r in rows]


def px(v):
    """A world coordinate to canvas px, rounded the same way everywhere (picture and blocks)."""
    return round(v * DOT)


def components(rows):
    """Each building: (char, set of (col, row)) - 4-connected cells of one building character."""
    seen, found = set(), []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in BUILDINGS and (c, r) not in seen:
                cells, todo = {(c, r)}, [(c, r)]
                seen.add((c, r))
                for cc, rr in todo:
                    for n in ((cc + 1, rr), (cc - 1, rr), (cc, rr + 1), (cc, rr - 1)):
                        if n not in seen and 0 <= n[1] < len(rows) and 0 <= n[0] < len(rows[0]) \
                                and rows[n[1]][n[0]] == ch:
                            seen.add(n)
                            cells.add(n)
                            todo.append(n)
                found.append((ch, cells))
    return found


def rects(cells):
    """Cells -> rectangles (c0, r0, c1, r1) inclusive: runs along each row, merged down the rows."""
    rows = {}
    for c, r in cells:
        rows.setdefault(r, []).append(c)
    out, open_runs = [], {}
    for r in range(min(rows), max(rows) + 2):
        runs, cs = set(), sorted(rows.get(r, []))
        i = 0
        while i < len(cs):
            j = i
            while j + 1 < len(cs) and cs[j + 1] == cs[j] + 1:
                j += 1
            runs.add((cs[i], cs[j]))
            i = j + 1
        for run, r0 in list(open_runs.items()):
            if run not in runs:
                out.append((run[0], r0, run[1], r - 1))
                del open_runs[run]
        for run in runs:
            open_runs.setdefault(run, r)
    return out


def draw(rows, seed=4):
    """-> (picture, blocks): blocks are (l, b, r, t, look) in world units, y up."""
    rng = random.Random(seed)
    cols, n = len(rows[0]), len(rows)
    W, H = cols * M, n * M
    cw, ch = px(W), px(H)
    img = Image.new("RGBA", (cw, ch), PAVING + (255,))
    d = ImageDraw.Draw(img)

    def cell_box(c, r):                                    # canvas px of a cell (row 0 at the top)
        return px(c * M), px(r * M), px((c + 1) * M) - 1, px((r + 1) * M) - 1

    for r in range(n):                                     # paving slabs, 1 m, rows offset
        y = px(r * M)
        d.line((0, y, cw, y), fill=GROUT)
        for c in range(cols + 1):
            x = px((c + (0.5 if r % 2 else 0)) * M)
            d.line((x, y, x, px((r + 1) * M)), fill=GROUT)
    road = [[rows[r][c] == "=" for c in range(cols)] for r in range(n)]
    for r in range(n):
        for c in range(cols):
            if road[r][c]:
                x0, y0, x1, y1 = cell_box(c, r)
                for y in range(y0, y1 + 1):
                    for x in range(x0, x1 + 1):
                        v = rng.randint(-4, 4)
                        img.putpixel((x, y), (56 + v, 58 + v, 64 + v, 255))
    for r in range(n):                                     # curbs where road meets pavement
        for c in range(cols):
            if not road[r][c]:
                continue
            x0, y0, x1, y1 = cell_box(c, r)
            if r > 0 and not road[r - 1][c]:
                d.line((x0, y0, x1, y0), fill=(140, 136, 126))
            if r < n - 1 and not road[r + 1][c]:
                d.line((x0, y1, x1, y1), fill=(70, 68, 64))
            if c > 0 and not road[r][c - 1]:
                d.line((x0, y0, x0, y1), fill=(120, 116, 108))
            if c < cols - 1 and not road[r][c + 1]:
                d.line((x1, y0, x1, y1), fill=(70, 68, 64))
    for _ in range(cols * n // 30):                        # cracks in the asphalt
        c, r = rng.randrange(cols), rng.randrange(n)
        if road[r][c]:
            x, y = cell_box(c, r)[:2]
            pts = [(x, y)]
            for _ in range(rng.randint(2, 5)):
                x, y = x + rng.randint(-4, 4), y + rng.randint(-4, 4)
                pts.append((x, y))
            d.line(pts, fill=(36, 36, 40))

    blocks = []
    for i, (kind, cells) in enumerate(components(rows)):
        c0, c1 = min(c for c, _ in cells), max(c for c, _ in cells)
        r0, r1 = min(r for _, r in cells), max(r for _, r in cells)
        ox, oy = px(c0 * M), px(r0 * M)
        bw, bh = px((c1 + 1) * M) - ox, px((r1 + 1) * M) - oy
        mask = Image.new("L", (bw, bh), 0)
        md = ImageDraw.Draw(mask)
        for c, r in cells:
            x0, y0, x1, y1 = cell_box(c, r)
            md.rectangle((x0 - ox, y0 - oy, x1 - ox, y1 - oy), fill=255)
        face_rows = FACE_M[kind]
        bottom = {}
        for c, r in cells:
            bottom[c] = max(bottom.get(c, r), r)           # the southmost row of each column
        wall = Image.new("L", (bw, bh), 0)
        wd = ImageDraw.Draw(wall)
        for c, r in cells:
            if r > bottom[c] - face_rows:                  # the bottom rows of each column: wall
                x0, y0, x1, y1 = cell_box(c, r)
                wd.rectangle((x0 - ox, y0 - oy, x1 - ox, y1 - oy), fill=255)
        roof = ImageChops.subtract(mask, wall)
        pic = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        if kind == "B":
            pic.paste(hd.office_roof(roof, seed=i), (0, 0), roof)
            pic.paste(hd.office_wall(bw, bh, seed=i), (0, 0), wall)
        else:
            pic.paste(hd.flat_roof(roof, seed=i), (0, 0), roof)
            pic.paste(hd.brick_wall(bw, bh, seed=i), (0, 0), wall)
        img.alpha_composite(pic, (ox, oy))
        for a, b_, e, f in rects(cells):                   # blocks: exactly the cells
            blocks.append((a * M, (n - 1 - f) * M, (e + 1) * M, (n - b_) * M, "building"))   # painted in the ground
    for r in range(n):                                     # the way out
        for c in range(cols):
            if rows[r][c] == "X":
                x0, y0, x1, y1 = cell_box(c, r)
                d.rectangle((x0 - 20, y0 - 16, x1 + 20, y1 + 10), fill=(18, 20, 22))
                d.rectangle((x0 - 20, y1 + 11, x1 + 20, y1 + 17), fill=(30, 120, 70))
    return img, blocks


def debug(img, blocks, rows):
    """The picture with each block's rectangle in red."""
    out = img.copy()
    d = ImageDraw.Draw(out)
    H = len(rows) * M
    for l, b, r, t, _ in blocks:
        d.rectangle((px(l), px(H - t), px(r) - 1, px(H - b) - 1), outline=(255, 40, 40))
    return out


# ------------------------------------------------------------------ a whole game area
# More characters for a hand-made map (2026-11-16 "골목 만들어"):
#   E  a house one can go into (a rectangle)   D  its doorway (2 m, on its south row)
#   S  the hero's start   z  an infected   k  a crawling one   c  a wrecked car   +  a supply   w  a weapon   g  a gun
SUPPLY_KINDS = ("can", "bandage", "can", "bandage", "pill")
WEAPON_KINDS = ("knife", "bat", "pipe", "axe")
WRECKS = {"wreck_0": (100, 40), "wreck_1": (80, 40), "wreck_2": (100, 40)}
GRID = 16                  # the wall grid of a house one can go into (house.py)


def build(rows, name, seed=16):
    """Write assets/areas/<name>/ (area.json, ground.png, roof and furniture pictures) for src/area.py."""
    import json
    import shutil
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import house  # noqa: E402

    rng = random.Random(seed)
    root = Path(__file__).resolve().parents[2]
    out = root / "assets" / "areas" / name
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("roof_*.png")) + list(out.glob("f_*.png")):
        old.unlink()
    n, cols = len(rows), len(rows[0])
    W, H = cols * M, n * M
    flat = [r.replace("E", ".").replace("D", ".") for r in rows]     # houses are drawn below
    img, blocks = draw([r.translate(str.maketrans("Szkc+wXg", "........")) for r in flat])
    blocks = [list(b) for b in blocks]
    d = ImageDraw.Draw(img)

    def world(c, r):                                       # the middle of a character, y up
        return c * M + M / 2, (n - 1 - r) * M + M / 2

    def to_px(p):
        return p[0] * DOT, (H - p[1]) * DOT

    found = {ch: [(c, r) for r in range(n) for c in range(cols) if rows[r][c] == ch] for ch in "EDSzkc+wXg"}
    buildings = []
    if found["E"]:                                         # the house one can go into
        es = found["E"] + found["D"]
        c0, c1 = min(c for c, _ in es), max(c for c, _ in es)
        r0, r1 = min(r for _, r in es), max(r for _, r in es)
        cells = {(cc, rr) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)
                 for cc in (2 * c, 2 * c + 1) for rr in (2 * (n - 1 - r), 2 * (n - 1 - r) + 1)}
        wall, face, part, pc = house.plan(cells)
        doors = []
        dcols = sorted(c for c, _ in found["D"])
        if dcols:                                          # the doorway: the middle of the D run
            x, y = (dcols[0] + dcols[-1] + 1) / 2 * M, (n - 1 - r1) * M + GRID / 2
            doors.append((round(x / 32) * 32, round(y / 32) * 32))
            wall = {(c, r) for c, r in wall
                    if not (abs((c + 0.5) * GRID - doors[0][0]) < 32 and abs((r + 0.5) * GRID - doors[0][1]) < 32)}
        glass = house.windows(cells, wall, face, doors, GRID)
        furniture = house.furnish(cells, wall, face, doors, GRID, rng)
        blocks += [list(rc) + ["wall"] for rc in _merge(wall - glass)]
        blocks += [list(rc) + ["window"] for rc in _merge(glass)]
        for piece, l_, b_, r_, t_, h_m in furniture:
            blocks.append([l_, b_, r_, t_, f"f_{piece}"])
            drawn = root / "assets" / "furniture" / f"{piece}.png"
            if drawn.exists():
                shutil.copy(drawn, out / f"f_{piece}.png")
            else:
                house.sprite(piece, (r_ - l_) * DOT, (t_ - b_) * DOT, h_m * M * DOT).save(out / f"f_{piece}.png")
        house.paint(d, cells, wall, face, part, pc, glass, to_px, GRID)
        l, b, r, t = c0 * M, (n - 1 - r1) * M, (c1 + 1) * M, (n - r0) * M
        box = (px(l), px(H - t), px(r), px(H - b))
        mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 255)
        roof = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        house.front(roof, mask, round(FACE_M["#"] * M * DOT), box, cells, glass, doors, to_px, GRID)
        roof.putalpha(mask)
        roof.save(out / "roof_0.png")
        buildings.append({"poly": [[l, b], [r, b], [r, t], [l, t]], "roof": "roof_0",
                          "box": [box[0] / DOT, H - box[3] / DOT, box[2] / DOT, H - box[1] / DOT],
                          "doors": [list(dd) for dd in doors]})
    for c, r in found["c"]:                                # wrecked cars, lying along the road
        look = rng.choice(list(WRECKS))
        w, h = WRECKS[look]
        x, y = world(c, r)
        blocks.append([round(x - w / 2), round(y - h / 2), round(x + w / 2), round(y + h / 2), look])
    # infected come in where a road or alley meets the map's edge (the middle of each open run)
    entrances = []
    for side, line in (("top", [(c, 0) for c in range(cols)]), ("bottom", [(c, n - 1) for c in range(cols)]),
                       ("left", [(0, r) for r in range(n)]), ("right", [(cols - 1, r) for r in range(n)])):
        run = []
        for cell in line + [None]:
            if cell is not None and rows[cell[1]][cell[0]] not in "#BED":
                run.append(cell)
                continue
            if len(run) >= 2:
                x, y = world(*run[len(run) // 2])
                x = 12 if side == "left" else W - 12 if side == "right" else x
                y = 12 if side == "bottom" else H - 12 if side == "top" else y
                entrances.append([[round(x), round(y)], side])
            run = []
    exit_rect = [0, 0, 80, 68]
    if found["X"]:
        x, y = world(*found["X"][0])
        exit_rect = [round(x - 40), round(y - 34), round(x + 40), round(y + 34)]
    hero = world(*found["S"][0]) if found["S"] else (64, H / 2)
    supplies = [[*map(round, world(c, r)), SUPPLY_KINDS[i % len(SUPPLY_KINDS)]] for i, (c, r) in enumerate(found["+"])]
    if buildings:                                          # two more inside the house, on open floor
        l, b, r, t = buildings[0]["poly"][0] + buildings[0]["poly"][2]

        def free(x, y, pad=20):
            return not any(bl - pad <= x <= br + pad and bb - pad <= y <= bt + pad for bl, bb, br, bt, _ in blocks)
        spots = [(x, y) for y in range(int(b) + 48, int(t) - 48, 16) for x in range(int(l) + 32, int(r) - 32, 16)
                 if free(x, y)]
        for i, k in enumerate(("bandage", "can")):
            if spots:
                x, y = spots[(len(spots) * (1 + 2 * i)) // 4]          # a quarter and three quarters in
                supplies.append([x, y, k])
    data = {"source": "hand-made text map", "credit": "", "size": [W, H], "blocks": blocks,
            "buildings": buildings, "entrances": entrances, "exit": exit_rect,
            "hero_start": [round(hero[0]), round(hero[1])],
            "zombie_starts": [list(map(round, world(c, r))) for c, r in found["z"]]
            + [[*map(round, world(c, r)), "crawler"] for c, r in found["k"]],
            "supplies": supplies,
            "weapons": [[*map(round, world(c, r)), WEAPON_KINDS[i % len(WEAPON_KINDS)]] for i, (c, r) in enumerate(found["w"])]
            + [[*map(round, world(c, r)), "pistol"] for c, r in found["g"]]}
    img.save(out / "ground.png")
    (out / "area.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {cols}x{n} m, {len(blocks)} blocks, {len(buildings)} house(s), {len(entrances)} entrances")
    return img, blocks


def _merge(cells):
    """House wall cells (GRID) -> world rectangles (l, b, r, t)."""
    if not cells:
        return []
    return [(c0 * GRID, r0 * GRID, (c1 + 1) * GRID, (r1 + 1) * GRID) for c0, r0, c1, r1 in rects(cells)]


if __name__ == "__main__":
    rows = read(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2].startswith("area:"):         # a whole game area
        build(rows, sys.argv[2][5:])
    else:
        img, blocks = draw(rows)
        img.save(sys.argv[2])
        if len(sys.argv) > 3:
            debug(img, blocks, rows).save(sys.argv[3])
        print(f"{len(rows[0])}x{len(rows)} m, {len(blocks)} blocks")
