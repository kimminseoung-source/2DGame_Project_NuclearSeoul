"""The rush: an infected that spots the hero runs at him for RUSH_TIME, then walks."""
import sys, random; sys.path.insert(0, "src")
from math import hypot, pi
import pico2d, sdl2, play, settings, ui, infected, area
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2); g = play.Game(); g.to_spawn = 0
# an open stretch of ground: the hero, and 130 px off an infected looking at him
spot = next((x, y) for x in range(300, area.ROOM_W - 300, 40) for y in range(300, area.ROOM_H - 300, 40)
            if all(not area.blocked(x + dx, y) for dx in range(0, 260, 10)))
h = g.hero; h.x, h.y = spot
z = infected.Zombie(g.zombie_look, h.x + 130, h.y); z.prone = False; z.pace = 1.0
z.heading, z.turn_in = pi, 99
g.zombies[:] = [z]
log, t = [], 0.0
for f in range(60 * 4):
    h.hp = 100
    keys[sdl2.SDL_SCANCODE_W] = 1 if (f // 20) % 2 else 0     # stepping about: easy to spot
    keys[sdl2.SDL_SCANCODE_S] = 0 if (f // 20) % 2 else 1
    before = (z.x, z.y)
    g.update(1 / 60, keys); t += 1 / 60
    if f % 15 == 0:
        log.append(f"{t:.2f}s {z.state:7s} rush {z.rush:.2f} speed {hypot(z.x - before[0], z.y - before[1]) * 60:.0f}")
print("\n".join(log[:12]))

