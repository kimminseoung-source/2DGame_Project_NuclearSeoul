import sys
from math import pi
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
def aim(g, wx, wy):
    g.aim = ((wx - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (wy - g.cam[1]) * settings.SCALE)
g = play.Game(); g.to_spawn = 0
for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
z = g.zombies[0]
# pick up: E near the bandage, check the motion
item = next(s for s in g.supplies if s.kind == "bandage")
g.hero.x, g.hero.y = item.x - 10, item.y
for _ in range(5): aim(g, item.x + 100, item.y); g.update(1 / 60, keys)
g.key_down(sdl2.SDLK_e, keys); print("pickup motion:", round(g.hero.pickup, 2), "bag", dict(g.bag))
x0 = g.hero.x; keys[sdl2.SDL_SCANCODE_D] = 1
for _ in range(10): g.update(1 / 60, keys)
print("moved during pickup:", round(g.hero.x - x0, 1)); keys[sdl2.SDL_SCANCODE_D] = 0
for c in g.supplies:
    if c.kind == "can" and not c.taken: c.taken = True; g.bag["can"] += 1; break
# spotted "!": an infected facing the hero 150 px away
g.hero.x, g.hero.y = 460.0, 420.0; z.x, z.y = 600.0, 420.0; z.state = "idle"; z.heading = pi; z.turn_in = 99
for i in range(20):
    aim(g, 620, 420); g.update(1 / 60, keys)
print("spotted:", z.state, round(z.spotted, 2))
shot(g, "ui_hud")
g.key_down(sdl2.SDLK_TAB, keys); g.hero.hp = 1
shot(g, "ui_bag")
g.key_down(sdl2.SDLK_RETURN, keys); print("used from bag: hp", g.hero.hp, "bandages", g.bag["bandage"], "| bag open", g.bag_open)
before = (z.x, z.y); g.update(1 / 60, keys); print("world paused while bag open:", (z.x, z.y) == before)
g.key_down(sdl2.SDLK_TAB, keys); print("closed:", not g.bag_open)
pico2d.close_canvas(); print("ok")
