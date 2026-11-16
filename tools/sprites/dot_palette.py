"""The dot look's pictures and its one palette (2026-11-16 "도트 형식으로").

1. The area (ground, wrecks; rendered in Blender at 1 px per world unit) is shrunk to the dot
   density - DOT = 32 / 54, the 32 px person against the original 54 - by averaging, so the street
   has the same pixel size as the characters (a dot character on a smooth street looks pasted on).
2. One palette for the whole game: a few fixed colours (the outline, the UI's ink / paper / road
   yellow / blood) plus colours picked from all dot pictures (median cut) up to PALETTE_SIZE.
3. Every dot picture (character sheets, area) is mapped onto that palette.
   Run it on freshly rendered sheets (render_character.py --size dot): it rewrites them in place.

    .venv\\Scripts\\python.exe tools/sprites/dot_palette.py <character folder> [...]
    (e.g. hero infected) -> assets/area/dot/*.png, assets/palette.png, sheets remapped in place
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DOT = 32 / 54
PALETTE_SIZE = 32
# Fixed colours: the outline and UI (ink, light paper, road yellow, blood), then small areas the
# median cut would merge into the greys (first try lost them): the infected's green skin and
# glowing wounds and eyes, the hero's skin and jacket, the faded road paint on the asphalt.
FIXED = [(16, 18, 26), (34, 30, 28), (222, 216, 198), (196, 170, 92), (168, 34, 30),
         (92, 104, 88), (128, 140, 116), (60, 160, 90), (130, 230, 140), (200, 255, 190),
         (214, 152, 108), (178, 124, 44), (85, 81, 64)]
AREA = ROOT / "assets" / "area"


def shrink_area():
    out = AREA / "dot"
    out.mkdir(exist_ok=True)
    made = []
    for f in sorted(AREA.glob("*.png")):
        img = Image.open(f).convert("RGBA")
        small = img.resize((max(1, round(img.width * DOT)), max(1, round(img.height * DOT))), Image.BOX)
        small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        small.save(out / f.name)
        made.append(out / f.name)
    return made


def sheets(folders):
    for folder in folders:
        for f in sorted((ROOT / "assets" / "characters" / folder).glob("*.png")):
            yield f


def build_palette(files):
    pixels = []
    for f in files:
        img = Image.open(f).convert("RGBA")
        step = 1 if img.width * img.height < 200_000 else 3          # the big ground: a sample is enough
        data = img.load()
        for y in range(0, img.height, step):
            for x in range(0, img.width, step):
                r, g, b, a = data[x, y]
                if a == 255:
                    pixels.append((r, g, b))
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    picked = strip.quantize(PALETTE_SIZE - len(FIXED), method=Image.Quantize.MEDIANCUT).getpalette()
    picked = [tuple(picked[i:i + 3]) for i in range(0, (PALETTE_SIZE - len(FIXED)) * 3, 3)]
    return FIXED + [c for c in picked if c not in FIXED]


def nearest(colour, palette, cache):
    if colour not in cache:
        r, g, b = colour
        # weighted distance: the eye is most sensitive to green, least to blue
        cache[colour] = min(palette, key=lambda p: 2 * (p[0] - r) ** 2 + 4 * (p[1] - g) ** 2 + 3 * (p[2] - b) ** 2)
    return cache[colour]


def remap(f, palette, cache):
    img = Image.open(f).convert("RGBA")
    data = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = data[x, y]
            if a:
                data[x, y] = (*nearest((r, g, b), palette, cache), 255)
    img.save(f)


def main(folders):
    area = shrink_area()
    weapons = sorted((ROOT / "assets" / "weapons").glob("*.png"))     # held in the hand by the game
    files = list(sheets(folders)) + area + weapons
    palette = build_palette(files)
    swatch = Image.new("RGB", (len(palette), 1))
    swatch.putdata(palette)
    swatch.resize((len(palette) * 12, 12), Image.NEAREST).save(ROOT / "assets" / "palette.png")
    cache = {}
    for f in files:
        remap(f, palette, cache)
    print(len(palette), "colours;", len(files), "pictures remapped")


if __name__ == "__main__":
    main(sys.argv[1:])
