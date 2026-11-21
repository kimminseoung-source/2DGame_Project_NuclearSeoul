"""Walk south with the PixelLab hero: frames over time, saved as a GIF and a strip."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(g):
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(1)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.daylight.hour = 14
for z in g.zombies: z.x, z.y = -5000, -5000
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, settings.HEIGHT - 1 - (g.hero.y - g.cam[1]) * k
keys[sdl2.SDL_SCANCODE_S] = 1
frames = []
for i in range(48):
    x, y = hp(); g.aim = (x, y + 300); g.update(1 / 60, keys)
    if i % 2 == 0:
        x, y = hp(); im = shot(g); frames.append(im.crop((int(x) - 90, int(y) - 150, int(x) + 90, int(y) + 30)))
    else:
        pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
print("moved to", round(g.hero.x), round(g.hero.y), "frames", len(frames))
frames[0].save("docs/planning/hero_walk_south.gif", save_all=True, append_images=frames[1:], duration=33, loop=0)
strip = Image.new("RGB", (180 * 8, 180)); [strip.paste(f, (i * 180, 0)) for i, f in enumerate(frames[:16:2])]
strip.save("docs/planning/hero_walk_south_strip.png")
pico2d.close_canvas(); print("ok")
