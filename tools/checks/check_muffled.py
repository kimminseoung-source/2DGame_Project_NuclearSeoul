import sys
from math import hypot, pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False)
res = {}
for case, hero_pos in (("behind the car", (310.0, 355.0)), ("in the open", (310.0, 250.0))):
    offs = []
    for _ in range(30):
        g = play.Game(); g.to_spawn = 0
        for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
        z = g.zombies[0]; z.x, z.y = 310.0, 290.0 if case == "in the open" else 230.0
        z.state, z.heading, z.turn_in = "idle", -pi / 2, 99
        g.hero.x, g.hero.y = hero_pos
        g.make_noise(230)
        offs.append(hypot(z.target[0] - g.hero.x, z.target[1] - g.hero.y) if z.target else -1)
    res[case] = (round(min(offs)), round(sum(offs) / len(offs)), round(max(offs)))
print("where the infected goes vs the real spot (min / avg / max px):", res)
pico2d.close_canvas()
