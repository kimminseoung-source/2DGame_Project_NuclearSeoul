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


WEAPONS = {"machete": machete, "bat": concept_bat}


def get(name):
    return WEAPONS[name]()
