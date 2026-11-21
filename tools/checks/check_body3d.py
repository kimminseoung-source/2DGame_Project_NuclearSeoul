"""3D hero body motions in the game, 8 directions: hurt, down, pickup, sneak, sneak still.
Also which look draws each (must be the new pictures, not the old side sheets).
Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena through run_hidden.py."""
import sys, ctypes, random; sys.path.insert(0, "src")
from pathlib import Path
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, weapons, character_look, hero as hr
from settings import HURT_REACT
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(1)
g = play.Game(); g.dev.freeze = True; g.zombies.clear()
h = g.hero; look = g.hero_look
h.weapon = weapons.WEAPONS["pipe"]
for _ in range(5): g.update(1 / 60, keys)
k = g.zoom * settings.DOT
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    cx, cy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
    return im.crop((int(cx) - 60, int(cy) - 100, int(cx) + 60, int(cy) + 25))
# which drawing each pose gets (DirLook picture -> new; None -> the old side sheet)
used = {}
for pose, t in (("hurt", 0.5), ("down", 0.9), ("pickup", 0.5), ("sneak", 0.2), ("sneak_idle", 0.0)):
    used[pose] = [bool(look.picture(pose, t, i * pi / 4)) for i in range(8)]
print("new pictures per pose (8 dirs):", {p: sum(v) for p, v in used.items()})
STATES = [
    ("맞기", lambda: setattr(h, "reeling", HURT_REACT * 0.5)),
    ("쓰러짐", lambda: setattr(h, "dead", 0.5)),
    ("줍기", lambda: setattr(h, "pickup", hr.PICKUP_TIME * 0.5)),
    ("살금살금 걷기", lambda: (setattr(h, "sneaking", True), setattr(h, "moving", True))),
    ("살금살금 서기", lambda: (setattr(h, "sneaking", True), setattr(h, "moving", False))),
]
def clear():
    h.reeling = 0; h.dead = 0; h.pickup = 0; h.sneaking = False; h.moving = False
rows = []
DIRN = ("south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west")
def sprite(folder, d, i):                      # the picture itself, at the game's size, on the ground colour
    im = Image.open(f"assets/characters/hero_3d/{folder}/{d}/{i}.png").convert("RGBA")
    bg = Image.new("RGBA", im.size, (58, 60, 62, 255)); bg.alpha_composite(im)
    big = bg.resize((im.width * g.zoom, im.height * g.zoom), Image.NEAREST)
    return big.crop((big.width // 2 - 60, big.height - 125 - 6 * g.zoom, big.width // 2 + 60, big.height - 6 * g.zoom)).convert("RGB")
for name, put in STATES:
    shots = []
    if name == "쓰러짐":                       # the game-over panel covers the game: show the pictures
        n = len(list(Path("assets/characters/hero_3d/Down/south").glob("*.png")))
        rows.append(("쓰러짐 (남, 차례로)", [sprite("Down", "south", i) for i in range(n)]))
        rows.append(("쓰러짐 마지막 8방향", [sprite("Down", d, n - 1) for d in DIRN]))
        continue
    for i in range(8):
        a = -pi / 2 + i * pi / 4
        h.angle = a; h.facing = 1 if cos(a) >= 0 else -1
        clear(); put()
        shots.append(shot())
    clear()
    rows.append((name, shots))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
sheet = Image.new("RGB", (110 + 8 * 120, len(rows) * 125 + 22), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for c, n in enumerate(("남", "남동", "동", "북동", "북", "북서", "서", "남서")):
    d.text((110 + c * 120 + 50, 2), n, font=f, fill=(200, 200, 200))
for r, (lab, shots) in enumerate(rows):
    d.text((6, 22 + r * 125 + 55), lab, font=f, fill=(220, 200, 140))
    for c, im in enumerate(shots): sheet.paste(im, (110 + c * 120, 22 + r * 125))
sheet.save("docs/planning/hero3d_body_motions.png")
pico2d.close_canvas(); print("ok")
