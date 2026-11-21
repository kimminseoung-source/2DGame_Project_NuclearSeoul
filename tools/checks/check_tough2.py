import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui, infected
from collections import Counter
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fight(seed, start="chase"):
    random.seed(seed)
    g = play.Game(); g.to_spawn = 0
    for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
    z = g.zombies[0]; z.prone = False; z.health = random.randint(*infected.HEALTH)
    g.hero.hp = 1e9; landed, states = 0, []
    for attempt in range(40):
        if not z.alive: break
        g.hero.x, g.hero.y = 400.0, 420.0; z.x, z.y = 432.0, 420.0
        if attempt == 0 or z.state == "flinch": z.state = start; z.timer = 9 if start == "down" else z.timer
        g.hero.slash = None; g.hero.slash_cooldown = 0; g.hero.roll = 0
        g.click((432 - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (448 - g.cam[1]) * settings.SCALE)   # aim at the torso
        if g.hero.slash is None: continue
        for _ in range(40):
            g.update(1 / 60, keys)
            if z.state in ("flinch", "down") and z.state not in states: states.append(z.state)
            if g.hero.slash is None or g.hero.slash.get("hit"): break
        if g.hero.slash and g.hero.slash.get("hit"): landed += 1
    return landed, states
res = [fight(s) for s in range(60)]
print("aware: slashes to kill", sorted(Counter(r[0] for r in res).items()), "| reactions", Counter(st for r in res for st in r[1]))
print("staggered (shoved):", sorted(Counter(fight(s, "stagger")[0] for s in range(10)).items()))
