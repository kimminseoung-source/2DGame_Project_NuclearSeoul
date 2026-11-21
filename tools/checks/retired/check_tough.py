import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fight(seed, start="chase"):
    random.seed(seed)
    g = play.Game(); g.to_spawn = 0
    for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
    z = g.zombies[0]; g.hero.x, g.hero.y = 400.0, 420.0; z.x, z.y = 430.0, 420.0
    z.state = start; z.heading = pi; z.health = random.randint(*infected.HEALTH)
    g.hero.hp = 1e9
    slashes, states = 0, []
    while z.alive and slashes < 10:
        z.x, z.y = 430.0, 420.0
        if z.state not in ("down", "stagger", "idle", "alert", "search"): z.state = "chase"  # keep it aware between swings
        g.aim = ((440 - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (420 + 14 - g.cam[1]) * settings.SCALE)
        g.hero.slash = None; g.hero.slash_cooldown = 0
        g.click(*g.aim) if hasattr(g, "click") else g.left_click(*g.aim)
        slashes += 1
        for _ in range(30):
            g.update(1 / 60, keys)
            if z.state in ("flinch", "down") and z.state not in states: states.append(z.state)
        if z.state == "flinch": z.state = "chase"
    return slashes, states
res = [fight(s) for s in range(40)]
from collections import Counter
print("aware: slashes to kill", Counter(r[0] for r in res), "| reactions seen", Counter(st for r in res for st in r[1]))
print("unaware idle: slashes", Counter(fight(s, "idle")[0] for s in range(10)))
g = play.Game(); z = g.zombies[0]; z.state, z.timer = "windup", 0.4; z.health = 3
print("hit during windup ->", z.hurt(z.x - 20, z.y), z.state, "| helpless", z.helpless)
print("moodles at panic:", (g.condition.__setattr__("tension", 1.0), g.condition.moodles(g.hero))[1])
