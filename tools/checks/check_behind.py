"""Notice behind: an idle infected facing away spots a still hero within NOTICE_NEAR, not beyond."""
import sys, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
for gap in (40, 80, 105, 130):
    random.seed(1)
    g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    z.x, z.y = g.hero.x + gap, g.hero.y; z.heading = 0.0; z.state = "idle"; z.turn_in = 99
    if not g.senses: g.toggle_senses()
    for _ in range(10): g.update(1 / 60, keys)
    print(f"등 뒤 {gap}px (가만히): {z.state}")
print("NOTICE_NEAR", infected.NOTICE_NEAR, "SPOT_DIST", infected.SPOT_DIST)
