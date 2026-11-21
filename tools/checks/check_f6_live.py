"""F6 as a player meets it: press F6, stand, walk, sneak, swing - what rings are on screen each moment?"""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dev_tools
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
for _ in range(10): g.update(1 / 60, keys)
g.key_down(sdl2.SDLK_F6, keys)
print("F6 on:", g.dev.sounds)


def grab():
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


shots = []
def step(label, frames, setkeys=(), action=None):
    for k in setkeys: keys[k] = 1
    if action: action()
    for _ in range(frames): g.update(1 / 60, keys)
    print(f"{label:22s} rings {[ (n[2], round(n[3], 2)) for n in g.dev.noises]}")
    shots.append((label, grab()))
    for k in setkeys: keys[k] = 0


step("standing", 30)
step("walking (0.5 s)", 30, (sdl2.SDL_SCANCODE_D,))
step("stopped 0.2 s", 12)
step("stopped 0.5 s", 18)
step("sneaking", 30, (sdl2.SDL_SCANCODE_D, sdl2.SDL_SCANCODE_LCTRL))
step("swing, 0.15 s later", 9, action=lambda: (g.press(900, 360), g.release(900, 360)))
step("swing, 0.4 s later", 15)
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 18)
sheet = Image.new("RGB", (1280, 4 * 250), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for k, (label, im) in enumerate(shots):
    x, y = (k % 2) * 640, (k // 2) * 250
    sheet.paste(im.resize((640, 360)).crop((0, 60, 640, 280)), (x, y + 28)); d.text((x + 8, y + 4), label, font=f, fill=(196, 170, 92))
sheet.save("docs/planning/f6_live.png")
pico2d.close_canvas(); print("ok")
