"""A piece of a real map as a text map (2026-11-16 "실제 지리를 글자 지도로", map plan: the real
place's streets and building spots as a sketch, buildings swapped for the game's own kinds, then
edited by hand in a text editor).

    python tools/map/osm_to_text.py <extract.osm> <out.txt> <lat_centre> <lon_centre> <width_m> <height_m>

One character is one metre. The map is turned so most building edges run along the grid (as
osm_area.py does). Characters:
    =  road            .  pavement / open ground
    #  a house (brick, flat roof)       B  a big building (offices, flats - drawn plain and solid)
    X  a real subway entrance (the way out)
Touching buildings are split by a one-metre alley so each stays its own block. The result is a
sketch: edit it freely (move the exit, add E for a house one can enter, c wrecks, z infected, S start).
"""
import sys
from math import atan2, cos, degrees, hypot, radians, sin
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from osm_area import ROAD_M, load, underground  # noqa: E402

BIG_M2 = 400               # a building bigger than this, or 4+ storeys, is drawn as a big block


def main(src, out, lat_c, lon_c, width_m, height_m):
    mx, my = 111320 * cos(radians(lat_c)), 110540
    ways, points = load(src)

    def to_m(ll):
        return (ll[1] - lon_c) * mx, (ll[0] - lat_c) * my

    votes = [0.0] * 90                                     # the turn: building edges' usual direction
    for tags, lls in ways:
        if "building" in tags and len(lls) >= 3:
            pts = [to_m(ll) for ll in lls]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                if hypot(x1, y1) < max(width_m, height_m) * 2:
                    votes[int(degrees(atan2(y2 - y1, x2 - x1)) % 90)] += hypot(x2 - x1, y2 - y1)
    best = max(range(90), key=lambda a: sum(votes[(a + k) % 90] for k in (-1, 0, 1)))
    turn = radians(best if best < 45 else best - 90)
    W, H = int(width_m), int(height_m)

    def grid(ll):                                          # (lat, lon) -> metres in the text, y down
        x, y = to_m(ll)
        x, y = x * cos(-turn) - y * sin(-turn), x * sin(-turn) + y * cos(-turn)
        return x + W / 2, H / 2 - y

    road = Image.new("L", (W, H), 0)
    rd = ImageDraw.Draw(road)
    for tags, lls in ways:
        hw = tags.get("highway")
        if hw in ROAD_M and not underground(tags) and len(lls) >= 2:
            metres = float(tags["lanes"]) * 3.3 if tags.get("lanes", "").isdigit() else ROAD_M[hw]
            rd.line([grid(ll) for ll in lls], fill=255, width=max(1, round(metres)), joint="curve")
    owner = [[-1] * W for _ in range(H)]                   # which building each metre belongs to
    kind = {}
    n = 0
    for tags, lls in ways:
        if "building" not in tags or len(lls) < 3 or underground(tags):
            continue
        pts = [grid(ll) for ll in lls]
        xs, ys = [x for x, _ in pts], [y for _, y in pts]
        if max(xs) < 0 or min(xs) > W or max(ys) < 0 or min(ys) > H:
            continue
        area = abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]))) / 2
        square = area / (((max(xs) - min(xs)) * (max(ys) - min(ys))) or 1)
        levels = tags.get("building:levels", "0")
        kind[n] = "B" if area > BIG_M2 or (levels.isdigit() and int(levels) >= 4) else "#"
        m = Image.new("L", (W, H), 0)
        if square >= 0.8:                                  # nearly a rectangle: snap it to one
            ImageDraw.Draw(m).rectangle((round(min(xs)), round(min(ys)), round(max(xs)) - 1, round(max(ys)) - 1), fill=255)
        else:
            ImageDraw.Draw(m).polygon(pts, fill=255)
        for y in range(H):
            for x in range(W):
                if m.getpixel((x, y)) and owner[y][x] < 0:
                    owner[y][x] = n
        n += 1
    rows = []
    for y in range(H):
        row = ""
        for x in range(W):
            o = owner[y][x]
            if o >= 0:
                apart = any(0 <= x + dx < W and 0 <= y + dy < H and owner[y + dy][x + dx] not in (-1, o)
                            for dx, dy in ((1, 0), (0, 1)))
                row += "." if apart else kind[o]           # a one-metre alley between two buildings
            elif road.getpixel((x, y)):
                row += "="
            else:
                row += "."
        rows.append(row)
    for tags, ll in points:
        if tags.get("railway") == "subway_entrance":
            x, y = grid(ll)
            if 1 <= x < W - 1 and 1 <= y < H - 1 and rows[int(y)][int(x)] == ".":
                r = rows[int(y)]
                rows[int(y)] = r[:int(x)] + "X" + r[int(x) + 1:]
    Path(out).write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"turned {degrees(turn):.0f} degrees, {W}x{H} m, {n} buildings")


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], float(a[3]), float(a[4]), float(a[5]), float(a[6]))
