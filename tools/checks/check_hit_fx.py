"""The hero hit (2026-11-22): the view is knocked the way the blow pushes him and settles in HIT_SHAKE s;
the whole screen flushes red and drains in HIT_RED s; frame time. Saves a strip of frames."""
import sys, ctypes, random, time; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui
from PIL import Image, ImageDraw, ImageFont, ImageStat
from pico2d import pico2d as canvas
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(1)
g = play.Game(); g.to_spawn = 0
z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]
for _ in range(3): g.update(1 / 60, keys)
h = g.hero
z.x, z.y = h.x + 24, h.y; z.heading = pi; z.state, z.timer, z.windup = "windup", 0.01, 0.01
drawn = []
real_draw = g.ground_img.draw if g.ground_img is not None else None
if real_draw:
    g.ground_img.draw = lambda x, y, w, hh: (drawn.append((x, y)), real_draw(x, y, w, hh))[1]
def frame():
    drawn.clear(); pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    return im, (drawn[0] if drawn else None)
base_im, base_at = frame()
base_red = ImageStat.Stat(base_im).mean
shots, rows = [("맞기 전", base_im)], []
hp = h.hp
t = 0.0
for f in range(30):
    g.update(1 / 60, keys); t += 1 / 60
    im, at = frame()
    m = ImageStat.Stat(im).mean
    shift = (round(at[0] - base_at[0] + (g.cam[0] - g.cam[0]), 1) if at and base_at else None)
    rows.append((round(t, 3), round(g.shake, 3), g.shake_dir and tuple(round(v, 2) for v in g.shake_dir),
                 round(m[0] - m[1], 1), round(g.hit_red, 3)))
    if f in (1, 4, 9, 18): shots.append((f"{t:.2f}s", im))
print("hp", round(hp), "->", round(h.hp), "| zombie on the right, so the push is to the left: dir", rows[2][2])
for r in rows[:22:3]:
    print("t", r[0], "shake", r[1], "red-green", r[3], "red left", r[4])
for red in (0.0, 0.3, 0.0, 0.3):
    g.hit_red = red; t0 = time.perf_counter()
    for _ in range(30): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    print(f"frame, red flush {'on ' if red else 'off'}: {(time.perf_counter() - t0) / 30 * 1000:.2f}ms")
k = g.zoom * settings.DOT
hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
f = ImageFont.truetype("malgun.ttf", 16)
crops = [(lab, im.crop((int(hx) - 160, int(hy) - 150, int(hx) + 160, int(hy) + 60))) for lab, im in shots]
cw, ch = crops[0][1].size
sheet = Image.new("RGB", (cw * len(crops), ch + 22), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for i, (lab, c) in enumerate(crops):
    sheet.paste(c, (i * cw, 22)); d.text((i * cw + 4, 2), lab, font=f, fill=(230, 220, 190))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/hit_fx.png"); print("ok")
