import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, pixel_ui as px
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2); g = play.Game(); g.to_spawn = 0; g.zombies[:] = []
g.hero.x, g.hero.y = 90, 300
for _ in range(30): g.update(1 / 60, keys)
shots = []
for step in range(3):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp"); shots.append(Image.open("docs/planning/_t.bmp").convert("RGB").crop((0, 0, 640, 300)))
    slash_before = g.hero.slash
    g.press(30 * px.K, 15 * px.K); g.release(30 * px.K, 15 * px.K)
    print("folded", g.note_folded, "| blow started", g.hero.slash is not None and g.hero.slash is not slash_before)
    for _ in range(3): g.update(1 / 60, keys)
import os; os.remove("docs/planning/_t.bmp")
sheet = Image.new("RGB", (640 * 2, 300), (20, 20, 22))
sheet.paste(shots[0], (0, 0)); sheet.paste(shots[1], (640, 0))
sheet.save("docs/planning/note_fold_ingame.png"); print(sheet.size)
