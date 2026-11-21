"""F4 attack motion x picture count for the 3D hero: film a south-east chop for each, one board.
Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena through run_hidden.py from the project root."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, weapons, dev_tools, character_look
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
random.seed(1)
g = play.Game()
g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
for _ in range(5): g.update(1 / 60, keys)
names = dev_tools._variants(g)
print("F4 variants", names)
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
rows = []
ang = -pi / 4
for v in names[1:]:
    for cnt in (2, 3, 0):
        character_look.DirLook.variant, character_look.DirLook.key_count = v, cnt
        for _ in range(40): g.update(1 / 60, keys)
        for _ in range(4):
            x, y = hp(); g.aim = (x + cos(ang) * 200, y - sin(ang) * 200); g.update(1 / 60, keys)
        g.hero.slash_cooldown = 0; g.hero.stamina.value = 999
        g.hero.start_slash(g.hero.x + cos(ang) * 50, g.hero.y + sin(ang) * 50)
        shots, seen = [], set()
        for n in range(66):
            x, y = hp(); g.aim = (x + cos(ang) * 200, y - sin(ang) * 200); g.update(1 / 60, keys)
            s = g.hero.slash
            if s:
                kp = g.hero_look.key_pose("chop", s["t"] if "t" in s else 0, s.get("hit_at", 0.5), ang) if False else None
            pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
            if n % 5 == 0:
                cx, cy = hp(); shots.append(im.crop((int(cx) - 80, int(cy) - 120, int(cx) + 80, int(cy) + 40)))
        rows.append((f"{dev_tools.VARIANT_NAMES[v]} / {dev_tools.COUNT_NAMES[cnt]}", shots))
cols = max(len(s) for _, s in rows)
sheet = Image.new("RGB", (cols * 160 + 200, len(rows) * 160), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for r, (lab, shots) in enumerate(rows):
    d.text((6, r * 160 + 70), lab, font=f, fill=(220, 200, 140))
    for c, im in enumerate(shots): sheet.paste(im, (200 + c * 160, r * 160))
sheet.save("docs/planning/attack_variants_game.png")
# the F4 rows
character_look.DirLook.variant, character_look.DirLook.key_count = "bash", 3
g.dev.open = True if hasattr(g.dev, "open") else None
pico2d.close_canvas(); print("ok", len(rows), "rows")
