"""Hand-held weapon sprites for the 2D clothes painter, drawn pixel by pixel (or taken from art).

Every weapon is a small RGBA image lying along +x with the grip at the left end
(x = 2, middle row): paint_clothes.py puts that point in the near hand and turns the image
to the action's angle. Add a weapon by adding a function to WEAPONS.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]

OUTLINE = (16, 18, 26, 255)


def machete():
    """A survivor's machete, about 20 px: dark wrapped grip, small guard, long steel blade
    with a darker spine on top, a lighter edge below and a clipped tip."""
    w, h = 21, 5
    img = Image.new("RGBA", (w, h))
    px = img.load()
    grip = (46, 34, 28, 255)
    grip_wrap = (70, 52, 40, 255)
    guard = (60, 60, 64, 255)
    spine = (96, 102, 110, 255)
    steel = (168, 174, 182, 255)
    edge = (214, 218, 222, 255)
    for x in range(0, 6):                         # grip, wrapped every other pixel
        for y in (2, 3):
            px[x, y] = grip_wrap if x % 2 else grip
    for y in range(1, 5):                         # guard
        px[6, y] = guard
    for x in range(7, w):                         # blade: spine, body, edge
        tip = x >= w - 3
        px[x, 1] = spine if not tip or x < w - 1 else (0, 0, 0, 0)
        px[x, 2] = steel
        px[x, 3] = edge if x < w - 1 else (0, 0, 0, 0)
        if x >= w - 2:                            # clipped point: the edge rises to the spine
            px[x, 3] = (0, 0, 0, 0)
    return img


def concept_bat(length=22):
    """The concept art's baseball bat (parts sheet), shrunk to game size."""
    import clean_concept as cc
    sheet = cc.key_out(Image.open(ROOT / "assets/characters/concepts/hero_parts_a.webp").convert("RGBA"),
                       [255, 0, 255], 150)
    bat = sheet.crop((752, 383, 968, 411))
    bat = bat.resize((length, max(2, round(bat.height * length / bat.width) + 1)), Image.NEAREST)
    bat.putalpha(bat.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    return bat


def machete_dot():
    """The machete for the 32 px dot look (2026-11-16 "도트 형식으로"), 13 px, drawn for its size
    rather than shrunk: 3 px wrapped grip, 1 px guard, a 2-row blade (steel over a light edge) whose
    point rises to the spine."""
    w, h = 13, 4
    img = Image.new("RGBA", (w, h))
    px = img.load()
    grip, wrap = (46, 34, 28, 255), (70, 52, 40, 255)
    guard, steel, edge = (60, 60, 64, 255), (150, 156, 164, 255), (214, 218, 222, 255)
    for x in range(0, 3):
        px[x, 2] = wrap if x % 2 else grip
    px[3, 1] = px[3, 2] = px[3, 3] = guard
    for x in range(4, w):
        px[x, 1] = steel
        if x < w - 1:
            px[x, 2] = edge
    return img


WEAPONS = {"machete": machete, "bat": concept_bat}
# Weapons drawn for the small dot look; others are shrunk from the full-size drawing.
DOT_WEAPONS = {"machete": machete_dot}


def get(name, person_px=54):
    """The weapon sprite for a person `person_px` tall (54: the original look, 32: the dot look)."""
    if person_px < 54:
        if name in DOT_WEAPONS:
            return DOT_WEAPONS[name]()
        big = WEAPONS[name]()
        k = person_px / 54
        return big.resize((max(3, round(big.width * k)), max(2, round(big.height * k))), Image.NEAREST)
    return WEAPONS[name]()
