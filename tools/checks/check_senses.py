import sys
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play as pt, settings, ui
pt.WIDTH, pt.HEIGHT, pt.SCALE, pt.CHEST, pt.ui = settings.WIDTH, settings.HEIGHT, settings.SCALE, settings.CHEST, ui
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(pt.WIDTH, pt.HEIGHT, sync=False); pt.ui.enable_blending()
def setup(senses):
    g = pt.Game(); g.senses = senses; g.reset()
    for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
    return g, g.zombies[0]
def run(g, sec, aim=None):
    for _ in range(int(sec * 60)):
        if aim: g.aim = ((aim[0] - g.cam[0]) * pt.SCALE, pt.HEIGHT - 1 - (aim[1] - g.cam[1]) * pt.SCALE)
        g.update(1 / 60, keys)
res = {}
for senses in (False, True):
    # 1) hero stands still 150 px behind an infected that faces away
    g, z = setup(senses); z.x, z.y = 600.0, 300.0; z.heading = 0.0; z.turn_in = 99
    g.hero.x, g.hero.y = 450.0, 300.0
    run(g, 2.0, aim=(600, 300))
    res[("still_behind", senses)] = z.state
    # 2) same, but the hero slashes the air
    g, z = setup(senses); z.x, z.y = 600.0, 300.0; z.heading = 0.0; z.turn_in = 99
    g.hero.x, g.hero.y = 450.0, 300.0
    run(g, 0.2, aim=(600, 300)); g.hero.start_slash(400, 300 + pt.CHEST); run(g, 0.3, aim=(600, 300))
    res[("slash_noise", senses)] = z.state
    # 3) infected reaches the hero from behind his sight vs in front
    for side, look_x in (("front", 700), ("behind", 300)):
        g, z = setup(senses); g.hero.x, g.hero.y = 500.0, 300.0; z.x, z.y = 540.0, 300.0
        z.state = "chase"; z.heading = pi
        w = None
        for _ in range(120):
            g.aim = ((look_x - g.cam[0]) * pt.SCALE, pt.HEIGHT - 1 - (300 + pt.CHEST - g.cam[1]) * pt.SCALE)
            g.update(1 / 60, keys)
            if z.state == "windup": w = z.windup; break
        res[("windup_" + side, senses)] = w
pico2d.close_canvas()
for k in ("still_behind", "slash_noise", "windup_front", "windup_behind"):
    print(f"{k:14s} old: {res[(k, False)]!s:8s} new: {res[(k, True)]}")
