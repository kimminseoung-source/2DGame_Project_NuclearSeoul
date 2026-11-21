"""Carried weapon: hang vs ready, 8 standing directions + east walk / pickup / sneak, in the game."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, character_look, hero as hero_mod
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
k = g.zoom * settings.DOT
h = g.hero
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
    return im.crop((int(hx) - 55, int(hy) - 115, int(hx) + 55, int(hy) + 20))
DIRS = ["east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east"]
rows = []
for carry in ("hang", "ready"):
    character_look.DirLook.CARRY = carry
    shots = []
    for n, d in enumerate(DIRS):
        h.x, h.y = 520, 260; h.pickup = 0
        h.angle = n * pi / 4; h.facing = 1 if n in (0, 1, 7) else -1
        for _ in range(2): g.update(1 / 60, keys)
        h.angle = n * pi / 4
        shots.append((d, shot()))
    h.x, h.y = 520, 260
    keys[sdl2.SDL_SCANCODE_D] = 1
    for _ in range(9): g.update(1 / 60, keys)
    shots.append(("걷기 동쪽", shot()))
    keys[sdl2.SDL_SCANCODE_LCTRL] = 1
    for _ in range(9): g.update(1 / 60, keys)
    shots.append(("살금 동쪽", shot()))
    keys[sdl2.SDL_SCANCODE_LCTRL] = 0; keys[sdl2.SDL_SCANCODE_D] = 0
    for _ in range(3): g.update(1 / 60, keys)
    h.angle = 0.0; h.facing = 1
    h.pickup = hero_mod.PICKUP_TIME * 0.4
    g.update(1 / 60, keys)
    shots.append(("줍기 동쪽", shot()))
    h.pickup = 0
    rows.append((carry, shots))
    print(carry, [round(character_look.DirLook.hang(h.look, d) * 180 / pi) for d in DIRS])
f = ImageFont.truetype("malgun.ttf", 14); fb = ImageFont.truetype("malgun.ttf", 18)
cw, ch = rows[0][1][0][1].size
sheet = Image.new("RGB", (130 + cw * 11, (ch + 20) * 2), (30, 30, 34)); dr = ImageDraw.Draw(sheet)
names = {"hang": "지금\n(아래로)", "ready": "새로\n(앞 위로)"}
for r, (carry, shots) in enumerate(rows):
    y = r * (ch + 20)
    dr.text((8, y + ch // 2 - 10), names[carry], font=fb, fill=(240, 230, 200))
    for c, (lab, im) in enumerate(shots):
        sheet.paste(im, (130 + c * cw, y + 20)); dr.text((130 + c * cw + 3, y + 2), lab, font=f, fill=(180, 180, 190))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/carry_compare.png"); print("ok")
