"""Sneaking east in the game: now vs D, side by side, every frame (GIF) + which pictures were used."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, character_look
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
f = ImageFont.truetype("malgun.ttf", 16)
strips, used = {}, {}
for anim in ("sneak", "sneak_sf", "sneak_sw"):
    character_look.DirLook.SNEAK_ANIM = anim
    random.seed(2)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.zombies[:] = []
    for _ in range(5): g.update(1 / 60, keys)
    h = g.hero; h.x, h.y = 470, 260
    k = g.zoom * settings.DOT
    keys[sdl2.SDL_SCANCODE_D] = 1; keys[sdl2.SDL_SCANCODE_LCTRL] = 1
    frames, seen = [], set()
    for i in range(72):
        g.update(1 / 60, keys)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
        frames.append(im.crop((int(hx) - 70, int(hy) - 120, int(hx) + 70, int(hy) + 22)))
    keys[sdl2.SDL_SCANCODE_D] = 0; keys[sdl2.SDL_SCANCODE_LCTRL] = 0
    pic = h.look.picture("sneak", 0.0, 0.0)
    used[anim] = pic[2] if pic else None
    strips[anim] = frames
print("pictures used:", used)
cw, ch = strips["sneak"][0].size
labels = {"sneak": "지금", "sneak_sf": "Sneaking Forward", "sneak_sw": "Sneak Walk"}
out = []
for i in range(len(strips["sneak"])):
    fr = Image.new("RGB", (cw * 3, ch + 22), (30, 30, 34)); d = ImageDraw.Draw(fr)
    for c, anim in enumerate(("sneak", "sneak_sf", "sneak_sw")):
        d.text((c * cw + 6, 2), labels[anim], font=f, fill=(240, 230, 200))
        fr.paste(strips[anim][i], (c * cw, 22))
    out.append(fr.resize((fr.width * 2, fr.height * 2), Image.NEAREST))
out[0].save(sys.argv[1], save_all=True, append_images=out[1:], duration=20, loop=0)
still = Image.new("RGB", (cw * 6, ch * 3), (30, 30, 34))
for r, anim in enumerate(("sneak", "sneak_sf", "sneak_sw")):
    for c in range(6):
        still.paste(strips[anim][12 + c * 10], (c * cw, r * ch))
still.save(sys.argv[1].replace(".gif", ".png")); print("ok")
