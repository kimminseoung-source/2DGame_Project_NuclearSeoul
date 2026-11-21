"""The empty test arena: chop in all 8 directions at standing infected; strip of the hit moment."""
import sys, os, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi, degrees
import pico2d, sdl2, play, settings, ui, weapons, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
print("arena", area.TEST_ARENA, "blocks", len(area.BLOCKS))
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(1)
g = play.Game()
print("people", len(g.people), "no_spawn", g.dev.no_spawn, "freeze", g.dev.freeze, "infected", sum(z.alive for z in g.zombies))
g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
for _ in range(5): g.update(1 / 60, keys)
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
rows = []
first = None
for i in range(8):
    a = i * pi / 4
    tx, ty = g.hero.x + cos(a) * 50, g.hero.y + sin(a) * 50
    for _ in range(4):
        x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200); g.update(1 / 60, keys)
    g.hero.slash_cooldown = 0; g.hero.stamina.value = 999; g.hero.start_slash(tx, ty)
    shots = []
    for n in range(40):
        x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200); g.update(1 / 60, keys)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        if n in (6, 18, 26):
            cx, cy = hp(); shots.append(im.crop((int(cx) - 110, int(cy) - 150, int(cx) + 110, int(cy) + 50)))
        if first is None and n == 0: first = im
    rows.append((f"{degrees(a):.0f}°", shots))
    for _ in range(30): g.update(1 / 60, keys)
sheet = Image.new("RGB", (8 * 220, 3 * 200 + 24), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for c, (lab, shots) in enumerate(rows):
    d.text((c * 220 + 6, 4), lab, font=f, fill=(196, 170, 92))
    for r, im in enumerate(shots): sheet.paste(im, (c * 220, 24 + r * 200))
sheet.save("docs/planning/arena_8dirs.png"); first.save("docs/planning/arena_view.png")
pico2d.close_canvas(); print("ok")
