"""The hero looks across a wreck (day and night): where does the shadow behind it start?"""
import sys, ctypes; sys.path.insert(0, "src")
from math import atan2
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
look = sys.argv[1] if len(sys.argv) > 1 else "wreck_1"
i = area.BLOCK_LOOKS.index(look)
l, b, r, t = area.BLOCKS[i]
print(look, "rect", (l, b, r, t), "| in sight blockers:", (l, b, r, t) in area.sight_blocks(l, b, r, t))
shots = []
for hour, extra in ((13, False), (22, False), (22, True)):
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
    for z in g.zombies: z.state, z.timer = "dead", 99
    g.daylight.hour = hour
    g.hero.x, g.hero.y = l - 120, (b + t) / 2 - 25          # down-left of the wreck, looking across it
    g.dev.boxes = extra
    for _ in range(30): g.update(1 / 60, keys)
    # aim at the far side of the wreck
    k = g.zoom * settings.DOT
    sx = (r + 60 - g.cam[0]) * k; sy = settings.HEIGHT - ((t + 20) - g.cam[1]) * k
    g.aim = (sx, sy)
    for _ in range(5): g.update(1 / 60, keys)
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    im = Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
    cx = ((l + r) / 2 - g.cam[0]) * k; cy = settings.HEIGHT - ((b + t) / 2 - g.cam[1]) * k
    shots.append((f"{hour}시" + (" F1" if extra else ""), im.crop((int(cx - 330), int(cy - 170), int(cx + 330), int(cy + 150)))))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 18)
sheet = Image.new("RGB", (660, 3 * 350), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for n, (label, im) in enumerate(shots):
    sheet.paste(im, (0, n * 350 + 28)); d.text((8, n * 350 + 4), label, font=f, fill=(230, 200, 110))
sheet.save(f"docs/planning/shadow_{look}.png")
pico2d.close_canvas(); print("ok")
