"""Make assets/ui/vision_mask.png: a white mask, clear in the middle and opaque outside.

    .venv\\Scripts\\python.exe tools/sprites/make_vision_mask.py

The game (src/vision.py) scales it so the clear circle has the radius it wants around the
hero, tints it (black, green, red) and fades it, so one image serves every exposure stage.
The clear core is CLEAR px wide, then the edge eases out to opaque at FULL px.
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SIZE = 1024
CLEAR = 48           # radius that stays fully clear (small, so the scaled mask always covers
FULL = 120           # the whole screen and no seam shows); fully opaque from FULL


def main():
    img = Image.new("RGBA", (SIZE, SIZE))
    px = img.load()
    c = SIZE / 2
    for y in range(SIZE):
        for x in range(SIZE):
            r = ((x + 0.5 - c) ** 2 + (y + 0.5 - c) ** 2) ** 0.5
            t = min(1.0, max(0.0, (r - CLEAR) / (FULL - CLEAR)))
            t = t * t * (3 - 2 * t)                    # smoothstep: a soft edge, no ring
            px[x, y] = (255, 255, 255, round(255 * t))
    out = ROOT / "assets" / "ui" / "vision_mask.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("saved", out)


if __name__ == "__main__":
    main()
