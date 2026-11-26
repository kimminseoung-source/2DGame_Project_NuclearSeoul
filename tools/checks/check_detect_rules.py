"""2026-11-26 rule "보이면·가까우면 들키고, 쏘면 몰려온다" in the real game (hidden window).
Front 240 spotted, behind 80 spotted, behind 150 not, walking behind 120 not (footsteps silent),
a shot pulls an infected 380 px behind. Raises if any number is wrong."""
import sys, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def setup(gap, facing_hero):
    random.seed(1)
    g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    z.x, z.y = g.hero.x + gap, g.hero.y
    z.heading = pi if facing_hero else 0.0
    z.state, z.turn_in = "idle", 99
    play.blocks_between = infected.blocks_between = lambda *a, **k: []   # open ground
    if not g.senses: g.toggle_senses()
    return g, z


def run(g, frames=10):
    for _ in range(frames): g.update(1 / 60, keys)


results = {}
for name, gap, face, want in (("정면 240", 240, True, True), ("등 뒤 80", 80, False, True),
                              ("등 뒤 150", 150, False, False)):
    g, z = setup(gap, face); run(g)
    results[name] = (z.state != "idle", want)
g, z = setup(120, False); g.hero.moving = True
for _ in range(30):
    g.hero.moving = True; run(g, 1)
results["걷기 등 뒤 120"] = (z.state != "idle", False)
g, z = setup(380, False)
g.make_noise(400)                       # pistol shot noise (weapons.py "shot": noise 400)
results["총소리 380 등 뒤"] = (z.state != "idle", True)
bad = [k for k, (got, want) in results.items() if got != want]
for k, (got, want) in results.items():
    print(f"{k}: {'감지' if got else '미감지'} (기대 {'감지' if want else '미감지'})")
print("SIGHT_RANGE", infected.SIGHT_RANGE, "NOTICE_NEAR", infected.NOTICE_NEAR)
assert not bad, bad
print("감지 규칙 OK")
