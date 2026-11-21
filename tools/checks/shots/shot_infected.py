"""The infected as they look in the game now: standing, walking, winding up, crawling - enlarged."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(1)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
g.daylight.hour = 13
h = g.hero
for _ in range(5): g.update(1 / 60, keys)
zs = g.zombies[:4]
for i, (z, state) in enumerate(zip(zs, ("idle", "chase", "windup", "chase"))):
    z.x, z.y, z.state, z.prone, z.heading, z.facing = h.x + 70 + i * 60, h.y, state, i == 3, pi, -1
    z.timer = z.windup = 0.5
    z.walk = 1.3 * i
for z in g.zombies[4:]: z.state, z.timer = "dead", 99
g.aim = (1100, 360)
for _ in range(10): g.update(1 / 60, keys)
pico2d.clear_canvas(); g.draw()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
pico2d.update_canvas()
im = Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
cx = (h.x - g.cam[0]) * g.zoom * settings.DOT
cy = settings.HEIGHT - (h.y - g.cam[1]) * g.zoom * settings.DOT
box = (int(cx - 40), int(cy - 130), int(cx + 520), int(cy + 30))
im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.NEAREST).save("docs/planning/infected_now.png")
pico2d.close_canvas(); print("ok", box)
