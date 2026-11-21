"""Shots: key marks at the start; after the first moves; a '?' over infected that heard a blow."""
import sys, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, infected, weapons
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def grab(g, around):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp"); im = Image.open("docs/planning/_t.bmp").convert("RGB")
    k = g.zoom * settings.DOT
    x, y = (around[0] - g.cam[0]) * k, settings.HEIGHT - (around[1] - g.cam[1]) * k
    return im.crop((int(x - 300), int(y - 240), int(x + 300), int(y + 120)))


shots = []
random.seed(2); g = play.Game(); g.to_spawn = 0; g.zombies[:] = []
for _ in range(30): g.update(1 / 60, keys)
shots.append(("시작: 키 표시 2개", grab(g, (g.hero.x, g.hero.y))))
g.used |= {"move", "attack"}
it = min(g.supplies, key=lambda s: (s.x - g.hero.x) ** 2 + (s.y - g.hero.y) ** 2)
g.hero.x, g.hero.y = it.x + 6, it.y + 4
for _ in range(5): g.update(1 / 60, keys)
shots.append(("걷고 때려 본 뒤 + 물건 옆: [E]", grab(g, (g.hero.x, g.hero.y))))
g.used |= {"roll", "charge", "sneak", "pick"}
h = g.hero
zs = [infected.Zombie(g.zombie_look, h.x + dx, h.y + dy) for dx, dy in ((70, 10), (-110, 40))]
for z in zs:
    z.prone = False
g.zombies[:] = zs
for z, dx in zip(zs, (70, -110)):
    z.x, z.y, z.state, z.heading, z.turn_in = h.x + dx, z.y, "idle", 0 if dx > 0 else pi, 99
g.make_noise(infected.NOISE_SLASH)
for _ in range(8): g.update(1 / 60, keys)
shots.append(("휘두른 소리를 들은 놈: 고개 돌림 + ?", grab(g, (h.x, h.y))))
import os; os.remove("docs/planning/_t.bmp")
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 20)
W, H = shots[0][1].size
sheet = Image.new("RGB", (W * 3, H + 36), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t, im) in enumerate(shots):
    sheet.paste(im, (i * W, 36)); d.text((i * W + 8, 8), t, font=font, fill=(196, 170, 92))
sheet.save("docs/planning/teach_marks_ingame.png"); print(sheet.size)
