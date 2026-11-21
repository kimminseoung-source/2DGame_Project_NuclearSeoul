"""Director outside: three blows -> peak, then relax, then build again; hurt hero = slower arrivals."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, director
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(3)
g = play.Game(); g.dev.freeze = True; g.to_spawn = 99
for z in g.zombies: z.state, z.timer = "dead", 9          # room for arrivals
d = g.director
for _ in range(3): d.hero_hit()
log, last, arrivals, n0 = [], None, [], len(g.zombies)
for f in range(40 * 60):
    g.update(1 / 60, keys)
    if d.state != last:
        log.append(f"{f / 60:5.1f}s -> {d.state} (intensity {d.intensity:.2f})"); last = d.state
    if len(g.zombies) > n0:
        arrivals.append((round(f / 60, 1), d.state)); n0 = len(g.zombies)
print("\n".join(log)); print("arrivals:", arrivals)
# hurt hero: next gap is 1.5x
g2 = play.Game(); g2.hero.hp = 20; g2.director.spawn_in = 0.0
g2.director.update(1 / 60, g2); print("hurt hero next gap:", round(g2.director.spawn_in, 1), "(build 6-9 x1.5 = 9-13.5)")
pico2d.close_canvas(); print("ok")
