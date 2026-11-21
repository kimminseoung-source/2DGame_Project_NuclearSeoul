"""Aimed blows: hold to ready, release to strike; the part under the cursor sets the damage."""
import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected, weapons
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fresh(seed=1):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    z = infected.Zombie(g.zombie_look, 900, 600); g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    for _ in range(60): g.update(1 / 60, keys)
    return g, g.hero, z
def scr(g, wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
for part, up in (("legs", 8), ("torso", 28), ("head", 48)):
    g, h, z = fresh(); z.x, z.y, z.state, z.health, z.seen_time, z.heading = h.x + 55, h.y, "chase", 30, 1, pi
    z.target, z.memory = (h.x, h.y), 9
    sx, sy = scr(g, z.x, z.y + up)
    print(part, "-> aimed", g.aimed(sx, sy) and g.aimed(sx, sy)[1], end=" | ")
    g.press(sx, sy)
    for _ in range(32): g.update(1 / 60, keys)          # held until charged
    ready = h.ready
    g.draw()
    sx, sy = scr(g, z.x, z.y + up)                     # the cursor follows it, as a player would
    g.release(sx, sy)
    pose, t0 = h.slash and h.slash["pose"], h.slash and round(h.slash["time"], 3)
    for _ in range(30): g.update(1 / 60, keys)
    print(f"held {ready:.2f}s, pose {pose}, starts at {t0}s | health 30 -> {z.health if z.alive else 'dead'}, crawls {z.prone}, {g.message}")
g, h, z = fresh(2); z.x, z.y = h.x + 300, h.y
g.press(*scr(g, h.x + 60, h.y + 20)); g.release(*scr(g, h.x + 60, h.y + 20))
print("quick click on empty ground: starts at", h.slash and h.slash["time"], "pose", h.slash and h.slash["pose"])
g, h, z = fresh(3); h.stamina.value = 100
g.press(*scr(g, h.x + 60, h.y + 20))
for _ in range(60): g.update(1 / 60, keys)
print("holding 1 s: stamina", round(h.stamina.value), "ready", round(h.ready, 2))
