"""Hand-finishing the dot sprites in Pixelorama (2026-11-18 "지금까지 한 거를 pixelorama로 해 보죠").

The sheets stay made the way they are (Blender render -> 32 px dot, render_character.py and
dot_palette.py); this adds a hand pass on top: outlines, face, hands, folds, wounds.

    .venv\\Scripts\\python.exe tools/sprites/pixelorama_kit.py kit infected_dot/idle [hero_dot/walk ...]
        -> assets/characters/pixelorama/work/<character>/<pose>.png   the sheet to open and edit
           assets/characters/pixelorama/guide/<character>_<pose>.png  8x enlarged, frame grid and numbers
           assets/characters/pixelorama/palette_busan.gpl             the game's colours for Pixelorama

    .venv\\Scripts\\python.exe tools/sprites/pixelorama_kit.py in infected_dot/idle
        -> checks the edited sheet (same size, every pixel solid or empty, colours off the palette),
           keeps the original in pixelorama/before/, puts the edited one in the game and writes
           pixelorama/compare/<character>_<pose>.png (before above, after below, 6x)

A sheet is one row of 64 x 48 cells (look.json "_size"), one frame per cell, feet 3 px above the
bottom: draw inside each cell and keep the feet where they are, or the character will hop.
Needs Pillow (dev tool only).
"""

import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CHARS = ROOT / "assets" / "characters"
KIT = CHARS / "pixelorama"
CELL_W, CELL_H = 64, 48
FONT = ROOT / "assets" / "fonts" / "galmuri" / "Galmuri11-Bold.ttf"


def palette():
    """The game's colours in the order assets/palette.png has them."""
    im = Image.open(ROOT / "assets" / "palette.png").convert("RGB")
    seen = []
    for y in range(im.height):
        for x in range(im.width):
            c = im.getpixel((x, y))
            if c not in seen:
                seen.append(c)
    return seen


def write_gpl():
    lines = ["GIMP Palette", "Name: busan", "Columns: 10", "#"]
    lines += [f"{r:3d} {g:3d} {b:3d}\tbusan{i:02d}" for i, (r, g, b) in enumerate(palette())]
    (KIT / "palette_busan.gpl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def guide(sheet, out, label):
    """8x enlarged on a mid grey, a line between frames, the frame number over each, the feet line."""
    k = 8
    im = Image.open(sheet).convert("RGBA")
    frames = im.width // CELL_W
    big = Image.new("RGBA", (im.width * k, im.height * k + 28), (70, 72, 76, 255))
    big.alpha_composite(im.resize((im.width * k, im.height * k), Image.NEAREST), (0, 28))
    d = ImageDraw.Draw(big)
    f = ImageFont.truetype(str(FONT), 18)
    d.text((6, 4), label, font=f, fill=(230, 200, 110))
    feet = 28 + (CELL_H - 3) * k
    for n in range(frames):
        x = n * CELL_W * k
        d.line([(x, 28), (x, big.height)], fill=(230, 200, 110), width=2)
        d.text((x + 6, 32), str(n + 1), font=f, fill=(230, 200, 110))
    d.line([(0, feet), (big.width, feet)], fill=(120, 170, 230), width=1)       # where the feet stand
    big.save(out)


def kit(names):
    for sub in ("work", "guide", "before", "compare"):
        (KIT / sub).mkdir(parents=True, exist_ok=True)
    write_gpl()
    for name in names:
        char, pose = name.split("/")
        src = CHARS / char / f"{pose}.png"
        (KIT / "work" / char).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, KIT / "work" / char / f"{pose}.png")
        frames = Image.open(src).width // CELL_W
        guide(src, KIT / "guide" / f"{char}_{pose}.png", f"{char}/{pose} · {frames}프레임 · 한 칸 {CELL_W}x{CELL_H} · 파란 선 = 발")
        print(f"{name}: {frames} frames -> work/{char}/{pose}.png")


def bring_in(names):
    pal = set(palette())
    for name in names:
        char, pose = name.split("/")
        edited = KIT / "work" / char / f"{pose}.png"
        game = CHARS / char / f"{pose}.png"
        new, old = Image.open(edited).convert("RGBA"), Image.open(game).convert("RGBA")
        if new.size != old.size:
            print(f"{name}: size {new.size} is not {old.size} - not taken (export the sheet at its own size)")
            continue
        soft = off = 0
        px = new.load()
        for y in range(new.height):
            for x in range(new.width):
                r, g, b, a = px[x, y]
                if 0 < a < 255:
                    soft += 1
                    px[x, y] = (r, g, b, 255 if a >= 128 else 0)        # dot art: solid or empty
                elif a and (r, g, b) not in pal:
                    off += 1
        before = KIT / "before" / char
        before.mkdir(parents=True, exist_ok=True)
        if not (before / f"{pose}.png").exists():
            shutil.copyfile(game, before / f"{pose}.png")              # the first original, kept once
        new.save(game)
        k = 6
        cmp = Image.new("RGBA", (old.width * k, old.height * k * 2 + 8), (70, 72, 76, 255))
        cmp.alpha_composite(old.resize((old.width * k, old.height * k), Image.NEAREST), (0, 0))
        cmp.alpha_composite(new.resize((new.width * k, new.height * k), Image.NEAREST), (0, old.height * k + 8))
        cmp.save(KIT / "compare" / f"{char}_{pose}.png")
        print(f"{name}: in the game | half-see-through pixels made solid: {soft} | colours off the palette: {off}")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("kit", "in"):
        print(__doc__)
        sys.exit(1)
    (kit if sys.argv[1] == "kit" else bring_in)(sys.argv[2:])
