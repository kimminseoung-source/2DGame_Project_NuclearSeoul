"""The game as it looks now (2026-11-25 분위기·UI 조사): full screens at noon, dusk and night with an
infected close, for comparing against the mood/UI research. Saves docs/planning/mood_now_<hour>.png."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui
from PIL import Image
from pico2d import pico2d as canvas
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
for hour in (12.0, 18.5, 22.0):
    random.seed(4)
    g = play.Game(); g.dev.freeze = True
    for _ in range(30): g.update(1 / 60, keys)
    g.daylight.hour = hour
    z = next((z for z in g.zombies if z.alive), None)
    if z: z.x, z.y = g.hero.x + 70, g.hero.y + 20
    for _ in range(5): g.update(1 / 60, keys)
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    im.save(f"docs/planning/mood_now_{int(hour)}.png"); print("saved", hour, g.daylight.name)
