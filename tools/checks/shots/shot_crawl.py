"""In-game shots: the hero mid-shove, and a crawler coming on."""
import sys, random
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
canvas_ = pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
import pico2d as p2
def shot(name):
    p2.clear_canvas(); g.draw(); p2.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(out + f"/{name}.png")
random.seed(5)
g = play.Game(); g.to_spawn = 0
hero = g.hero; hero.x, hero.y = 420, 240
zs = g.zombies[:2]; g.zombies[:] = zs
a, b = zs
a.x, a.y, a.state = hero.x + 30, hero.y, "chase"
b.x, b.y = hero.x + 110, hero.y - 40
b.state, b.prone, b.crawl_left, b.facing = "crawl", True, 30.0, -1
for _ in range(20): g.update(1 / 60, keys)
for _ in range(8): g.update(1 / 60, keys)
a.x, a.y, a.state = hero.x + 30, hero.y, "chase"
cx, cy = (a.x - g.cam[0]) * settings.SCALE if hasattr(settings, "SCALE") else 0, 0
g.right_click(*[(v) for v in ((hero.x + 40 - g.cam[0]) * play.SCALE, settings.HEIGHT - 1 - (hero.y + 20 - g.cam[1]) * play.SCALE)])
for _ in range(6): g.update(1 / 60, keys)
shot("ingame_shove_crawl")
print("hero shove", round(hero.shove, 3), "a", a.state, "b", b.state, round(b.x), round(b.y))
