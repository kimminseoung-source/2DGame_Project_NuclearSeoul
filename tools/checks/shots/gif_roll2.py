"""Animated GIF: the three dodge looks, east, every frame (plus a still before and after)."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dodge_fx, stamina
from PIL import Image, ImageDraw, ImageFont
from pico2d import pico2d as canvas
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(2)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.zombies[:] = []
for _ in range(5): g.update(1 / 60, keys)
g.hero.x += 140
k = g.zoom * settings.DOT
n = int(settings.ROLL_TIME * 60) + 14
f = ImageFont.truetype("malgun.ttf", 16)
strips = {}
for st in ("roll", "roll_spin"):
    dodge_fx.style = st
    h = g.hero; g.effects.clear(); h.roll = 0; h.roll_cooldown = 0; h.trail = dodge_fx.Trail()
    h.stamina.value = stamina.MAX; h.stamina.rest_in = 0
    x0 = h.x
    g.update(1 / 60, keys)
    cam0 = tuple(g.cam)
    frames = []
    for i in range(n + 8):
        if i == 8:
            keys[sdl2.SDL_SCANCODE_D] = 1; g.key_down(sdl2.SDLK_SPACE, keys); keys[sdl2.SDL_SCANCODE_D] = 0
        g.update(1 / 60, keys)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        hx, hy = (x0 - cam0[0]) * k, H - 1 - (h.y - cam0[1]) * k
        dx = (g.cam[0] - cam0[0]) * k                  # follow the camera so the floor stays put
        frames.append(im.crop((int(hx - dx) - 90, int(hy) - 120, int(hx - dx) + 260, int(hy) + 24)))
    strips[st] = frames
    h.x = x0
cw, ch = strips["roll"][0].size
out = []
for i in range(len(strips["roll"])):
    fr = Image.new("RGB", (cw, (ch + 22) * 2), (30, 30, 34)); d = ImageDraw.Draw(fr)
    for r, st in enumerate(("roll", "roll_spin")):
        d.text((6, r * (ch + 22) + 2), dodge_fx.STYLE_NAMES[st], font=f, fill=(240, 230, 200))
        fr.paste(strips[st][i], (0, r * (ch + 22) + 22))
    out.append(fr.resize((fr.width * 2, fr.height * 2), Image.NEAREST))
out[0].save(sys.argv[1], save_all=True, append_images=out[1:], duration=[20] * len(out[:-1]) + [600], loop=0)
print("frames", len(out), out[0].size)
