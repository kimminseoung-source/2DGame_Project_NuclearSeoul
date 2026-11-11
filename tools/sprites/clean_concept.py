"""Turn an AI concept image (fake pixel art on a flat key colour) into a game-size sprite.

    .venv\\Scripts\\python.exe tools/sprites/clean_concept.py assets/characters/concepts/hero_concept_a.webp
        --height 56 --out assets/characters/concepts/hero_concept_a_sprite.png

Steps: remove the key colour (magenta by default) -> keep the largest figure (drops logos
and specks) -> find the size of one "pixel" block in the concept -> sample one colour per
block (the concept's real pixel grid) -> scale to the game height with nearest neighbour
-> put it in a 96x64 cell with the feet on the floor line (CHARACTER_SPEC.md).
Needs Pillow (dev tool only, not used by the game).
"""

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image

CELL_W, CELL_H, FEET_FROM_BOTTOM = 96, 64, 4


def key_out(img, key, tolerance):
    """Remove the key colour and the soft edge pixels blended with it.

    For magenta, an edge pixel mixed with the background keeps red and blue well above
    green, so those are dropped too; otherwise a pink fringe shows around the figure.
    """
    px = img.load()
    w, h = img.size
    magenta = key == [255, 0, 255]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            close = abs(r - key[0]) + abs(g - key[1]) + abs(b - key[2]) < tolerance
            fringe = magenta and r - g > 35 and b - g > 35   # pink edge pixels mixed with the key
            if close or fringe:
                px[x, y] = (0, 0, 0, 0)
    return img


def outline(img, rgb=(16, 18, 26)):
    """1 px dark outline around the figure, like every other sprite in the game."""
    src = img.load()
    out = img.copy()
    dst = out.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            if any(0 <= x + dx < w and 0 <= y + dy < h and src[x + dx, y + dy][3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                dst[x, y] = (*rgb, 255)
    return out


def largest_component(img):
    """Keep only the biggest connected solid area (the character)."""
    w, h = img.size
    px = img.load()
    seen = bytearray(w * h)
    best = []
    for start in range(w * h):
        if seen[start] or px[start % w, start // w][3] == 0:
            continue
        stack, comp = [start], []
        seen[start] = 1
        while stack:
            i = stack.pop()
            comp.append(i)
            x, y = i % w, i // w
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                j = ny * w + nx
                if 0 <= nx < w and 0 <= ny < h and not seen[j] and px[nx, ny][3]:
                    seen[j] = 1
                    stack.append(j)
        if len(comp) > len(best):
            best = comp
    keep = bytearray(w * h)
    for i in best:
        keep[i] = 1
    for i in range(w * h):
        if not keep[i]:
            px[i % w, i // w] = (0, 0, 0, 0)
    return img.crop(img.getbbox())


def block_size(img):
    """Most common run length of identical colours = the concept's pixel size."""
    px = img.load()
    w, h = img.size
    runs = Counter()
    for y in range(0, h, 3):
        run, prev = 0, None
        for x in range(w):
            c = px[x, y]
            near = prev is not None and sum(abs(c[k] - prev[k]) for k in range(3)) < 24 and c[3] and prev[3]
            if near:
                run += 1
            else:
                if 2 <= run <= 16:
                    runs[run] += 1
                run = 1
            prev = c
    return max(runs, key=runs.get) if runs else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("--out", required=True)
    parser.add_argument("--height", type=int, default=56, help="figure height in game pixels")
    parser.add_argument("--key", default="255,0,255")
    parser.add_argument("--tolerance", type=int, default=150)
    args = parser.parse_args()
    img = Image.open(args.src).convert("RGBA")
    img = largest_component(key_out(img, [int(v) for v in args.key.split(",")], args.tolerance))
    block = block_size(img)
    native = img.resize((max(1, round(img.width / block)), max(1, round(img.height / block))), Image.NEAREST)
    # Shrink to the game height minus the outline, then draw the outline around it.
    inner = args.height - 2
    scale = inner / native.height
    sprite = native.resize((max(1, round(native.width * scale)), inner), Image.NEAREST)
    # Hard alpha: pixel art has no half-transparent edges.
    sprite.putalpha(sprite.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    padded = Image.new("RGBA", (sprite.width + 2, sprite.height + 2), (0, 0, 0, 0))
    padded.paste(sprite, (1, 1), sprite)
    sprite = outline(padded)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    cell.paste(sprite, ((CELL_W - sprite.width) // 2, CELL_H - FEET_FROM_BOTTOM - sprite.height), sprite)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cell.save(args.out)
    native.save(Path(args.out).with_name(Path(args.out).stem + "_native.png"))
    print(f"block {block}px -> native {native.size} -> game {sprite.size} in {CELL_W}x{CELL_H} cell: {args.out}")


if __name__ == "__main__":
    main()
