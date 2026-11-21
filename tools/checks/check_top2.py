import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(exist_ok=True)
import pico2d, sdl2
from pico2d import pico2d as canvas
from PIL import Image
import play as pt, settings, ui
pt.WIDTH, pt.HEIGHT, pt.SCALE, pt.CHEST, pt.ui = settings.WIDTH, settings.HEIGHT, settings.SCALE, settings.CHEST, ui
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
def grab(name):
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, pt.WIDTH, pt.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, str(out / "t.bmp").encode()); Image.open(out / "t.bmp").convert("RGB").save(out / name)
pico2d.open_canvas(pt.WIDTH, pt.HEIGHT, sync=False); pt.ui.enable_blending()
g = pt.Game()
def aim_world(wx, wy):
    g.aim = ((wx - g.cam[0]) * pt.SCALE, pt.HEIGHT - 1 - (wy - g.cam[1]) * pt.SCALE)
def frame(): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
g.hero.x, g.hero.y = 200.0, 318.0
hidden = g.zombies[0]; hidden.x, hidden.y = 420.0, 322.0       # behind the car
seen = g.zombies[1]; seen.x, seen.y = 400.0, 230.0             # in the open, inside the cone
for z in g.zombies[2:]: z.state = "dead"; z.timer = 9
for i in range(40):
    hidden.state = seen.state = "idle"
    aim_world(g.hero.x + 200, g.hero.y - 10); g.update(1/60, keys)
eye = (g.hero.x, g.hero.y)
print("behind car visible:", g.vision.visible(eye, g.look, hidden.x, hidden.y), " open visible:", g.vision.visible(eye, g.look, seen.x, seen.y))
frame(); grab("shadow.png")
t = time.perf_counter()
for i in range(60): frame()
print("ms/frame", round((time.perf_counter() - t) / 60 * 1000, 2))
pico2d.close_canvas(); print("ok")
