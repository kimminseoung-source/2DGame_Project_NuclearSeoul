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
def aim(g, wx, wy):
    g.aim = ((wx - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (wy - g.cam[1]) * settings.SCALE)
for real in (False, True):
    g = play.Game()
    if g.real != real: g.key_down(sdl2.SDLK_F3, keys)
    g.to_spawn = 0
    for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
    a = g.zombies[0]; g.hero.x, g.hero.y = 470.0, 420.0; a.x, a.y = 515.0, 420.0; a.state = "idle"; a.heading = 0
    for _ in range(30): aim(g, 600, 420); g.update(1 / 60, keys)
    g.click(*g.aim)
    for i in range(9): aim(g, 600, 420); g.update(1 / 60, keys)
    shot(g, f"real_{int(real)}_hit")
    for i in range(60): aim(g, 600, 420); g.update(1 / 60, keys)
    shot(g, f"real_{int(real)}_after")
    print("real", real, "stains", len(g.stains), "alive", a.alive, "slow possible", settings.EXPOSURE_ON)
pico2d.close_canvas()
ims = [Image.open(f"{out}/real_{r}_{k}.png") for r in (0, 1) for k in ("hit", "after")]
W, H = settings.WIDTH // 2, settings.HEIGHT // 2
sheet = Image.new("RGB", (W * 2 + 10, H * 2 + 10))
for i, im in enumerate(ims): sheet.paste(im.resize((W, H)), ((i % 2) * (W + 10), (i // 2) * (H + 10)))
sheet.save(f"{out}/realism.png"); print("ok")
