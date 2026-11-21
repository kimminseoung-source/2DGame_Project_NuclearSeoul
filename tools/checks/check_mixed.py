"""A crawler and a standing infected together: aim low = stomp the crawler, level = the standing
one; swings and stabs pass over a crawler, a chop reaches it; part rules."""
import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected, weapons
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def scene(seed=1):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    h = g.hero; h.x, h.y = 420, 300
    c = infected.Zombie(g.zombie_look, 900, 600, crawler=True)
    s = infected.Zombie(g.zombie_look, 900, 600)
    g.zombies[:] = [c, s]
    for _ in range(60): g.update(1 / 60, keys)
    c.x, c.y, c.state, c.heading = h.x + 26, h.y, "chase", pi
    s.x, s.y, s.state, s.heading, s.health = h.x + 40, h.y + 2, "chase", pi, 30   # within the reach (2026-11-16 shorter)
    for z in (c, s): z.seen_time, z.target, z.memory = 1, (h.x, h.y), 9
    return g, h, c, s
def scr(g, wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
g, h, c, s = scene()
for label, dy in (("cursor low", -25), ("cursor level", 22), ("cursor raised", 75)):
    a = g.aimed(*scr(g, h.x + 200, h.y + dy)); print(label, "->", a and ("crawler" if a[0] is c else "standing"), a and a[1])
for wname in ("machete", "bat", "knife"):
    g, h, c, s = scene()
    h.weapon = weapons.WEAPONS[wname]
    g.click(*scr(g, h.x + 200, h.y + 22))
    for _ in range(40): g.update(1 / 60, keys)
    print(f"{wname} ({h.weapon['style']}) at the standing one: crawler {'dead' if not c.alive else 'alive'}, standing health {s.health if s.alive else 'dead'}")
g, h, c, s = scene()
g.click(*scr(g, h.x + 200, h.y - 25)); pose = h.slash and h.slash["pose"]
for _ in range(40): g.update(1 / 60, keys)
print("aim low: pose", pose, "| crawler", "dead" if not c.alive else "alive", "| standing", s.health if s.alive else "dead")
# head: quick vs held
for held in (False, True):
    g, h, c, s = scene(); g.zombies[:] = [s]; s.x = h.x + 50
    sx, sy = scr(g, h.x + 200, h.y + 90)
    g.press(sx, sy)
    for _ in range(32 if held else 0): g.update(1 / 60, keys)
    if held: s.x, s.y = h.x + 50, h.y + 2
    g.release(sx, sy)
    for _ in range(40): g.update(1 / 60, keys)
    print("head,", "held" if held else "quick", "-> health 30 ->", s.health if s.alive else "dead", "| state", s.state)
print("crawl speed", round(infected.ZOMBIE_SPEED * infected.CRAWL_SPEED, 1), "px/s")
