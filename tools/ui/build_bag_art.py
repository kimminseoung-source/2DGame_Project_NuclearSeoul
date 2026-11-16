"""Export the bag screen's and the HUD's fixed pixel art for the game (2026-11-16, bag B v4 "이대로 구현").

The pictures come from the same drawing code as the approved mockup (ui_mockup_bag.py), drawn on
the 640x360 pixel canvas; the game draws them x2 with no smoothing (src/pixel_ui.py).

usage: python tools/ui/build_bag_art.py            -> assets/ui/bag/*.png
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from ui_mockup_bag import (ASPHALT_HI, CELL, GREY, GRID, METAL, NEAR_GRID, TARP, TARP_DARK,  # noqa: E402
                           TARP_LIGHT, H, INK, W, big_icon, cells, crisp, pix_icon)
from ui_mockup_v2 import BLOOD_DARK, dither_edge, paper, tape  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "assets" / "ui" / "bag"
MARGIN = 12                    # sheet edge around the grid
KINDS = ("bandage", "can", "pill", "backpack", "machete", "drop", "snail")


def sheet():
    """The olive ground sheet with its stitched cells; the grid starts at (MARGIN, MARGIN)."""
    gw, gh = GRID[0] * CELL, GRID[1] * CELL
    w, h = gw + 2 * MARGIN, gh + 2 * MARGIN
    img = Image.new("RGBA", (w + 4, h + 4), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    rnd = random.Random(9)
    l, t, r, b = 0, 0, w, h
    pts = [(l, t + 2), (r - 1, t), (r, b - 1), (l + 2, b)]
    d.polygon([(x + 3, y + 3) for x, y in pts], fill=(4, 4, 6))
    d.polygon(pts, fill=TARP, outline=INK)
    for _ in range(w * h // 12):
        x, y = rnd.randint(l + 2, r - 2), rnd.randint(t + 3, b - 3)
        d.point((x, y), fill=TARP_DARK if (x * y) % 5 else TARP_LIGHT)
    for (cx, cy) in ((l + 5, t + 5), (r - 6, t + 4), (r - 5, b - 6), (l + 6, b - 5)):
        d.rectangle((cx - 2, cy - 2, cx + 2, cy + 2), outline=METAL)
    cells(d, MARGIN, MARGIN, *GRID, (50, 54, 38), TARP_LIGHT)
    return img


def ground():
    """The asphalt patch for things lying nearby; the grid starts at (4, 4)."""
    gw, gh = NEAR_GRID[0] * CELL, NEAR_GRID[1] * CELL
    img = Image.new("RGBA", (gw + 9, gh + 9), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    rnd = random.Random(3)
    d.rectangle((0, 0, gw + 8, gh + 8), fill=(30, 32, 36), outline=ASPHALT_HI)
    for _ in range(140):
        d.point((rnd.randint(1, gw + 7), rnd.randint(1, gh + 7)), fill=ASPHALT_HI)
    cells(d, 4, 4, *NEAR_GRID, (70, 72, 76), ASPHALT_HI)
    return img


def dither():
    """Darkens the world in a checker dither instead of a smooth glass layer."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            if (x + y) % 2 == 0 or y % 2 == 0:
                d.point((x, y), fill=(6, 6, 8, 255))
    return img


def body():
    """The body outline of the bag screen's left column (wounds are drawn on it by the game)."""
    img = Image.new("RGBA", (40, 102), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    cx, cy, o = 20, 0, GREY
    d.ellipse((cx - 7, cy, cx + 7, cy + 14), outline=o)
    d.rectangle((cx - 12, cy + 17, cx + 12, cy + 58), outline=o)
    d.rectangle((cx - 19, cy + 18, cx - 14, cy + 54), outline=o)
    d.rectangle((cx + 14, cy + 18, cx + 19, cy + 54), outline=o)
    d.rectangle((cx - 11, cy + 60, cx - 2, cy + 100), outline=o)
    d.rectangle((cx + 2, cy + 60, cx + 11, cy + 100), outline=o)
    return img


def icons():
    for kind in KINDS:
        small = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        pix_icon(crisp(ImageDraw.Draw(small)), kind, 0, 0)
        small.save(OUT / f"icon_{kind}.png")
        big = Image.new("RGBA", (34, 34), (0, 0, 0, 0))
        big_icon(big, kind, 0, 0)
        big.save(OUT / f"big_{kind}.png")


def note():
    """The goal note of the HUD (UI v2): a torn scrap of paper with a strip of tape; the words are
    written on it by the game."""
    img = Image.new("RGBA", (172, 46), (0, 0, 0, 0))
    d = crisp(ImageDraw.Draw(img))
    paper(d, (6, 3, 166, 41), 3)
    tape(d, 0, 0)
    return img


def bleed_edge():
    """The screen edge going red in an ordered dither while bleeding (UI v2, no blur)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dither_edge(img, BLOOD_DARK, 0.6)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    note().save(OUT.parent / "note.png")
    bleed_edge().save(OUT.parent / "bleed_edge.png")
    sheet().save(OUT / "sheet.png")
    ground().save(OUT / "ground.png")
    dither().save(OUT / "dither.png")
    body().save(OUT / "body.png")
    icons()
    print("saved", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
