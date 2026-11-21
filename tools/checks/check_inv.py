import sys
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(g, name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(f"{out}/{name}.png")
g = play.Game(); g.to_spawn = 0
# finisher: slash an idle infected from behind
for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
z = g.zombies[0]; z.prone = False; g.hero.x, g.hero.y = 470.0, 420.0; z.x, z.y = 510.0, 420.0; z.state = "idle"; z.heading = 0; z.turn_in = 99
g.aim = ((560 - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (420 + settings.CHEST - g.cam[1]) * settings.SCALE)
g.click(*g.aim); quiet = g.hero.slash.get("quiet")
for _ in range(40): g.update(1 / 60, keys)
print("finisher: quiet slash", quiet, "| killed", not z.alive, "|", g.message)
# condition: two chasing infected close -> tension; wounds
g = play.Game(); g.to_spawn = 0
for z in g.zombies[2:]: z.state = "dead"; z.timer = 9
for i, z in enumerate(g.zombies[:2]):
    z.x, z.y = g.hero.x + 90 + i * 20, g.hero.y; z.state = "chase"; z.seen_time = 0
for _ in range(120): g.condition.update(1 / 60, g.hero, g.zombies)
print("tension after 2 s with two close:", round(g.condition.tension, 2), "panic", g.condition.panic, "view", g.condition.view_scale())
import random; random.seed(3)
names = [g.condition.wound() for _ in range(4)]
print("wounds:", names, "| bleeding", g.condition.bleeding)
g.bag["bandage"] = 2; g.use("bandage"); print("bandage:", g.message, "| bleeding", g.condition.bleeding)
for z in g.zombies: z.state = "dead"; z.timer = 9
g.hero.slowed = 0.3; keys[sdl2.SDL_SCANCODE_LCTRL] = 1; g.update(1 / 60, keys); keys[sdl2.SDL_SCANCODE_LCTRL] = 0
shot(g, "status_panel")
# inventory with nearby items
it = g.supplies[0]; g.hero.x, g.hero.y = it.x + 5, it.y
g.bag["can"] = 1; g.key_down(sdl2.SDLK_TAB, keys)
shot(g, "inventory3")
g.key_down(sdl2.SDLK_f, keys); print("take all:", g.message, dict(g.bag))
pico2d.close_canvas(); print("ok")
