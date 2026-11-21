"""F5: infected sight cones and the hero's noise rings."""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, infected
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game()
g.zoom = g.zoom_shown = settings.ZOOM_STEPS[0]
for _ in range(3): g.update(1 / 60, keys)
g.key_down(sdl2.SDLK_F5, keys); print("sight overlay", g.dev.sight)
g.dev.freeze = True
g.make_noise(infected.NOISE_SLASH); g.make_noise(infected.NOISE_STEP)
print("rings", [n[2] for n in g.dev.noises])
for _ in range(12): g.update(1 / 60, keys)
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/dev_senses.png")
for _ in range(60): g.update(1 / 60, keys)
print("rings after 1 s:", len(g.dev.noises))
pico2d.close_canvas(); print("ok")

