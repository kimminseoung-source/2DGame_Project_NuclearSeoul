"""8-direction PixelLab hero in the game: aim at 8 directions, day and night, beside an infected; old look too."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi, degrees
import pico2d, sdl2, play, settings, ui, character_look
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(g):
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
def hero_px(g):
    k = g.zoom * settings.DOT
    return (g.hero.x - g.cam[0]) * k, settings.HEIGHT - 1 - (g.hero.y - g.cam[1]) * k
def crop(im, g):
    x, y = hero_px(g); return im.crop((int(x) - 110, int(y) - 140, int(x) + 110, int(y) + 50))
def game(hour):
    random.seed(1)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.daylight.hour = hour
    z = g.zombies[0]; z.x, z.y = g.hero.x + 45, g.hero.y + 2
    for other in g.zombies[1:]: other.x, other.y = -5000, -5000
    return g
print("look type", type(game(14).hero_look).__name__)
rows = []
for hour, label in ((14.0, "낮"), (22.0, "밤")):
    g = game(hour); cells = []
    for i in range(8):
        a = i * pi / 4
        for _ in range(3):
            hx, hy = hero_px(g); g.aim = (hx + 220 * cos(a), hy - 220 * sin(a)); g.update(1 / 60, keys)
        im = shot(g)
        cells.append((f"{degrees(g.look):.0f}°", crop(im, g)))
    rows.append((label, cells))
character_look.DirLook.on = False
g = game(14.0)
for _ in range(3):
    hx, hy = hero_px(g); g.aim = (hx, hy + 220); g.update(1 / 60, keys)
old = crop(shot(g), g)
character_look.DirLook.on = True
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 16)
W, H = 220, 190
sheet = Image.new("RGB", (8 * W, 3 * (H + 24)), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for r, (label, cells) in enumerate(rows):
    for c, (t, im) in enumerate(cells):
        sheet.paste(im, (c * W, r * (H + 24) + 24)); d.text((c * W + 6, r * (H + 24) + 4), f"{label} {t}", font=f, fill=(196, 170, 92))
sheet.paste(old, (0, 2 * (H + 24) + 24)); d.text((6, 2 * (H + 24) + 4), "예전 그림", font=f, fill=(196, 170, 92))
sheet.save("docs/planning/hero_dirlook_ingame.png")
pico2d.close_canvas(); print("ok")
