"""Cut-out animation test: cut the concept into parts and pose them like a paper doll.

    .venv\\Scripts\\python.exe tools/sprites/cutout_demo.py assets/characters/concepts/hero_concept_a.webp <out.png>

Parts (in the cleaned concept's pixels): head, torso (jacket, arms and backpack together,
because the concept draws the arms into the jacket), back leg, front leg and the bat
(picked by its wood colour). Holes the bat leaves in the trousers are filled from the
neighbouring trouser pixels. Each pose rotates parts around their joints, then the frame
is shrunk to game size with an outline (clean_concept.py). This is a comparison demo, not
the final pipeline.
"""

import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import clean_concept as cc  # noqa: E402

HIP_Y = 264
NECK = (100, 92)
HIPS = {"back": (74, 268), "front": (128, 268)}
GRIP = (62, 272)                     # where the hands would hold the bat


BAT_A, BAT_B = (12, 252), (210, 357)  # handle end and barrel end in the concept


def on_bat(x, y):
    """Inside the bat's band (handle thin, barrel thick), outline included."""
    ax, ay = BAT_A
    bx, by = BAT_B
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy)))
    px, py = ax + t * vx, ay + t * vy
    return math.hypot(x - px, y - py) <= 9 + 7 * t


def split(fig):
    w, h = fig.size
    src = fig.load()
    parts = {name: Image.new("RGBA", (w, h)) for name in ("head", "torso", "back", "front", "bat")}
    px = {k: v.load() for k, v in parts.items()}
    for y in range(h):
        for x in range(w):
            c = src[x, y]
            if not c[3]:
                continue
            if y > 240 and on_bat(x, y):
                px["bat"][x, y] = c
            elif y < NECK[1] and x > 50 and not (c[0] > 150 and c[1] > 110 and c[2] < 90):
                px["head"][x, y] = c                    # skip the yellow hood: it stays on the torso
            elif y >= HIP_Y:
                px["back" if x < 102 + (y - HIP_Y) * 0.04 else "front"][x, y] = c
            else:
                px["torso"][x, y] = c
    # Fill the trouser holes left by the bat with the nearest trouser pixel on the same row.
    for leg in ("back", "front"):
        lp = px[leg]
        for y in range(HIP_Y, h):
            row = [x for x in range(w) if lp[x, y][3]]
            if not row:
                continue
            for x in range(min(row), max(row) + 1):
                if not lp[x, y][3] and px["bat"][x, y][3]:
                    left = next((lp[i, y] for i in range(x, min(row) - 1, -1) if lp[i, y][3]), None)
                    lp[x, y] = left or lp[max(row), y]
    return parts


def place(canvas, part, pivot, angle, dest):
    """Rotate part around pivot (screen degrees, + = counter-clockwise) and put pivot at dest."""
    big = Image.new("RGBA", (part.width * 3, part.height * 3))
    big.paste(part, (part.width, part.height))
    p = (pivot[0] + part.width, pivot[1] + part.height)
    rotated = big.rotate(angle, resample=Image.NEAREST, center=p)
    canvas.alpha_composite(rotated, (round(dest[0] - p[0]), round(dest[1] - p[1])))


def pose(parts, size, legs=(0, 0), bob=0, lean=0, head=0, bat=None):
    """bat = (angle, grip position) or None to keep it where the concept has it."""
    w, h = size
    canvas = Image.new("RGBA", (w + 200, h + 120))
    ox, oy = 100, 100
    for leg, angle in (("back", legs[0]),):
        place(canvas, parts[leg], HIPS[leg], angle, (HIPS[leg][0] + ox, HIPS[leg][1] + oy + bob))
    place(canvas, parts["torso"], (100, HIP_Y), lean, (100 + ox, HIP_Y + oy + bob))
    neck = rotate_point(NECK, (100, HIP_Y), lean)
    place(canvas, parts["head"], NECK, lean + head, (neck[0] + ox, neck[1] + oy + bob))
    place(canvas, parts["front"], HIPS["front"], legs[1], (HIPS["front"][0] + ox, HIPS["front"][1] + oy + bob))
    if bat is None:
        place(canvas, parts["bat"], GRIP, 0, (GRIP[0] + ox, GRIP[1] + oy + bob))
    else:
        angle, grip = bat
        place(canvas, parts["bat"], GRIP, angle, (grip[0] + ox, grip[1] + oy + bob))
    return canvas


def rotate_point(p, c, angle):
    a = math.radians(-angle)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


def game_size(frame, height=56):
    bbox = frame.getbbox()
    fig = frame.crop(bbox)
    return fig, bbox


POSES = {
    "서 있기": dict(),
    "걷기 1": dict(legs=(-16, 16), bob=-4),
    "걷기 2": dict(legs=(16, -16), bob=-4),
    # + lean tips the body back (it faces right); the bat starts pointing down-forward.
    "준비": dict(lean=6, bat=(148, (95, 150))),
    "맞는 순간": dict(lean=-10, legs=(-10, 12), bat=(22, (150, 185))),
}


def main():
    src, out = sys.argv[1], sys.argv[2]
    img = Image.open(src).convert("RGBA")
    fig = cc.largest_component(cc.key_out(img, [255, 0, 255], 150))
    parts = split(fig)
    frames = {name: pose(parts, fig.size, **kw) for name, kw in POSES.items()}
    # One common scale: the standing pose is 56 px tall in the game.
    stand = frames["서 있기"].crop(frames["서 있기"].getbbox())
    scale = 54 / stand.height
    results = []
    floor = None
    for name, frame in frames.items():
        bbox = frame.getbbox()
        crop = frame.crop(bbox)
        small = crop.resize((max(1, round(crop.width * scale)), max(1, round(crop.height * scale))), Image.NEAREST)
        small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        pad = Image.new("RGBA", (small.width + 2, small.height + 2))
        pad.paste(small, (1, 1), small)
        results.append((name, cc.outline(pad), bbox))
    # Sheet of 96x64 cells, feet on the floor line, horizontally aligned on the hips.
    sheet = Image.new("RGBA", (96 * len(results), 64))
    for i, (name, sprite, bbox) in enumerate(results):
        hip_x = (100 + 100 - bbox[0]) * scale
        sheet.alpha_composite(sprite, (i * 96 + round(40 - hip_x + 1), 64 - 4 - sprite.height))
    sheet.save(out)
    print("saved", out, [n for n, _, _ in results])


if __name__ == "__main__":
    main()
