import sys, random
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.to_spawn = 0
z = g.zombies[0]; z.prone = False; z.state = "idle"; z.target = None
z.shoved(g.hero.x, g.hero.y); g.hero.x, g.hero.y = 900, 600
for _ in range(400): g.update(1 / 60, keys)
print("shoved idle, hero gone ->", z.state, "no crash")
