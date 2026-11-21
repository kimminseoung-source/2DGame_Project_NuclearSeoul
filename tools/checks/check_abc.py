import sys
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play as pt, settings, ui
pt.WIDTH, pt.HEIGHT, pt.SCALE, pt.CHEST, pt.ui = settings.WIDTH, settings.HEIGHT, settings.SCALE, settings.CHEST, ui
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(pt.WIDTH, pt.HEIGHT, sync=False); pt.ui.enable_blending()
def setup(senses, n=1):
    g = pt.Game(); g.senses = senses; g.reset()
    for z in g.zombies[n:]: z.state = "dead"; z.timer = 9
    return g
def look(g, wx, wy):
    g.aim = ((wx - g.cam[0]) * pt.SCALE, pt.HEIGHT - 1 - (wy + pt.CHEST - g.cam[1]) * pt.SCALE)
for senses in (False, True):
    tag = "new" if senses else "old"
    # A) an infected turns a corner right next to the hero: time until its warning starts
    g = setup(senses); z = g.zombies[0]; g.hero.x, g.hero.y = 500.0, 300.0
    z.x, z.y = 525.0, 300.0; z.heading = pi; z.state = "idle"; z.turn_in = 99
    t = 0
    while z.state != "windup" and t < 3:
        look(g, 700, 300); g.update(1 / 60, keys); t += 1 / 60
    print(f"[{tag}] A  sudden contact -> warning starts after {t:.2f}s")
    # B) a slash heard from behind: how long it stands turning before walking
    g = setup(senses); z = g.zombies[0]; g.hero.x, g.hero.y = 450.0, 300.0
    z.x, z.y = 620.0, 300.0; z.heading = 0.0; z.state = "idle"; z.turn_in = 99
    g.hero.start_slash(300, 300 + pt.CHEST); x0 = z.x; t = 0; states = []
    while abs(z.x - x0) < 1 and t < 2:
        look(g, 300, 300); g.update(1 / 60, keys); t += 1 / 60; states.append(z.state)
    print(f"[{tag}] B  heard a slash -> starts moving after {t:.2f}s, states {sorted(set(states))}")
    # C) two infected on the hero, a blow lands
    g = setup(senses, n=2); a, b = g.zombies[0], g.zombies[1]; g.hero.x, g.hero.y = 500.0, 300.0
    a.x, a.y, b.x, b.y = 524.0, 300.0, 478.0, 304.0
    for z in (a, b): z.state, z.seen_time, z.heading = "chase", 1.0, 0
    grabbed = 0; x_before = None
    for i in range(240):
        look(g, 700, 300); g.update(1 / 60, keys)
        if g.hero.grabbed > 0 and not grabbed:
            grabbed = 1; keys[sdl2.SDL_SCANCODE_W] = 1; x_before = (g.hero.x, g.hero.y)
            for j in range(20): g.update(1 / 60, keys)
            moved = (g.hero.x, g.hero.y) != x_before
            keys[sdl2.SDL_SCANCODE_W] = 0
            g.key_down(sdl2.SDLK_SPACE, keys); g.update(1 / 60, keys)
            print(f"[{tag}] C  grabbed: yes, could walk while held: {moved}, roll frees: {g.hero.grabbed == 0}")
            break
    if not grabbed:
        print(f"[{tag}] C  grabbed: no (hp {g.hero.hp})")
pico2d.close_canvas()
