"""Two weights of hit feel: a light hit vs a finishing blow."""
import sys, random; sys.path.insert(0, "src")
from math import pi
import pico2d, sdl2, play, settings, ui
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def blow(health):
    random.seed(1)
    g = play.Game(); g.dev.no_spawn = True; g.dev.god = True
    for z in g.zombies[1:]: z.state, z.timer = "dead", 9
    z = g.zombies[0]; h = g.hero
    z.x, z.y, z.state, z.health, z.seen_time, z.heading, z.prone = h.x + 40, h.y, "chase", health, 1, pi, False
    g.dev.freeze = True
    sx, sy = 640 + 40 * settings.ZOOM_DEFAULT * settings.DOT, 360
    g.press(sx, sy); g.release(sx, sy)
    stop = amp = shake = flash = 0.0
    for _ in range(40):
        g.update(1 / 60, keys)
        stop, amp, shake = max(stop, g.hitstop), max(amp, g.shake_amp), max(shake, g.shake_len if g.shake > 0 else 0)
        flash = max(flash, getattr(z, "flash", 0))
    return z.alive, stop, amp, shake, flash


for label, health in (("light (survives)", 30), ("heavy (finished)", 1)):
    alive, stop, amp, shake, flash = blow(health)
    print(f"{label:18s} alive {alive} | hitstop {stop:.3f}s ({stop * 60:.0f} frames) | shake {amp:.0f}px for {shake:.2f}s | flash {flash:.3f}s")
pico2d.close_canvas(); print("ok")
