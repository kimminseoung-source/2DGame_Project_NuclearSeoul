"""Roll easing: same distance, more of it early; old even roll for comparison."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, hero as hero_rules, stamina
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.zombies[:] = []
for _ in range(5): g.update(1 / 60, keys)
h = g.hero; SX, SY = h.x, h.y
for ease in ((1.0, 1.0), (1.6, 0.4)):
    hero_rules.ROLL_EASE = ease
    for fps in (60, 144):
        h.x, h.y = SX, SY; h.roll = 0; h.roll_cooldown = 0; h.stamina.value = stamina.MAX
        x0 = h.x; ok = h.start_roll(1, 0); xs = [0.0]; print("started", ok, h.roll)
        while h.roll > 0:
            g.update(1 / fps, keys); xs.append(h.x - x0)
        half = xs[len(xs) // 2 - 1]
        print(f"ease {ease} {fps}fps: distance {xs[-1]:.1f}px, half the time {half:.1f}px ({half / xs[-1]:.0%})")
