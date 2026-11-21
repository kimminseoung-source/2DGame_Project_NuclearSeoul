"""The 6-picture roll in 8 directions in the game: each picture comes from Roll_Spin (never the old sheet
or a glide), drawn at the middle of its timed share; a sheet of all 48."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, dodge_fx, stamina, character_look
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
look = g.hero.look
print("style", dodge_fx.style)
shares = look.keys["timing"]["roll_spin"]; tot = sum(shares)
mids = [(sum(shares[:i]) + shares[i] / 2) / tot for i in range(6)]
k = g.zoom * settings.DOT
used = {}
rows = []
DIRS = ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"]
for n, d in enumerate(DIRS):
    a = n * pi / 4
    h = g.hero; h.x, h.y = 520, 260; h.roll = 0; h.roll_cooldown = 0; h.stamina.value = stamina.MAX
    h.trail = dodge_fx.Trail(); g.effects.clear()
    g.update(1 / 60, keys)
    h.start_roll(round(cos(a), 3), round(sin(a), 3))
    shots, t = [], 0.0
    for m in mids:
        while 1 - h.roll / settings.ROLL_TIME < m:
            g.update(1 / 120, keys)
        pic = look.picture(dodge_fx.roll_pose(), 1 - h.roll / settings.ROLL_TIME, h.roll_angle())
        used.setdefault(d, []).append((pic[2], pic[4]) if pic else None)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
        shots.append(im.crop((int(hx) - 70, int(hy) - 120, int(hx) + 70, int(hy) + 25)))
    rows.append((d, shots))
for d in DIRS:
    print(d, used[d])
ok = all(u and u[0] == "roll_spin" for d in DIRS for u in used[d]) and all([u[1] for u in used[d]] == list(range(6)) for d in DIRS)
print("all from Roll_Spin, pictures 0..5 in order:", ok)
f = ImageFont.truetype("malgun.ttf", 16)
cw, ch = rows[0][1][0].size
sheet = Image.new("RGB", (100 + cw * 6, ch * 8), (30, 30, 34)); dr = ImageDraw.Draw(sheet)
for r, (d, shots) in enumerate(rows):
    dr.text((6, r * ch + ch // 2), d, font=f, fill=(240, 230, 200))
    for c, s in enumerate(shots):
        sheet.paste(s, (100 + c * cw, r * ch))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/roll_8dirs_game.png"); print("ok")
