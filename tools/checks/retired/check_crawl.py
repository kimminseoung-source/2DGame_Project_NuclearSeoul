"""Crawl: a downed infected sometimes crawls toward the hero, slow, helpless, bites, gets up."""
import sys, random
from math import hypot
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
counts = {"crawl": 0, "up": 0}
for i in range(60):
    random.seed(i)
    g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; g.zombies[:] = [z]
    hero = g.hero
    z.x, z.y = hero.x + 140, hero.y
    z.reel(hero.x, hero.y, 0, "down", 0.01)
    for _ in range(3): g.update(1 / 60, keys)
    counts["crawl" if z.state == "crawl" else "up"] += 1
print("after down ->", counts, "(expect ~40% crawl)")

# one crawler: speed, helpless, reaches and bites, gets up after its time
random.seed(3)
g = play.Game(); g.to_spawn = 0
z = g.zombies[0]; g.zombies[:] = [z]
hero = g.hero
from area import BLOCKS
from vision_cone import ray_hit
for dx, dy in ((160, 0), (-160, 0), (0, 160), (0, -160), (120, 120), (-120, 120), (120, -120), (-120, -120)):
    d = hypot(dx, dy)
    from area import blocked
    if not blocked(hero.x + dx, hero.y + dy) and ray_hit(hero.x, hero.y, dx / d, dy / d, BLOCKS) > d + 20:
        break
z.x, z.y = hero.x + dx, hero.y + dy
d0 = hypot(z.x - hero.x, z.y - hero.y)
z.state, z.prone, z.crawl_left = "crawl", True, 30.0
for _ in range(60): g.update(1 / 60, keys)
print("crawl speed px/s", round(d0 - hypot(z.x - hero.x, z.y - hero.y), 1), "walk", settings.ZOMBIE_SPEED, "helpless", z.helpless)
hp0 = hero.hp; t = 0
while hero.hp == hp0 and t < 1200:
    g.update(1 / 60, keys); t += 1
print("bit hero after", round(t / 60, 1), "s: hp", hp0, "->", hero.hp, "state", z.state, "prone", z.prone)
for _ in range(120): g.update(1 / 60, keys)
print("after bite state", z.state, "prone", z.prone)
z.crawl_left = 0.01
for _ in range(60): g.update(1 / 60, keys)
print("time up ->", z.state, "prone", z.prone, "rising", z.rising)
# shove skips crawlers; draw works
z.state, z.prone, z.crawl_left = "crawl", True, 5.0
g.right_click(400, 300); print("shove on crawler ->", z.state)
g.draw(); print("draw ok")
