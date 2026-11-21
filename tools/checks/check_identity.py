"""Paces of the infected; what each weapon is good and bad at."""
import sys, random
from math import pi
from collections import Counter
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected, weapons
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(3); paces = Counter(round(infected.Zombie(None, 0, 0).pace, 1) for _ in range(1000))
print("paces of 1000:", dict(sorted(paces.items())), "| speeds px/s:", sorted({round(infected.ZOMBIE_SPEED * p) for p in paces}))
def scene(wkey):
    random.seed(1); g = play.Game(); g.to_spawn = 0
    h = g.hero; h.x, h.y = 420, 300; h.weapon = weapons.WEAPONS[wkey]
    z = infected.Zombie(g.zombie_look, 900, 600); g.zombies[:] = [z]
    for _ in range(60): g.update(1 / 60, keys)
    z.x, z.y, z.state, z.heading, z.health = h.x + 45, h.y, "chase", pi, 30
    z.seen_time, z.target, z.memory = 0.1, (h.x, h.y), 9
    return g, h, z
def scr(g, wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
for wkey in ("knife", "machete", "bat", "pipe", "axe"):
    g, h, z = scene(wkey)
    heard = []
    g.make_noise = lambda r, *a, **k: heard.append(r)
    g.click(*scr(g, h.x + 200, h.y + 22))                    # quick, torso
    for _ in range(40): g.update(1 / 60, keys)
    torso = f"torso -> health {z.health if z.alive else 'dead'}, {z.state}"
    g, h, z = scene(wkey)
    g.click(*scr(g, h.x + 200, h.y + 90))                    # quick, head
    for _ in range(40): g.update(1 / 60, keys)
    head = f"quick head -> {z.health if z.alive else 'dead'}"
    print(f"{wkey:8s} noise {max(heard) if heard else '-'} | {torso} | {head}")
