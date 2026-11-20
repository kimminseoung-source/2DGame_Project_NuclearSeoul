"""Repaint Blender pose renders with the concept art's colours, part by part (rotoscoping).

    .venv\\Scripts\\python.exe tools/sprites/repaint.py --costume assets/characters/costumes/hero_b.json
        --id <id pass dir> --light <light pass dir> --out <dir> [sheets...]

Inputs per sheet (same frames, same pixels): the ID pass (each part in its own flat colour,
ids.json says which) and the light pass (a white body, so brightness = light). For every
pixel: part from the ID colour, light level from the light pass cut into three bands, then
the colour from that part's ramp [dark, mid, light] in the costume's "ramps" (sampled from
the concept image). Finally a 1 px dark outline, like every sprite in the game.

Optional pixel-art finishing (costume "repaint", 2026-11-20, from hand-made sprite practice):
- "outline": the outline colour (the PixelLab hero uses a purple-black, not pure black);
- "inner_lines": parts that get a 1 px line of their own darkest shade where they meet
  another part (a jacket's edge over the shirt, an arm over the body), so shapes read at 36 px
  the way artists draw them (selective inner lines, not black);
- "cleanup": a lone pixel whose four neighbours all share one other colour of the same part
  takes that colour (no orphan pixels / noise inside a shape).
Needs Pillow (dev tool only).
"""

import argparse
import json
from pathlib import Path

from PIL import Image

OUTLINE = (16, 18, 26, 255)


def to_display(c):
    """The ID colours are stored linear; the render shows them sRGB-encoded."""
    def enc(v):
        v /= 255
        v = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        return round(v * 255)
    return tuple(enc(v) for v in c)


def repaint(id_img, light_img, ids, ramps, part_ramp, cuts, tex_img=None, splits=None,
            outline=OUTLINE, inner_lines=(), cleanup=False):
    """splits: part -> {"below": luminance, "ramp": name}: inside that part, pixels whose
    own texture (tex pass) is darker than "below" take another ramp (a cap or hair on the
    head region, gloves on the hands)."""
    w, h = id_img.size
    ip, lp = id_img.load(), light_img.load()
    tp = tex_img.load() if tex_img is not None else None
    splits = splits or {}
    shown = {part: to_display(c) for part, c in ids.items()}
    out = Image.new("RGBA", (w, h))
    op = out.load()
    names = {}                                          # (x, y) -> ramp name, for the finishing passes
    for y in range(h):
        for x in range(w):
            r, g, b, a = ip[x, y]
            if a < 128:
                continue
            part = min(shown, key=lambda p: sum((u - v) ** 2 for u, v in zip(shown[p], (r, g, b))))
            light = lp[x, y][0]
            level = 0 if light < cuts[0] else 1 if light < cuts[1] else 2
            name = part_ramp.get(part, part)
            rule = splits.get(part)
            if rule and tp is not None:
                tr, tg, tb, _ = tp[x, y]
                if 0.3 * tr + 0.59 * tg + 0.11 * tb < rule["below"]:
                    name = rule["ramp"]
            ramp = ramps[name]
            op[x, y] = (*ramp[level], 255)
            names[x, y] = name
    if cleanup:
        for (x, y), name in list(names.items()):
            around = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            if all(names.get(q) == name for q in around):
                cols = {op[q] for q in around}
                if len(cols) == 1 and op[x, y] not in cols:
                    op[x, y] = cols.pop()
    if inner_lines:
        marks = []
        for (x, y), name in names.items():
            if name in inner_lines and any(names.get((x + dx, y + dy), name) != name
                                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                marks.append((x, y, name))
        for x, y, name in marks:
            op[x, y] = (*ramps[name][0], 255)
    # 1 px outline around the figure.
    solid = [[op[x, y][3] > 0 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if solid[y][x]:
                continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and solid[y + dy][x + dx]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                op[x, y] = tuple(outline) + (255,) if len(outline) == 3 else tuple(outline)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--costume", required=True)
    parser.add_argument("--id", required=True)
    parser.add_argument("--light", required=True)
    parser.add_argument("--tex", default=None, help="tex pass dir (model texture, flat light)")
    parser.add_argument("--out", required=True)
    parser.add_argument("sheets", nargs="*")
    args = parser.parse_args()
    costume = json.loads(Path(args.costume).read_text(encoding="utf-8"))
    ids = json.loads((Path(args.id) / "ids.json").read_text(encoding="utf-8"))
    paint = costume["repaint"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sheets = args.sheets or [p.stem for p in Path(args.id).glob("*.png")]
    for sheet in sheets:
        id_img = Image.open(Path(args.id) / f"{sheet}.png").convert("RGBA")
        light_img = Image.open(Path(args.light) / f"{sheet}.png").convert("RGBA")
        tex_img = Image.open(Path(args.tex) / f"{sheet}.png").convert("RGBA") if args.tex else None
        repaint(id_img, light_img, ids, paint["ramps"], paint["part_ramp"], paint["cuts"],
                tex_img, paint.get("splits"), paint.get("outline", OUTLINE), paint.get("inner_lines", ()),
                paint.get("cleanup", False)).save(out / f"{sheet}.png")
        print("saved", out / f"{sheet}.png")


if __name__ == "__main__":
    main()
