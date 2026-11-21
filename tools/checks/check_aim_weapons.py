"""Aiming and standing with every weapon (south-east, south, north-east), and a knife aimed while
stepping (must not show the old side sheet). BUSAN_HERO picks the hero folder."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, weapons
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
g = play.Game(); g.dev.freeze = True
look = g.hero_look
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
def aim_at(a):
    x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200)
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    cx, cy = hp(); return im.crop((int(cx) - 70, int(cy) - 110, int(cx) + 70, int(cy) + 30))
for _ in range(5): g.update(1 / 60, keys)
rows, log = [], []
for wk, w in weapons.WEAPONS.items():
    g.hero.weapon = w
    shots = []
    for a in (-pi / 4, -pi / 2, pi / 4):
        g.hero.start_ready()
        for _ in range(4): aim_at(a); g.update(1 / 60, keys); g.hero.ready = 1.0
        shots.append(shot())
    stand = look.has(f"ready_stand_{w['style']}")
    log.append(f"{w['name']}({w['style']}): own aim picture {stand}")
    g.hero.ready = None
    for _ in range(3): g.update(1 / 60, keys)
    rows.append((f"{w['name']}", shots))
# knife aimed while stepping right
g.hero.weapon = weapons.WEAPONS["knife"]
keys[sdl2.SDL_SCANCODE_D] = 1
g.hero.start_ready(); shots = []
for n in range(24):
    aim_at(-pi / 4); g.update(1 / 60, keys); g.hero.ready = 1.0
    if n % 6 == 0: shots.append(shot())
keys[sdl2.SDL_SCANCODE_D] = 0
log.append(f"knife stepping: has ready_stab {look.has('ready_stab')}, moving {g.hero.moving}")
rows.append(("식칼 조준 걷기", shots))
print("\n".join(log))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
cols = max(len(s) for _, s in rows)
sheet = Image.new("RGB", (110 + cols * 140, len(rows) * 140), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for r, (lab, shots) in enumerate(rows):
    d.text((6, r * 140 + 60), lab, font=f, fill=(220, 200, 140))
    for c, im in enumerate(shots): sheet.paste(im, (110 + c * 140, r * 140))
sheet.save("docs/planning/aim_stand_weapons.png")
pico2d.close_canvas(); print("ok")
