"""v6.6: nothing is knocked down; counter = long stagger; crawlers from the start; stomp on them."""
import sys, random
from math import pi, hypot
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected
from collections import Counter
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fresh(seed, crawler=False):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    z = infected.Zombie(g.zombie_look, 900, 600, crawler=crawler); g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    for _ in range(60): g.update(1 / 60, keys)
    return g, g.hero, z
def scr(g, wx, wy): return (wx - g.cam[0]) * (g.zoom * settings.DOT), settings.HEIGHT - 1 - (wy - g.cam[1]) * (g.zoom * settings.DOT)
states = Counter()
for seed in range(40):                      # shoves at random moments, slashes on aware ones
    g, h, z = fresh(seed); z.x, z.y, z.state = h.x + 30, h.y, "chase"
    g.right_click(*scr(g, z.x, z.y + settings.CHEST)); states["shove->" + z.state] += 1
    g, h, z = fresh(seed); z.x, z.y, z.state, z.health = h.x + 30, h.y, "chase", 3
    g.click(*scr(g, z.x, z.y + settings.CHEST))
    for _ in range(12): g.update(1 / 60, keys); states["slash->" + z.state] += z.state == "down"
print("states after shoves / slashes:", dict(states))
g, h, z = fresh(1); z.x, z.y, z.state, z.timer, z.windup, z.heading = h.x + 30, h.y, "windup", 0.05, 0.6, pi
x0 = z.x; g.right_click(*scr(g, z.x, z.y + settings.CHEST))
print("counter:", z.state, round(z.timer, 2), "s", "|", g.message)
for _ in range(40): g.update(1 / 60, keys)
print("  pushed back", round(z.x - x0), "px")
random.seed(0); n = Counter()
for seed in range(200):
    random.seed(seed); g = play.Game(); n.update(z.prone for z in g.zombies)
print("crawlers among starting infected:", n[True], "/", n[True] + n[False])
g, h, z = fresh(3, crawler=True); z.x, z.y, z.state = h.x + 120, h.y, "chase"; z.seen_time = 1
d0 = hypot(z.x - h.x, z.y - h.y)
for _ in range(60): g.update(1 / 60, keys)
print("crawler speed", round(d0 - hypot(z.x - h.x, z.y - h.y), 1), "px/s, state", z.state)
g, h, z = fresh(4, crawler=True); z.x, z.y, z.state = h.x + 40, h.y, "chase"
g.click(*scr(g, z.x, z.y + settings.CHEST)); pose = h.slash and h.slash["pose"]
for _ in range(45): g.update(1 / 60, keys)
print("click on a crawler: pose", pose, "| killed", not z.alive, "| lies as it was", z.on_ground)
g, h, z = fresh(5); z.x, z.y, z.state, z.heading = h.x + 50, h.y, "idle", 0.0
g.click(*scr(g, z.x, z.y + settings.CHEST)); q = h.slash and h.slash.get("quiet")
for _ in range(40): g.update(1 / 60, keys)
print("unaware one: plain slash, quiet", q, "| killed", not z.alive, "| takedown attr", hasattr(h, "takedown"))
g.draw(); print("draw ok")
