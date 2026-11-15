"""Crop the empty margins of the rendered wreck pictures (assets/area/wreck_*.png) so the game can
place each one by its bottom edge over the block it stands for."""
from pathlib import Path

from PIL import Image

AREA = Path(__file__).resolve().parents[2] / "assets" / "area"
for path in sorted(AREA.glob("wreck_*.png")):
    im = Image.open(path).convert("RGBA")
    box = im.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    if box:
        im.crop(box).save(path)
        print(path.name, im.size, "->", (box[2] - box[0], box[3] - box[1]))
