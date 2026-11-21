"""Pillar 1: the opening after its claw (one slash), the counter shove at the end of the warning."""
import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected
from collections import Counter
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fresh(seed):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]; g.hero.x, g.hero.y = 420, 240; z.x, z.y = 900, 600; z.state = "idle"
    for _ in range(60): g.update(1 / 60, keys)
    return g, g.hero, z
def scr(g, wx, wy): return (wx - g.cam[0]) * (g.zoom * settings.DOT), settings.HEIGHT - 1 - (wy - g.cam[1]) * (g.zoom * settings.DOT)
# slash during recover: one slash kills (health 3)
res = Counter()
for seed in range(20):
    g, h, z = fresh(seed); z.health = 3
    z.x, z.y, z.state, z.timer, z.heading = h.x + 30, h.y, "recover", settings.ZOMBIE_RECOVER, pi
    g.click(*scr(g, z.x, z.y + settings.CHEST))
    for _ in range(30): g.update(1 / 60, keys)
    res["killed" if not z.alive else "alive"] += 1
print("slash in its recovery (health 3):", dict(res), "|", g.message)
# counter shove: late in the warning -> always down; early -> chance
for label, left in (("late", infected.COUNTER_WINDOW * 0.5), ("early", settings.ZOMBIE_WINDUP * 0.9)):
    res = Counter()
    for seed in range(40):
        g, h, z = fresh(seed)
        z.x, z.y, z.state, z.timer, z.windup, z.heading = h.x + 30, h.y, "windup", left, settings.ZOMBIE_WINDUP, pi
        g.right_click(*scr(g, z.x, z.y + settings.CHEST)); res[z.state] += 1
    print(f"shove {label} in the warning:", dict(res), "|", g.message)
