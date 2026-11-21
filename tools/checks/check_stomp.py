"""Stomping a crawler from the ways a player would click."""
import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def scene(dx, dy):
    random.seed(1); g = play.Game(); g.to_spawn = 0
    h = g.hero; h.x, h.y = 420, 300
    c = infected.Zombie(g.zombie_look, 900, 600, crawler=True); g.zombies[:] = [c]
    for _ in range(60): g.update(1 / 60, keys)
    c.x, c.y, c.state, c.heading = h.x + dx, h.y + dy, "chase", pi
    c.seen_time, c.target, c.memory = 1, (h.x, h.y), 9
    return g, h, c
def scr(g, wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
cases = [("click on its body", lambda h, c: (c.x, c.y + 6)),
         ("click on its head end", lambda h, c: (c.x + 14, c.y + 8)),
         ("cursor level, far", lambda h, c: (h.x + 200, h.y + 22)),
         ("cursor low, far", lambda h, c: (h.x + 200, h.y - 30))]
for dist in (30, 50):
    for label, where in cases:
        for held in (False, True):
            g, h, c = scene(dist, 0)
            sx, sy = scr(g, *where(h, c))
            shown = g.aimed(sx, sy)
            g.press(sx, sy)
            for _ in range(15 if held else 0): g.update(1 / 60, keys)
            sx, sy = scr(g, *where(h, c))
            g.release(sx, sy)
            pose = h.slash and h.slash["pose"]
            for _ in range(50): g.update(1 / 60, keys)
            print(f"{dist}px {label:22s} {'held ' if held else 'quick'}: shown {shown and shown[1]!s:6s} pose {pose!s:6s} -> {'dead' if not c.alive else 'ALIVE'}")
