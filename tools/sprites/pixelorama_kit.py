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


def best_shift(base, frame, reach=4):
    """How far `frame` sits from `base` (both one cell, RGBA): the (dx, dy) that makes the most of
    their solid pixels overlap - the body bobbing a pixel or two while it breathes or steps."""
    a = base.getchannel("A").load()
    b = frame.getchannel("A").load()
    w, h = base.size
    solid = [(x, y) for y in range(h) for x in range(w) if a[x, y]]
    best, score = (0, 0), -1
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            s = sum(1 for x, y in solid if 0 <= x + dx < w and 0 <= y + dy < h and b[x + dx, y + dy])
            if s > score:
                best, score = (dx, dy), s
    return best


LOCAL = 4           # changed pixels in the same 4 x 4 block share one measured move
WINDOW = 5          # px around a changed spot compared to find where it went
REACH = 3           # px a spot may have moved between frames


def local_shift(base, frame, x, y):
    """Where the neighbourhood of (x, y) in `base` went in `frame` (both pixel access objects):
    the (dx, dy) whose window matches best, colour and see-through alike; no move wins ties."""
    best, score = (0, 0), None
    for dy in range(-REACH, REACH + 1):
        for dx in range(-REACH, REACH + 1):
            miss = 0
            for wy in range(y - WINDOW, y + WINDOW + 1):
                for wx in range(x - WINDOW, x + WINDOW + 1):
                    if not (0 <= wx < CELL_W and 0 <= wy < CELL_H):
                        continue
                    a = base[wx, wy]
                    tx, ty = wx + dx, wy + dy
                    b = frame[tx, ty] if 0 <= tx < CELL_W and 0 <= ty < CELL_H else (0, 0, 0, 0)
                    if (a[3] > 0) != (b[3] > 0) or (a[3] and a[:3] != b[:3]):
                        miss += 1
            key = (miss, abs(dx) + abs(dy))
            if score is None or key < score:
                best, score = (dx, dy), key
    return best


def spread(names):
    """Key frame (2026-11-18 "내가 작업하면 4개가 다 일정하지 않은데"): only frame 1 is drawn by
    hand; every pixel changed there is copied onto the other frames, moved by how far each frame's
    body has moved from frame 1. Run after editing frame 1 of work/<character>/<pose>.png."""
    for name in names:
        char, pose = name.split("/")
        work = KIT / "work" / char / f"{pose}.png"
        original = Image.open(CHARS / char / f"{pose}.png").convert("RGBA")
        edited = Image.open(work).convert("RGBA")
        if edited.size != original.size:
            print(f"{name}: size {edited.size} is not {original.size}")
            continue
        frames = original.width // CELL_W
        cell = lambda im, n: im.crop((n * CELL_W, 0, (n + 1) * CELL_W, CELL_H))
        base_old, base_new = cell(original, 0), cell(edited, 0)
        po, pn = base_old.load(), base_new.load()
        changes = [(x, y, pn[x, y]) for y in range(CELL_H) for x in range(CELL_W) if po[x, y] != pn[x, y]]
        out = edited.copy()
        for n in range(1, frames):
            frame = cell(original, n)
            fp = frame.load()
            moves = {}
            for x, y, colour in changes:
                # the move is measured around the changed spot, not the whole body: the feet stay
                # put while the head bobs (whole-body matching said "no move" for a lifted head)
                block = (x // LOCAL, y // LOCAL)
                if block not in moves:
                    moves[block] = local_shift(po, fp, x, y)
                dx, dy = moves[block]
                tx, ty = x + dx, y + dy
                if 0 <= tx < CELL_W and 0 <= ty < CELL_H:
                    fp[tx, ty] = colour
            out.paste(frame, (n * CELL_W, 0))
            seen = sorted(set(moves.values()))
            print(f"{name} frame {n + 1}: {len(changes)} pixels copied, moves used {seen}")
        out.save(work)
        guide(work, KIT / "guide" / f"{char}_{pose}_spread.png", f"{char}/{pose} · 1번을 나머지에 옮긴 결과")


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("kit", "in", "spread"):
        print(__doc__)
        sys.exit(1)
    {"kit": kit, "in": bring_in, "spread": spread}[sys.argv[1]](sys.argv[2:])
