"""Full screen at night, the hero looking straight at a wreck: is the cone lit and the shadow behind it?"""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
i = area.BLOCK_LOOKS.index("wreck_1"); l, b, r, t = area.BLOCKS[i]
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.daylight.hour = float(sys.argv[1]) if len(sys.argv) > 1 else 22
for z in g.zombies: z.state, z.timer = "dead", 99
g.hero.x, g.hero.y = l - 150, (b + t) / 2 - 22
for _ in range(40): g.update(1 / 60, keys)
k = g.zoom * settings.DOT
g.aim = (((l + r) / 2 - g.cam[0]) * k, settings.HEIGHT - ((b + t) / 2 + 22 - g.cam[1]) * k)
for _ in range(3): g.update(1 / 60, keys)
print("look", round(g.look, 3), "cam", [round(c) for c in g.cam], "hero", round(g.hero.x), round(g.hero.y), "aim", [round(a) for a in g.aim])
pico2d.clear_canvas(); g.draw()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
pico2d.update_canvas()
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save(f"docs/planning/cone_wreck_{int(g.daylight.hour)}.png")
pico2d.close_canvas(); print("ok")
