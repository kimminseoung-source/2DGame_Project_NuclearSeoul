"""Stamina off, roll charges (2026-11-21): Space three times -> two rolls, one more after
ROLL_RECHARGE; slashing again and again stays the same speed; the dots under the feet (full: hidden,
used, coming back, empty flash) - a picture of them."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, stamina
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
h = g.hero; k = g.zoom * settings.DOT
print("STAMINA_ON", settings.STAMINA_ON, "charges", stamina.ROLL_CHARGES, "recharge", stamina.ROLL_RECHARGE)
def shot(label):
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
    return label, im.crop((int(hx) - 50, int(hy) - 100, int(hx) + 50, int(hy) + 30))
shots = [shot("가득 (안 보임)")]
rolled, red = 0, False                                   # Space every frame for 1 s
for f in range(60):
    if h.roll <= 0 and h.roll_cooldown <= 0:
        if h.start_roll(1, 0):
            rolled += 1
            if rolled == 1:
                g.update(1 / 60, keys); shots.append(shot("1번 씀"))
        elif not red:
            red = True; g.update(1 / 60, keys); shots.append(shot("없을 때 Space (빨강)"))
    g.update(1 / 60, keys)
print("Space every frame for 1 s ->", rolled, "rolls (2 stored), left", h.rolls.left)
while h.roll > 0 or h.roll_cooldown > 0: g.update(1 / 60, keys)
h.rolls.left, h.rolls.timer = 0, 0.0                     # none left now
red = h.start_roll(1, 0)
g.update(1 / 60, keys); shots.append(shot("없을 때 Space (빨강)"))
print("Space with none left rolls:", red)
t = 0.0
while h.rolls.left < 1:
    g.update(1 / 60, keys); t += 1 / 60
    if 0.5 < h.rolls.coming < 0.56 and len(shots) < 4: shots.append(shot("차오르는 중"))
shots.append(shot("1개 돌아옴 (반짝)"))
print(f"one came back {t:.2f}s later, can roll: {h.start_roll(1, 0)}")
times = []
for n in range(6):                                       # slashes back to back
    while h.slash or h.slash_cooldown > 0 or h.roll > 0:
        g.update(1 / 60, keys)
    h.start_slash(h.x + 60, h.y + settings.CHEST)
    times.append(round(h.slash["whole"], 3))
print("slash lengths, back to back:", times, "stamina", round(h.stamina.value))
f = ImageFont.truetype("malgun.ttf", 14)
cw, ch = shots[0][1].size
sheet = Image.new("RGB", (cw * len(shots), ch + 20), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for i, (lab, im) in enumerate(shots):
    big = im
    sheet.paste(big, (i * cw, 20)); d.text((i * cw + 3, 2), lab, font=f, fill=(230, 220, 190))
sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/roll_dots.png"); print("ok")
