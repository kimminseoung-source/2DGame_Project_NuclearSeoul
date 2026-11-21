import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.note_folded = True
g.aim = (settings.WIDTH / 2 + 300, settings.HEIGHT / 2 + 40)
for _ in range(30): g.update(1 / 60, keys)
print([(round(z.x), round(z.y), z.prone, z.state) for z in g.zombies])
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/alley_start_zombies.png")
