"""Paint the hero's clothes in 2D pixel art over the base body's frames (no 3D clothes).

    .venv\\Scripts\\python.exe tools/sprites/paint_clothes.py --id <id pass dir> --light <light pass dir>
        --poses poses1.json poses2.json --out <dir> [sheets...]

The base body keeps its motion; this draws over every frame, pixel by pixel:
- part map (id pass of costumes/base_parts.json: head, top, arms and legs split into the
  near "_r" and far "_l" side) + light (light pass) cut into three bands;
- concept colours (ramps below, picked from concepts/hero_concept_a): skin, hair, a
  mustard jacket over torso and arms (one pixel bulkier, covering the hips, with a hem line
  and a hood collar at the back of the neck), dark cargo trousers with a pocket mark, chunky
  boots, black gloves; far limbs one shade darker;
- the concept's own backpack and bat pixel art (parts sheet), shrunk to game size: the pack
  on the back following the torso tilt, the bat in the near hand at the action's angle
  (tools/blender/export_pose2d.py), the near hand drawn over the handle;
- a 1 px dark outline.
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import clean_concept as cc  # noqa: E402
from repaint import to_display  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "assets/characters/concepts/hero_parts_a.webp"
PACK_BOX, BAT_BOX = (320, 58, 418, 185), (752, 383, 968, 411)
PACK_H, BAT_LEN = 15, 22                       # game pixels
CUTS = (115, 160)
OUTLINE = (16, 18, 26, 255)
RAMPS = {
    "skin": [(150, 92, 62), (214, 152, 108), (234, 176, 132)],
    "hair": [(28, 22, 20), (46, 38, 34), (66, 56, 50)],
    "jacket": [(128, 82, 30), (178, 124, 44), (214, 160, 66)],
    "hood": [(104, 66, 24), (140, 94, 34), (176, 126, 48)],
    "trousers": [(38, 36, 34), (58, 56, 52), (82, 80, 74)],
    "boots": [(24, 22, 20), (42, 36, 30), (64, 56, 46)],
    "gloves": [(24, 24, 24), (40, 38, 38), (60, 58, 56)],
    "eyes": [(20, 16, 16)] * 3,
}
JACKET = {"top", "top_r", "top_l", "forearms_r", "forearms_l"}
LEGS = {"bottom", "bottom_r", "bottom_l"}
FEET = {"shoes_r", "shoes_l"}
HANDS = {"hands_r", "hands_l"}


def part_map(id_img, ids):
    shown = {p: to_display(c) for p, c in ids.items()}
    px = id_img.load()
    w, h = id_img.size
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= 128:
                out[y][x] = min(shown, key=lambda p: sum((u - v) ** 2 for u, v in zip(shown[p], (r, g, b))))
    return out


def cells(part, region_set):
    return [(x, y) for y, row in enumerate(part) for x, p in enumerate(row) if p in region_set]


def level(light, x, y):
    v = light[x, y][0]
    return 0 if v < CUTS[0] else 1 if v < CUTS[1] else 2


def paint_frame(part, light, pose, pack, bat):
    h, w = len(part), len(part[0])
    paint = {}                                     # (x, y) -> (ramp, level, far)

    def put(x, y, ramp, lv, far=False):
        if 0 <= x < w and 0 <= y < h:
            paint[(x, y)] = (ramp, max(0, lv - (1 if far else 0)))

    head = cells(part, {"head"})
    torso = cells(part, {"top"})
    # Base colours by part.
    for y in range(h):
        for x in range(w):
            p = part[y][x]
            if p is None:
                continue
            lv = level(light, x, y)
            far = p.endswith("_l")
            if p in JACKET:
                put(x, y, "jacket", lv)                # sleeves match the jacket (no dark spots)
            elif p in LEGS:
                put(x, y, "trousers", lv, far)
            elif p in FEET:
                put(x, y, "boots", lv, far)
            elif p in HANDS:
                put(x, y, "gloves", lv, far)
            elif p == "eyes":
                put(x, y, "eyes", 0)
            else:                                  # head, brows
                put(x, y, "skin", lv)
    # Hair: the top 45 % of the head and its back half above the ear line.
    if head:
        top, bottom = min(y for _, y in head), max(y for _, y in head)
        left, right = min(x for x, _ in head), max(x for x, _ in head)
        cx = (left + right) / 2
        for x, y in head:
            if y <= top + (bottom - top) * 0.42 or (x < cx and y <= top + (bottom - top) * 0.75):
                put(x, y, "hair", level(light, x, y))
        for x in range(left, right + 1):           # one pixel of volume on top
            col = [y for hx, y in head if hx == x]
            if col:
                put(x, min(col) - 1, "hair", 1)
    # Jacket: one pixel bulkier around the torso, covering the hips, hem and hood collar.
    if torso:
        tbottom = max(y for _, y in torso)
        ttop = min(y for _, y in torso)
        for x, y in list(torso):
            for dx, dy in ((1, 0), (-1, 0)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and part[ny][nx] is None:
                    put(nx, ny, "jacket", level(light, x, y))
        # The jacket covers the hips: trouser pixels within 2 px of the torso (by distance,
        # not height, so a body lying down keeps its trousers).
        torso_set = set(torso)
        for x, y in cells(part, LEGS):
            if any((x + dx, y + dy) in torso_set for dx in range(-2, 3) for dy in range(-2, 3)):
                put(x, y, "jacket", level(light, x, y))
        back = min(x for x, y in torso if y <= ttop + 2)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 1), (2, 0)):
            put(back + dx - 1, ttop + dy - 1, "hood", 1)
    # Cargo pocket on the near thigh.
    thigh = cells(part, {"bottom_r"})
    if thigh:
        ys = sorted(y for _, y in thigh)
        mid = ys[len(ys) // 2]
        xs = sorted(x for x, y in thigh if y == mid)
        if xs:
            for dx in range(2):
                for dy in range(3):
                    put(xs[len(xs) // 2] + dx - 1, mid + dy - 1, "trousers", 0)
    # Boots: one pixel wider and two pixels up the shin.
    for x, y in cells(part, FEET):
        far = part[y][x].endswith("_l")
        for dx, dy in ((1, 0), (-1, 0), (0, -1), (0, -2)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (part[ny][nx] is None or part[ny][nx] in LEGS):
                put(nx, ny, "boots", 1, far)

    # Layers: far limbs, then the backpack, then the torso and near limbs over it.
    far_px = {k for k in paint if part[k[1]][k[0]] is not None and part[k[1]][k[0]].endswith("_l")}
    layers = [Image.new("RGBA", (w, h)) for _ in range(2)]
    for (x, y), (ramp, lv) in paint.items():
        layers[0 if (x, y) in far_px else 1].putpixel((x, y), (*RAMPS[ramp][max(0, min(2, lv))], 255))
    frame = Image.new("RGBA", (w, h))
    frame.alpha_composite(layers[0])
    if torso and pack is not None:
        tilt = math.degrees(math.atan2(pose["neck"][0] - pose["hip"][0], -(pose["neck"][1] - pose["hip"][1])))
        p = pack.rotate(-tilt, resample=Image.NEAREST, expand=True)
        ttop = min(y for _, y in torso)
        # The back line: the torso's rearmost pixel on the chest rows (the far arm may hang
        # behind the torso, the pack still sits on the back).
        rows = range(ttop + 2, ttop + 10)
        back = min((x for x, y in torso if y in rows), default=min(x for x, _ in torso))
        frame.alpha_composite(p, (back - p.width + 3, ttop))
    frame.alpha_composite(layers[1])
    # Bat in the near hand at the action's angle; the near hand over the handle.
    near = cells(part, {"hands_r"})
    if near and bat is not None:
        gx = sum(x for x, _ in near) / len(near)
        gy = sum(y for _, y in near) / len(near)
        ang = math.degrees(math.atan2(pose["bat_dir"][1], pose["bat_dir"][0]))
        big = Image.new("RGBA", (BAT_LEN * 3, BAT_LEN * 3))
        grip = (BAT_LEN * 3 // 2, BAT_LEN * 3 // 2)
        big.paste(bat, (grip[0] - 2, grip[1] - bat.height // 2), bat)
        rot = big.rotate(-ang, resample=Image.NEAREST, center=grip)
        frame.alpha_composite(rot, (round(gx - grip[0]), round(gy - grip[1])))
        for x, y in near:
            frame.putpixel((x, y), (*RAMPS["gloves"][level(light, x, y)], 255))
    return cc.outline(frame, OUTLINE[:3])


def load_props():
    sheet = cc.key_out(Image.open(PARTS).convert("RGBA"), [255, 0, 255], 150)
    pack = sheet.crop(PACK_BOX)
    pack = pack.resize((max(1, round(pack.width * PACK_H / pack.height)), PACK_H), Image.NEAREST)
    bat = sheet.crop(BAT_BOX)
    bat = bat.resize((BAT_LEN, max(2, round(bat.height * BAT_LEN / bat.width) + 1)), Image.NEAREST)
    for img in (pack, bat):
        img.putalpha(img.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    return pack, bat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--light", required=True)
    ap.add_argument("--poses", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-pack", action="store_true", help="draw no backpack")
    ap.add_argument("sheets", nargs="*")
    a = ap.parse_args()
    ids = json.loads((Path(a.id) / "ids.json").read_text(encoding="utf-8"))
    poses = {}
    for p in a.poses:
        poses.update(json.loads(Path(p).read_text(encoding="utf-8")))
    pack, bat = load_props()
    if a.no_pack:
        pack = None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for sheet in a.sheets or list(poses):
        id_img = Image.open(Path(a.id) / f"{sheet}.png").convert("RGBA")
        light_img = Image.open(Path(a.light) / f"{sheet}.png").convert("RGBA")
        n = id_img.width // 96
        strip = Image.new("RGBA", (96 * n, 64))
        for i in range(n):
            box = (i * 96, 0, i * 96 + 96, 64)
            part = part_map(id_img.crop(box), ids)
            light = light_img.crop(box).load()
            pose = poses[sheet][min(i, len(poses[sheet]) - 1)]
            strip.alpha_composite(paint_frame(part, light, pose, pack, bat), (i * 96, 0))
        strip.save(out / f"{sheet}.png")
        print("saved", out / f"{sheet}.png", n, "frames")


if __name__ == "__main__":
    main()
