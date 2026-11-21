"""Key-pose chop toward the south-east at an infected, in the game: key poses on vs off, as a GIF."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, weapons, character_look, slash_fx
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
W, H = settings.WIDTH, settings.HEIGHT


def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


def record(on):
    character_look.DirLook.key_poses = True
    slash_fx.SpriteFx.on = on
    random.seed(3)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.daylight.hour = 14
    g.hero.weapon = weapons.WEAPONS["pipe"] if "pipe" in weapons.WEAPONS else next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
    z = g.zombies[0]
    for other in g.zombies[1:]: other.x, other.y = -5000, -5000
    g.hero.x, g.hero.y = 400, 500
    z.x, z.y = g.hero.x + 34, g.hero.y - 30
    k = g.zoom * settings.DOT
    def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
    for _ in range(5):
        x, y = hp(); g.aim = (x + 200, y + 200); g.update(1 / 60, keys)
    g.hero.start_slash(z.x, z.y)
    frames = []
    for n in range(54):
        x, y = hp(); g.aim = (x + 200, y + 200); g.update(1 / 60, keys)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        cx, cy = hp()
        frames.append(im.crop((int(cx) - 150, int(cy) - 170, int(cx) + 170, int(cy) + 90)))
    return frames


a = record(False)
b = record(True)
slash_fx.SpriteFx.on = True
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 16)
out = []
for fa, fb in zip(a, b):
    p = Image.new("RGB", (2 * 320 + 16, 260 + 28), (20, 20, 22)); d = ImageDraw.Draw(p)
    p.paste(fa, (0, 28)); p.paste(fb, (336, 28))
    d.text((6, 6), "핵심 자세 2장 (효과 그림 없음)", font=f, fill=(220, 220, 220))
    d.text((342, 6), "핵심 자세 2장 + 베기 궤적·타격 효과", font=f, fill=(240, 200, 120))
    out.append(p)
out[0].save("docs/planning/keypose_fx.gif", save_all=True, append_images=out[1:], duration=33, loop=0)
strip = Image.new("RGB", (8 * 160, 2 * 130), (20, 20, 22))
for j, n in enumerate(range(0, 48, 6)):
    strip.paste(a[n].resize((160, 130)), (j * 160, 0)); strip.paste(b[n].resize((160, 130)), (j * 160, 130))
strip.save("docs/planning/keypose_fx_strip.png")
pico2d.close_canvas(); print("ok")
