import sys, random
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2
import play, settings, ui, hud
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(g, name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(out + "/" + name)
random.seed(3)
g = play.Game(); g.to_spawn = 0
g.hero.x, g.hero.y = 330.0, 330.0
z = g.zombies[0]; z.x, z.y = 400.0, 345.0; z.state = "chase"; z.spotted = 0.5; z.target = (330.0, 330.0); z.memory = 8
g.zombies[1].x, g.zombies[1].y = 250, 300
for _ in range(20): g.update(1 / 60, keys)
g.bag["bandage"] = 2; g.bag["can"] = 1
g.condition.wound(); g.condition.wound(); g.hero.hp = 58
g.aim = (settings.WIDTH * 0.62, settings.HEIGHT * 0.45)
g.message = "찢어짐! 체력 -22%"
for _ in range(3): g.update(1 / 60, keys)
shot(g, "now_play.png")
g.key_down(sdl2.SDLK_TAB, keys); shot(g, "now_bag.png")
g.key_down(sdl2.SDLK_TAB, keys)
saved = (hud.draw_hud, hud.draw_inventory)
hud.draw_hud = lambda game: None
shot(g, "bg_play.png")
hud.draw_hud = saved[0]
pico2d.close_canvas(); print("ok")
