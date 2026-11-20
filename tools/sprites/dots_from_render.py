"""Sprite-size 3D render -> finished pixel art (2026-11-20, docs/study/05_3D를_도트로.md).

    .venv\\Scripts\\python.exe tools/sprites/dots_from_render.py <in.png ...> --out <dir> [--colours 14]

For renders with real textures (tools/blender/mpfb_pose.py --pixel), where there is no
part-ID pass to repaint from:
1. hard edge: alpha cut at half, no soft border pixels;
2. few colours: all frames together are reduced to one small palette (median cut), so every
   frame of an action shares the same colours (no flicker between frames);
3. cleanup: a lone pixel whose four neighbours share one other colour takes it;
4. outline: 1 px around the figure in the game's outline colour (purple-black, as the
   PixelLab hero), and inner edges where a much darker colour meets a light one stay as drawn.
Same feet row is kept: nothing is moved.
"""

import argparse
from pathlib import Path

from PIL import Image

OUTLINE = (22, 19, 22)


def palette_for(images, colours):
    strip = Image.new("RGB", (sum(i.width for i in images), max(i.height for i in images)))
    x = 0
    pix = []
    for im in images:
        rgb = Image.new("RGB", im.size, (0, 0, 0))
        rgb.paste(im.convert("RGB"), mask=im.getchannel("A").point(lambda v: 255 if v >= 128 else 0))
        strip.paste(rgb, (x, 0))
        pix += [im.getpixel((px, py))[:3] for py in range(im.height) for px in range(im.width) if im.getpixel((px, py))[3] >= 128]
        x += im.width
    sample = Image.new("RGB", (len(pix), 1))
    sample.putdata(pix)
    return sample.quantize(colors=colours, method=Image.Quantize.MEDIANCUT)


def finish(im, pal):
    w, h = im.size
    solid = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    q = im.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGB")
    out = Image.new("RGBA", (w, h))
    out.paste(q, mask=solid)
    op = out.load()
    for y in range(h):                                   # lone pixels
        for x in range(w):
            if not op[x, y][3]:
                continue
            ns = [op[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= x + dx < w and 0 <= y + dy < h]
            if len(ns) == 4 and all(n[3] for n in ns) and len({n for n in ns}) == 1 and ns[0] != op[x, y]:
                op[x, y] = ns[0]
    edge = [(x, y) for y in range(h) for x in range(w) if not op[x, y][3] and any(
        0 <= x + dx < w and 0 <= y + dy < h and op[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        op[x, y] = OUTLINE + (255,)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--colours", type=int, default=14)
    a = ap.parse_args()
    ims = [Image.open(p).convert("RGBA") for p in a.images]
    pal = palette_for(ims, a.colours)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for p, im in zip(a.images, ims):
        finish(im, pal).save(out / Path(p).name)
        print("saved", out / Path(p).name)


if __name__ == "__main__":
    main()
