"""Sneaking in 8 directions in the game (Sneaking Forward): 3 walking moments + standing still, the
pictures come from Sneak/ and Sneak_Idle/ (never the old sheet)."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui
from PIL import Image, ImageDraw, ImageFont
from pico2d import pico2d as canvas
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(2)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.zombies[:] = []
for _ in range(5): g.update(1 / 60, keys)
k = g.zoom * settings.DOT; h = g.hero
SC = sdl2
DIRS = [("east", [SC.SDL_SCANCODE_D]), ("north-east", [SC.SDL_SCANCODE_D, SC.SDL_SCANCODE_W]), ("north", [SC.SDL_SCANCODE_W]),
        ("north-west", [SC.SDL_SCANCODE_A, SC.SDL_SCANCODE_W]), ("west", [SC.SDL_SCANCODE_A]),
        ("south-west", [SC.SDL_SCANCODE_A, SC.SDL_SCANCODE_S]), ("south", [SC.SDL_SCANCODE_S]),
        ("south-east", [SC.SDL_SCANCODE_D, SC.SDL_SCANCODE_S])]
rows, report = [], []
def step(a):
    """One update with the mouse 200 px off toward angle a (the hero looks at the mouse)."""
    wx, wy = h.x + cos(a) * 200, h.y + sin(a) * 200
    g.aim = ((wx - g.cam[0]) * settings.SCALE, H - 1 - (wy - g.cam[1]) * settings.SCALE)
    g.update(1 / 60, keys)
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
    return im.crop((int(hx) - 60, int(hy) - 110, int(hx) + 60, int(hy) + 22))
orig = h.look.picture
seen = []
def spy(pose, time, angle, contact=None):
    r = orig(pose, time, angle, contact)
    seen.append(r[2] if r else None)
    return r
h.look.picture = spy
for n_dir, (d, ks) in enumerate(DIRS):
    a = n_dir * pi / 4
    h.x, h.y = 520, 260
    keys[SC.SDL_SCANCODE_LCTRL] = 1
    for c in ks: keys[c] = 1
    shots = []
    for n in range(3):
        for _ in range(8): step(a)
        seen.clear(); shots.append(shot()); walk_used = list(seen)
    for c in ks: keys[c] = 0
    for _ in range(4): step(a)
    seen.clear(); shots.append(shot()); still_used = list(seen)
    keys[SC.SDL_SCANCODE_LCTRL] = 0
    rows.append((d, shots)); report.append((d, walk_used, still_used))
for r in report: print(r)
f = ImageFont.truetype("malgun.ttf", 15)
cw, ch = rows[0][1][0].size
sheet = Image.new("RGB", (100 + cw * 4, ch * 8), (30, 30, 34)); dr = ImageDraw.Draw(sheet)
for r, (d, shots) in enumerate(rows):
    dr.text((6, r * ch + ch // 2), d, font=f, fill=(240, 230, 200))
    for c, s in enumerate(shots): sheet.paste(s, (100 + c * cw, r * ch))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/sneak_8dirs_game.png"); print("ok")
