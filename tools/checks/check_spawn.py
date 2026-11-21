import sys
from math import hypot
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); print("sounds loaded:", len(g.sounds.wavs))
g.hero.x, g.hero.y = 120.0, 120.0           # a quiet corner, away from the starting infected
for z in g.zombies: z.state = "dead"; z.timer = 9
times = []; t = 0.0
while t < 30 and g.to_spawn > 0:
    n = len(g.zombies); g.update(1 / 60, keys); t += 1 / 60
    if len(g.zombies) > n:
        z = g.zombies[-1]; times.append(round(t, 1))
        d = hypot(z.x - g.hero.x, z.y - g.hero.y)
        if len(times) <= 3: print(f"arrival at {t:.1f}s, {d:.0f}px from hero, state {z.state}")
        z.state = "dead"; z.timer = 9                  # keep the count low
print("arrivals in 30 s (quiet):", len(times))
# a slash brings the next one soon, heading for the noise
g.director.spawn_in = 8.0; t0 = t
g.hero.start_slash(g.hero.x + 50, g.hero.y + settings.CHEST)
while len(g.zombies) == len(g.zombies) and t - t0 < 5:
    n = len(g.zombies); g.update(1 / 60, keys); t += 1 / 60
    if len(g.zombies) > n: break
z = g.zombies[-1]
print(f"after a slash: next arrival {t - t0:.2f}s later, target {tuple(round(v) for v in z.target)} (hero at {round(g.hero.x)},{round(g.hero.y)})")
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
sdl2.SDL_SaveBMP(s, (sys.argv[2] + "/t.bmp").encode()); Image.open(sys.argv[2] + "/t.bmp").convert("RGB").save(sys.argv[2] + "/spawn.png")
pico2d.close_canvas()
