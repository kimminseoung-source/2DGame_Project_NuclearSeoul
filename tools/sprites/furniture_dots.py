"""Furniture as hand-placed dot art (2026-11-16, ③ "칸마다 정리": the 3D render in
tools/blender/render_furniture.py is the reference for shape and light; every pixel here is set
on purpose - outline, three steps of light, highlights, a little wear).

    python tools/sprites/furniture_dots.py      -> assets/furniture/<name>.png

Each picture is the piece in the game's 3/4 view: its top face over its front face, light from the
upper left (left edges lit, right edges in shade), ~19 px per metre like the rest of the world.
tools/map/osm_area.py uses these when it furnishes a house.
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "furniture"
INK = (28, 24, 22)
# metal / enamel (fridge, stove): highlight, light, mid, shade, dark
ENAMEL = ((214, 218, 214), (186, 192, 190), (160, 166, 166), (122, 128, 130), (92, 96, 100))
WOOD = ((150, 114, 78), (128, 96, 62), (104, 76, 48), (78, 56, 36))
CLOTH = ((122, 138, 152), (98, 112, 128), (76, 88, 104))          # a worn blue blanket
SHEET = ((210, 206, 194), (182, 176, 164), (150, 144, 132))
RUST, GRIME, GLASS = (122, 88, 58), (138, 136, 120), (40, 42, 46)


class Pic:
    def __init__(self, w, h):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def dot(self, x, y, c):
        self.img.putpixel((x, y), c + (255,))

    def rect(self, x0, y0, x1, y1, c):               # inclusive
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.dot(x, y, c)

    def box(self, x0, y0, x1, y1, fill, lit, shade):
        """A face: fill, its left column lit, its right column in shade (just inside the outline)."""
        self.rect(x0, y0, x1, y1, fill)
        self.rect(x0 + 1, y0, x0 + 1, y1, lit)
        self.rect(x1 - 1, y0, x1 - 1, y1, shade)

    def outline(self):
        """A 1 px ink line round everything drawn (the characters have one too)."""
        w, h = self.img.size
        a = [[self.img.getpixel((x, y))[3] for y in range(h)] for x in range(w)]
        for x in range(w):
            for y in range(h):
                if a[x][y] and (x in (0, w - 1) or y in (0, h - 1) or not all(
                        a[x + dx][y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))):
                    self.dot(x, y, INK)


# Heights are shown at full size (~19 px a metre, like the hero: 1.7 m = 32 px) and top faces at
# their real depth - the game's 3/4 cheat, as in Stardew-like games.
def fridge():                                       # 0.8 x 0.6 m, 1.7 m tall
    H, L, M, S, D = ENAMEL
    p = Pic(18, 44)
    p.box(0, 0, 17, 10, L, H, S)                    # top
    p.rect(1, 1, 16, 1, H)
    p.rect(0, 11, 17, 11, D)                        # front top edge
    p.box(0, 12, 17, 41, M, H, S)                   # front
    p.rect(1, 21, 16, 21, D)                        # freezer / fridge doors
    p.rect(13, 14, 14, 18, D)                       # handles
    p.rect(13, 24, 14, 32, D)
    p.dot(13, 24, S); p.dot(13, 14, S)
    p.dot(6, 27, S); p.dot(10, 35, S); p.dot(11, 35, S)     # dents
    p.dot(3, 38, GRIME); p.dot(3, 39, RUST); p.dot(4, 39, GRIME); p.dot(4, 38, RUST)
    p.rect(1, 41, 16, 41, S)                        # kick plate
    p.rect(0, 42, 17, 43, D)
    p.outline()
    return p.img


def stove():                                        # 0.8 x 0.7 m, 0.9 m tall
    H, L, M, S, D = ENAMEL
    p = Pic(18, 30)
    p.box(0, 0, 17, 12, L, H, S)                    # top
    for bx, by in ((3, 2), (10, 2), (3, 7), (10, 7)):       # four burners
        p.rect(bx, by, bx + 4, by + 2, D)
        p.rect(bx + 1, by + 1, bx + 3, by + 1, GLASS)
        p.dot(bx + 2, by + 1, S)
    p.rect(0, 13, 17, 13, D)
    p.box(0, 14, 17, 28, M, H, S)                   # front
    for kx in (3, 6, 9, 12):                        # knobs
        p.dot(kx, 15, D); p.dot(kx, 16, S)
    p.rect(2, 18, 15, 26, D)                        # oven door
    p.rect(3, 19, 14, 25, GLASS)
    p.rect(4, 20, 7, 20, (70, 74, 80))              # a glint on the glass
    p.rect(4, 18, 13, 18, S)                        # its handle
    p.dot(15, 27, RUST); p.dot(14, 27, GRIME)
    p.rect(0, 29, 17, 29, D)
    p.outline()
    return p.img


def bed():                                          # 1.0 x 2.0 m, 0.5 m tall
    w1, w2, w3, w4 = WOOD
    s1, s2, s3 = SHEET
    c1, c2, c3 = CLOTH
    p = Pic(20, 48)
    p.box(0, 0, 19, 5, w2, w1, w3)                  # headboard
    p.rect(1, 1, 18, 1, w1)
    p.box(0, 6, 19, 38, w3, w2, w4)                 # frame
    p.rect(2, 6, 17, 37, s2)                        # mattress
    p.rect(3, 7, 16, 12, s1)                        # pillow
    p.rect(3, 12, 16, 12, s3)
    p.dot(4, 8, (230, 228, 220)); p.dot(5, 8, (230, 228, 220))
    p.rect(2, 15, 17, 37, c2)                       # blanket
    p.rect(2, 15, 17, 16, c1)                       # its folded-back edge, lit
    p.rect(2, 15, 2, 37, c1)
    p.rect(17, 17, 17, 37, c3)
    p.dot(8, 22, c3); p.dot(9, 23, c3); p.dot(10, 23, c3)   # creases
    p.dot(12, 30, c3); p.dot(13, 31, c3); p.dot(5, 27, c3)
    p.dot(6, 34, GRIME)
    p.box(0, 39, 19, 45, w3, w2, w4)                # front of the frame
    p.rect(2, 40, 17, 40, s3)                       # the mattress's side
    p.rect(1, 46, 3, 47, w4); p.rect(16, 46, 18, 47, w4)    # legs
    p.outline()
    return p.img


def table():                                        # 1.2 x 0.8 m, 0.75 m tall
    w1, w2, w3, w4 = WOOD
    p = Pic(28, 30)
    p.box(0, 0, 27, 14, w2, w1, w3)                 # top
    for y in (4, 9):                                # boards
        p.rect(1, y, 26, y, w3)
    p.dot(9, 2, w1); p.dot(19, 6, w1); p.dot(5, 11, w1)     # grain
    p.rect(17, 11, 18, 12, w4)                      # a dark ring (a cup was here)
    p.rect(0, 15, 27, 16, w3)                       # front edge
    p.rect(1, 16, 26, 16, w4)
    for lx in (1, 24):                              # legs, 3 px so the outline leaves a lit middle
        p.rect(lx, 17, lx + 2, 29, w3)
    p.outline()
    return p.img


PIECES = {"fridge": fridge, "stove": stove, "bed": bed, "table": table}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, make in PIECES.items():
        make().save(OUT / f"{name}.png")
        print("saved", name)
