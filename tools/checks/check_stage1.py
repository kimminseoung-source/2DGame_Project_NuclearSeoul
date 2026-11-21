import sys
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui
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
g = play.Game()
for z in g.zombies: z.state = "dead"; z.timer = 9
g.to_spawn = 0
item = g.supplies[2]                       # bandage at (700, 500)
g.hero.x, g.hero.y = item.x - 15, item.y
for _ in range(20): g.update(1 / 60, keys)
shot(g, "s1_near_item")
g.key_down(sdl2.SDLK_e, keys); print("picked:", item.taken, g.bag, "|", g.message)
g.hero.hp = 1; g.key_down(sdl2.SDLK_1, keys); print("bandage used: hp", g.hero.hp, g.bag["bandage"])
g.exposure = 50; g.supplies[1].taken = False
g.hero.x, g.hero.y = g.supplies[1].x, g.supplies[1].y; g.key_down(sdl2.SDLK_e, keys)
g.key_down(sdl2.SDLK_2, keys); print("pill used: exposure", g.exposure, g.bag["pill"])
g.hero.x, g.hero.y = 880.0, 540.0
for _ in range(30): g.update(1 / 60, keys)
shot(g, "s2b_sign")
g.hero.x, g.hero.y = 940.0, 552.0
for _ in range(30): g.update(1 / 60, keys)
print("near exit:", g.near_exit())
shot(g, "s2_exit")
g.key_down(sdl2.SDLK_e, keys); g.update(1 / 60, keys); print("left:", g.left, "|", g.message)
shot(g, "s3_summary")
pico2d.close_canvas()
ims = [Image.open(f"{out}/{n}.png") for n in ("s1_near_item", "s2_exit", "s3_summary")]
sheet = Image.new("RGB", (settings.WIDTH, settings.HEIGHT * 3 + 20), (0, 0, 0))
for i, im in enumerate(ims): sheet.paste(im, (0, i * (settings.HEIGHT + 10)))
sheet.save(f"{out}/stage1.png"); print("ok")
