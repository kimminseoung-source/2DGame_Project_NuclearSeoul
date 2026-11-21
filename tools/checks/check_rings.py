"""F6: walking leaves one footstep ring, not a pile; rings go after NOISE_SHOW."""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dev_tools
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game()
g.key_down(sdl2.SDLK_F6, keys); g.dev.freeze = True
keys[sdl2.SDL_SCANCODE_D] = 1
for _ in range(60): g.update(1 / 60, keys)
print("walking 1 s: rings", len(g.dev.noises), [n[2] for n in g.dev.noises])
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/dev_sounds_walk.png")
keys[sdl2.SDL_SCANCODE_D] = 0
for _ in range(int(dev_tools.NOISE_SHOW * 60) + 2): g.update(1 / 60, keys)
print("stopped", dev_tools.NOISE_SHOW, "s later: rings", len(g.dev.noises))
pico2d.close_canvas(); print("ok")
