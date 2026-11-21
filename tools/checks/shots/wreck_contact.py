"""Walk the hero into a wreck from below, above and the side with F1 on: where does the body stop?"""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True; g.dev.god = True; g.dev.no_spawn = True
for z in g.zombies: z.state, z.timer = "dead", 9
g.key_down(sdl2.SDLK_F1, keys)
i = area.BLOCK_LOOKS.index(sys.argv[1] if len(sys.argv) > 1 else "wreck_1")
l, b, r, t = area.BLOCKS[i]
print("rect", (l, b, r, t))


def grab(name):
    g.cam = [(l + r) / 2 - g.view_w / 2, (b + t) / 2 - g.view_h / 2]
    pico2d.clear_canvas(); g.draw()                 # read before present: the frame just drawn
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    im = Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
    cw, ch = 520, 300
    im.crop((640 - cw // 2, 360 - ch // 2, 640 + cw // 2, 360 + ch // 2)).save(name)


shots = []
for label, start, key in (("below", ((l + r) / 2, b - 60), sdl2.SDL_SCANCODE_W), ("above", ((l + r) / 2, t + 60), sdl2.SDL_SCANCODE_S),
                          ("left", (l - 60, (b + t) / 2), sdl2.SDL_SCANCODE_D)):
    g.hero.x, g.hero.y = start
    keys[key] = 1
    for _ in range(90): g.update(1 / 60, keys)
    keys[key] = 0
    for _ in range(5): g.update(1 / 60, keys)
    print(f"from {label}: hero stops at ({g.hero.x:.0f}, {g.hero.y:.0f})")
    name = f"docs/planning/wreck_contact_{label}.png"
    grab(name); shots.append(name)
sheet = Image.new("RGB", (520 * 3, 300), (0, 0, 0))
for k, n in enumerate(shots):
    sheet.paste(Image.open(n), (k * 520, 0))
sheet.save("docs/planning/wreck_contact.png")
pico2d.close_canvas(); print("ok")
