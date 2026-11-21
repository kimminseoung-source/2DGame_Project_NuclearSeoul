import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui, supplies
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def aim(g, wx, wy):
    g.aim = ((wx - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (wy - g.cam[1]) * settings.SCALE)
def spot_time(still, sneak, n=40):
    times = []
    for seed in range(n):
        g = play.Game(); g.to_spawn = 0
        random.seed(seed * 7 + (3 if sneak else 0) + (5 if still else 0))
        for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
        z = g.zombies[0]; g.hero.x, g.hero.y = 400.0, 420.0; z.x, z.y = 560.0, 420.0
        z.state = "idle"; z.heading = pi; z.turn_in = 99
        keys[sdl2.SDL_SCANCODE_LCTRL] = 1 if sneak else 0
        t = 0
        while z.state not in ("chase", "poised") and t < 6:
            keys[sdl2.SDL_SCANCODE_W] = 0 if still else (1 if int(t * 2) % 2 == 0 else 0)
            keys[sdl2.SDL_SCANCODE_S] = 0 if still else (0 if int(t * 2) % 2 == 0 else 1)
            aim(g, 300, 420); g.update(1 / 60, keys); t += 1 / 60
        times.append(t)
    keys[sdl2.SDL_SCANCODE_W] = keys[sdl2.SDL_SCANCODE_S] = keys[sdl2.SDL_SCANCODE_LCTRL] = 0
    times.sort(); return round(sum(times) / len(times), 2), round(times[len(times) // 2], 2), sum(t >= 6 for t in times)
print("spot time at 160px, median s / never in 6s (of 40): walking", spot_time(False, False), " sneaking", spot_time(False, True), " still", spot_time(True, False))
g = play.Game(); g.to_spawn = 0
for z in g.zombies: z.state = "dead"; z.timer = 9
x0 = g.hero.x; keys[sdl2.SDL_SCANCODE_D] = 1
for _ in range(30): g.update(1 / 60, keys)
walk = g.hero.x - x0; g.hero.take_blow(); g.hero.take_blow(); x0 = g.hero.x
for _ in range(30): g.update(1 / 60, keys)
print("slowed after two blows: speed share", round((g.hero.x - x0) / walk, 2)); keys[sdl2.SDL_SCANCODE_D] = 0
# front sound: idle infected facing the sound goes straight to search
g = play.Game(); g.to_spawn = 0
z = g.zombies[0]; z.state = "idle"; z.x, z.y = 600, 300; z.heading = pi
z.hear(500, 300, 200); print("sound ahead ->", z.state)
z.state = "idle"; z.heading = 0; z.hear(500, 300, 200); print("sound behind ->", z.state)
# weight limit
g = play.Game(); g.bag["can"] = 5
c = next(s for s in g.supplies if s.kind == "can"); g.hero.x, g.hero.y = c.x, c.y
g.interact(); print("bag full:", g.message, "| taken", c.taken)
g.key_down(sdl2.SDLK_TAB, keys); g.bag_cursor = 0; g.key_down(sdl2.SDLK_x, keys); print("dropped:", g.message, g.bag)
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(out + "/bag_list.png")
pico2d.close_canvas(); print("ok")
