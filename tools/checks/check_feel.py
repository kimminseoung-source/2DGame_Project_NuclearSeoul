"""Experiments 빠르게 / 세게: how long a swing takes, how hard a hit lands."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, hero as hero_rules, dev_tools
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def setup():
    random.seed(1)
    g = play.Game(); g.dev.no_spawn = True; g.dev.god = True
    for z in g.zombies[1:]: z.state, z.timer = "dead", 9
    z = g.zombies[0]; h = g.hero
    z.x, z.y, z.state, z.health, z.seen_time, z.heading, z.prone = h.x + 40, h.y, "idle", 30, 0, pi, False
    g.dev.freeze = True
    return g, z


def swing(g):
    """Time from click to the next possible click; hitstop and shake on landing."""
    t, peak_stop, peak_shake = 0.0, 0.0, 0.0
    sx, sy = 640 + 40 * settings.ZOOM_DEFAULT * settings.DOT, 360
    g.press(sx, sy); g.release(sx, sy)
    while True:
        g.update(1 / 60, keys); t += 1 / 60
        peak_stop, peak_shake = max(peak_stop, g.hitstop), max(peak_shake, g.shake)
        if g.hero.free or t > 3:
            return t, peak_stop, peak_shake


for fast in (False, True):
    for punchy in (False, True):
        hero_rules.Hero.action_speed = 1.3 if fast else 1.0
        g, z = setup(); g.dev.punchy = punchy
        x0 = z.x
        t, stop, shake = swing(g)
        print(f"빠르게 {fast!s:5} 세게 {punchy!s:5}: swing to next {t:.2f}s | hitstop {stop:.3f} | shake {shake:.3f} | pushed {z.x - x0:.1f} | flash {getattr(z, 'flash', 0):.2f}")
# a picture of the flash
hero_rules.Hero.action_speed = 1.0
g, z = setup(); g.dev.punchy = True
for _ in range(40): g.update(1 / 60, keys)
z.flash = 0.12
pico2d.clear_canvas(); g.draw()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
pico2d.update_canvas()
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/feel_flash.png")
pico2d.close_canvas(); print("ok")

