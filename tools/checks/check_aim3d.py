"""3D hero aiming: stand with the bat raised (8 directions), step with it raised, let go = bat swing.
Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena through run_hidden.py from the project root."""
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
g = play.Game()
g.dev.freeze = True
g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
look = g.hero_look
print("has ready_stand", look.has("ready_stand"), "has ready_chop", look.has("ready_" + g.hero.weapon["style"]),
      "default attack", look.keys.get("default_variant"))
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
def aim_at(a):
    x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200)
def shot(w=90, top=120, bottom=40):
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    cx, cy = hp(); return im.crop((int(cx) - w, int(cy) - top, int(cx) + w, int(cy) + bottom))
for _ in range(5): g.update(1 / 60, keys)
rows = []
# 1. aiming, standing, 8 directions
stand = []
for i in range(8):
    a = -pi / 2 + i * pi / 4
    g.hero.start_ready(); g.hero.ready = 1.0
    for _ in range(3): aim_at(a); g.update(1 / 60, keys); g.hero.ready = 1.0
    p = look.picture("ready_stand", g.hero.time, g.hero.angle)
    stand.append(shot())
print("stand key", p[2] if p else None)
rows.append(("조준 서 있기 8방향", stand))
# 2. aiming while walking to the right (aim south-east)
walk = []
keys[sdl2.SDL_SCANCODE_D] = 1
g.hero.start_ready()
for n in range(36):
    aim_at(-pi / 4); g.update(1 / 60, keys); g.hero.ready = 1.0
    if n % 4 == 0: walk.append(shot())
keys[sdl2.SDL_SCANCODE_D] = 0
p = look.picture("ready_" + g.hero.weapon["style"], g.hero.time, g.hero.angle)
print("moving", g.hero.moving, "step key", p[2] if p else None, "frame", p[4] if p else None)
rows.append(("조준한 채 걷기 (오른쪽, 남동 조준)", walk))
# 3. let go: the bat swing
swing = []
for _ in range(10): g.update(1 / 60, keys)
g.hero.slash_cooldown = 0; g.hero.stamina.value = 999
g.hero.start_slash(g.hero.x + 50, g.hero.y - 50)
for n in range(50):
    aim_at(-pi / 4); g.update(1 / 60, keys)
    if n % 5 == 0: swing.append(shot())
rows.append(("놓아서 휘두르기 (기본 = 방망이)", swing))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
cols = max(len(s) for _, s in rows)
sheet = Image.new("RGB", (cols * 180, len(rows) * 186), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for r, (lab, shots) in enumerate(rows):
    d.text((6, r * 186 + 2), lab, font=f, fill=(220, 200, 140))
    for c, im in enumerate(shots): sheet.paste(im, (c * 180, r * 186 + 22))
sheet.save("docs/planning/hero3d_aim_game.png")
pico2d.close_canvas(); print("ok")
