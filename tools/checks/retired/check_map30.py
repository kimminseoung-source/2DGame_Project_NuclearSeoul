"""Real-map area: does the summary card draw, and do chasing infected get around buildings?"""
import sys, random; sys.path.insert(0, "src")
from math import hypot
import pico2d, sdl2, play, settings, ui, area, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(1); g = play.Game(); g.to_spawn = 0
g.left = True; pico2d.clear_canvas(); g.draw(); pico2d.update_canvas(); g.left = False
print("summary with credit ok:", area.CREDIT)
# the biggest building: hero on one side, an infected that knows where he is on the other
cases = []
for l, b, r, t in (bl for bl, look in zip(area.BLOCKS, area.BLOCK_LOOKS) if look == "building"):
    for hx, hy, zx, zy in (((l + r) / 2, b - 40, (l + r) / 2, t + 40), (l - 40, (b + t) / 2, r + 40, (b + t) / 2)):
        if not area.blocked(hx, hy) and not area.blocked(zx, zy) and hypot(zx - hx, zy - hy) > 150:
            cases.append((hx, hy, zx, zy))
random.seed(7); cases = random.sample(cases, 6)
stuck = 0
for hx, hy, zx, zy in cases:
    g.hero.x, g.hero.y = hx, hy
    z = infected.Zombie(g.zombie_look, zx, zy); z.prone = False
    g.zombies[:] = [z]; z.state, z.target, z.memory = "chase", (hx, hy), 99
    start = hypot(z.x - hx, z.y - hy)
    for _ in range(60 * 30):
        g.hero.hp = 100; g.hero.x, g.hero.y = hx, hy
        g.update(1 / 60, keys)
    end = hypot(z.x - hx, z.y - hy)
    print(f"around a building from ({zx:.0f},{zy:.0f}): {start:.0f} -> {end:.0f} px, state {z.state}")
    stuck += end > 80
print("stuck:", stuck)

