"""Mock-up: the noise of a blow shown as a ring; infected inside it get a "?" (2026-11-16 proposal)."""
import sys, random; sys.path.insert(0, "src")
from math import pi, cos, sin
import pico2d, sdl2, play, settings, ui, infected, weapons
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 22)
big = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 34)
spots = [(58, 4), (-150, 70), (230, -60)]
panels = []
for wkey in ("knife", "axe"):
    random.seed(3); g = play.Game(); g.to_spawn = 0
    h = g.hero; h.x, h.y = 520, 320; h.weapon = weapons.WEAPONS[wkey]
    zs = [infected.Zombie(g.zombie_look, h.x + dx, h.y + dy) for dx, dy in spots]
    for z in zs: z.prone = False
    g.zombies[:] = zs
    for _ in range(90): g.update(1 / 60, keys)
    for z, (dx, dy) in zip(zs, spots):
        z.x, z.y, z.state, z.heading, z.turn_in = h.x + dx, h.y + dy, "idle", 0 if dx > 0 else pi, 99
    h.facing = 1
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp"); im = Image.open("docs/planning/_t.bmp").convert("RGB")
    k = g.zoom * settings.DOT
    def scr(wx, wy): return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
    d = ImageDraw.Draw(im, "RGBA")
    radius = h.weapon["noise"]
    hx, hy = scr(h.x, h.y + 20)
    n = int(2 * pi * radius * k / 14)
    for i in range(n):                                   # the ring, dotted, pixel squares
        a = 2 * pi * i / n
        x, y = hx + cos(a) * radius * k, hy + sin(a) * radius * k * 0.75
        d.rectangle((x - 3, y - 3, x + 3, y + 3), fill=(236, 220, 170, 210))
    for z in zs:
        if (z.x - h.x) ** 2 + ((z.y - h.y) / 0.75) ** 2 <= radius ** 2:
            zx, zy = scr(z.x, z.y + 66)
            d.text((zx - 9, zy - 34), "?", font=big, fill=(240, 200, 80))
    cx = settings.WIDTH // 2
    panels.append((h.weapon, im))
import os; os.remove("docs/planning/_t.bmp")
W, H = panels[0][1].size
sheet = Image.new("RGB", (W, H * 2 + 80), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (w, im) in enumerate(panels):
    y0 = i * (H + 40) + 40
    sheet.paste(im, (0, y0))
    d.text((12, y0 - 32), f"{w['name']}로 공격 → 소리 원 (반지름 {w['noise']}) · 원 안 피폭체 머리 위 '?' = 소리를 듣고 온다",
           font=font, fill=(196, 170, 92))
sheet = sheet.resize((sheet.width * 2 // 3, sheet.height * 2 // 3), Image.NEAREST)
sheet.save("docs/planning/noise_ring_mockup.png"); print(sheet.size)
