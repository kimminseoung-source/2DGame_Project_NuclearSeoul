"""The shown range is the hit range; a marked target is hit; speeds differ by weapon."""
import sys, random
from math import pi, cos, sin, hypot
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected, weapons
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def scene(wkey, zx, zy, seed=1):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    h = g.hero; h.x, h.y = 420, 300; h.weapon = weapons.WEAPONS[wkey]
    z = infected.Zombie(g.zombie_look, 900, 600); g.zombies[:] = [z]
    for _ in range(60): g.update(1 / 60, keys)
    z.x, z.y, z.state, z.heading, z.health, z.turn_in = zx, zy, "chase", pi, 9, 99
    z.seen_time, z.target, z.memory = 0.1, (h.x, h.y), 9
    return g, h, z
def scr(g, wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k
for wkey in ("knife", "machete", "axe"):
    rng = weapons.attack_range(weapons.WEAPONS[wkey])
    # marked: aim along the path at its torso; it stands just inside the range
    g, h, z = scene(wkey, 420 + rng - 6, 300)
    sx, sy = scr(g, h.x + 300, h.y + 22)
    shown = g.aimed(sx, sy)
    g.press(sx, sy)
    for _ in range(12): g.update(1 / 60, keys)
    z.x, z.y = 420 + rng - 6, 300
    g.release(sx, sy)
    for _ in range(60): g.update(1 / 60, keys)
    marked_hit = z.health < 9 or not z.alive
    # unmarked, just outside the drawn range in the aim direction
    g, h, z = scene(wkey, 420 + rng + 14, 300)
    z.state, z.timer, z.push = "flinch", 9, (0.0, 0.0)  # held still: it must not walk into range
    g.click(*scr(g, h.x + 300, h.y - 60))            # aim elsewhere so it is not marked
    for _ in range(60): g.update(1 / 60, keys)
    out_hit = z.health < 9 or not z.alive
    w = weapons.WEAPONS[wkey]
    print(f"{wkey}: range {rng:.0f}px | marked at the edge -> {'hit' if marked_hit else 'MISS'} (shown {shown and shown[1]})"
          f" | outside range -> {'HIT' if out_hit else 'not hit'} | blow {w['time']:.2f}s + rest {w['cooldown']:.2f}s ({weapons.speed_word(w)})")
