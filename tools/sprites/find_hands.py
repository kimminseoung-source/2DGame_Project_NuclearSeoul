"""Find the weapon hand in every frame of an 8-direction PixelLab character (2026-11-19).

The game draws weapons as separate small pictures stuck to the hand (layered drawing,
"paper doll"), so the body is one empty-handed set for every weapon. This writes the hand
point of every frame:

    python tools/sprites/find_hands.py assets/characters/hero_px40

-> <folder>/hands.json   {"idle": {"south": [[x, y]], ...}, "walk": {"south": [[x, y], ...]}}
   (picture pixels, from the top-left of each frame's own image)
-> docs/planning/hands_check.png   every frame with its point, to look over

How: the hero's forearms are bare (sleeves rolled up), so a hand is the lowest clump of skin
colour in the lower part of the body. Which side of the picture is the weapon hand depends on
the direction: facing south the hero's right hand is on the picture's left, facing north on
its right; east and west take whichever hand shows lower. A frame where the hand is hidden
behind the body borrows the nearest frame's point. Hand-made fixes in <folder>/hands_fix.json
(same shape, only the frames to change) win over what is found.
"""

import colorsys
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

DIRS = ("east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east")
LEFT = {"south", "south-east", "south-west"}           # the weapon hand is on the picture's left
RIGHT = {"north", "north-east", "north-west"}          # ... on its right
LOWER_PART = 0.4                                       # hands are below this share of the body height
FEET_PART = 0.78                                       # ... and above this one (brown boots look like skin)


def is_skin(rgba):
    r, g, b, a = rgba
    if a < 200:
        return False
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return 0.02 < h < 0.12 and 0.2 < s < 0.65 and v > 0.55


def hand_in(image, direction):
    """(x, y) of the weapon hand in one picture, or None when no hand shows."""
    box = image.getchannel("A").getbbox()
    if not box:
        return None
    middle = (box[0] + box[2]) / 2
    top = box[1] + (box[3] - box[1]) * LOWER_PART
    sides = {"left": [], "right": []}
    bottom = box[1] + (box[3] - box[1]) * FEET_PART
    for y in range(int(top), int(bottom)):
        for x in range(box[0], box[2]):
            if is_skin(image.getpixel((x, y))):
                sides["left" if x < middle else "right"].append((x, y))
    if direction in LEFT:
        found = sides["left"]
    elif direction in RIGHT:
        found = sides["right"]
    else:                                              # east / west: the lower hand
        found = max(sides.values(), key=lambda pts: max((p[1] for p in pts), default=-1))
    if not found:
        return None
    lowest = max(p[1] for p in found)
    clump = [p for p in found if p[1] >= lowest - 1]
    return [round(sum(p[0] for p in clump) / len(clump), 1), round(sum(p[1] for p in clump) / len(clump), 1)]


def frames_of(folder):
    """{pose: {direction: [image paths in order]}} in the same layout DirLook reads."""
    poses = {}
    for path in sorted(Path(folder).rglob("*.png")):
        parent = path.parent
        if parent.name == "rotations" and path.stem in DIRS:
            poses.setdefault("idle", {})[path.stem] = [path]
        elif parent.name in DIRS:
            pose = "walk" if "walk" in parent.parent.name.lower() else parent.parent.name.lower()
            poses.setdefault(pose, {}).setdefault(parent.name, []).append(path)
    for by_dir in poses.values():
        for d, paths in by_dir.items():
            by_dir[d] = sorted(paths, key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)
    return poses


def fill_gaps(points):
    """Hidden hands borrow the nearest found frame (the animation loops)."""
    known = [i for i, p in enumerate(points) if p is not None]
    if not known:
        return points
    n = len(points)
    return [p if p is not None else points[min(known, key=lambda k: min(abs(k - i), n - abs(k - i)))]
            for i, p in enumerate(points)]


def main(folder):
    folder = Path(folder)
    poses = frames_of(folder)
    hands = {pose: {d: fill_gaps([hand_in(Image.open(p).convert("RGBA"), d) for p in paths])
                    for d, paths in by_dir.items()} for pose, by_dir in poses.items()}
    fix = folder / "hands_fix.json"
    if fix.exists():
        for pose, by_dir in json.loads(fix.read_text(encoding="utf-8")).items():
            for d, points in by_dir.items():
                for i, point in enumerate(points):
                    if point is not None:
                        hands[pose][d][i] = point
    (folder / "hands.json").write_text(json.dumps(hands, ensure_ascii=False, indent=1), encoding="utf-8")

    # A sheet to look over: every frame at 4x with its point.
    scale, cell = 4, 64 * 4
    rows = [(pose, d, paths) for pose, by_dir in poses.items() for d, paths in by_dir.items()]
    width = max(len(paths) for *_, paths in rows) * cell
    sheet = Image.new("RGB", (width + 120, len(rows) * cell), (40, 40, 44))
    draw = ImageDraw.Draw(sheet)
    for r, (pose, d, paths) in enumerate(rows):
        draw.text((width + 6, r * cell + 8), f"{pose}\n{d}", fill=(230, 230, 230))
        for i, path in enumerate(paths):
            im = Image.open(path).convert("RGBA")
            big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
            sheet.paste(big, (i * cell, r * cell), big)
            point = hands[pose][d][i]
            if point:
                cx, cy = i * cell + (point[0] + 0.5) * scale, r * cell + (point[1] + 0.5) * scale
                draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), outline=(255, 60, 60), width=2)
    out = Path(__file__).resolve().parents[2] / "docs" / "planning" / "hands_check.png"
    sheet.save(out)
    missing = sum(p is None for by_dir in hands.values() for pts in by_dir.values() for p in pts)
    print(f"hands.json: {sum(len(p) for b in hands.values() for p in b.values())} frames, {missing} without a hand -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "assets/characters/hero_px40")
