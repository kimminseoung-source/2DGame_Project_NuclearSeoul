"""Default attack of the 3D hero: aim (bat) -> let go -> sword hit -> held blade. Swung weapons,
south-east and south. Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena through run_hidden.py."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, weapons
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
g = play.Game(); g.dev.freeze = True
look = g.hero_look
print("default attack", look.keys.get("default_variant"))
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
def aim_at(a):
    x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200)
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    cx, cy = hp(); return im.crop((int(cx) - 80, int(cy) - 110, int(cx) + 80, int(cy) + 30))
for _ in range(5): g.update(1 / 60, keys)
rows = []
for wk in ("pipe", "machete", "bat", "axe"):
    w = weapons.WEAPONS[wk]; g.hero.weapon = w
    for a, dn in ((-pi / 4, "남동"), (-pi / 2, "정면")):
        shots = []
        g.hero.start_ready()
        for _ in range(12): aim_at(a); g.update(1 / 60, keys); g.hero.ready = 1.0
        shots.append(shot())                                      # aiming
        g.hero.slash_cooldown = 0; g.hero.stamina.value = 999
        g.hero.start_slash(g.hero.x + cos(a) * 50, g.hero.y + sin(a) * 50)
        seen, n = [], 0
        while g.hero.slash and n < 120:
            aim_at(a); g.update(1 / 60, keys)
            s = g.hero.slash
            if s:
                kp = look.key_pose(s["pose"], s["time"] / s["whole"], s["hit_at"] / s["whole"], s["angle"])
                tag = kp[0] if kp else None
                if tag is not None and (not seen or seen[-1] is not tag):
                    seen.append(tag); shots.append(shot())
            n += 1
        for _ in range(20): g.update(1 / 60, keys)
        shots.append(shot())                                      # back to standing
        rows.append((f"{w['name']} {dn}", shots))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
cols = max(len(s) for _, s in rows)
sheet = Image.new("RGB", (120 + cols * 160, len(rows) * 140 + 24), (20, 20, 22)); d = ImageDraw.Draw(sheet)
d.text((120, 2), "조준 | 준비 | 치기 | 회복 | 서 있기", font=f, fill=(200, 200, 200))
for r, (lab, shots) in enumerate(rows):
    d.text((6, 24 + r * 140 + 60), lab, font=f, fill=(220, 200, 140))
    for c, im in enumerate(shots): sheet.paste(im, (120 + c * 160, 24 + r * 140))
sheet.save("docs/planning/samurai_game.png")
pico2d.close_canvas(); print("ok", [len(s) for _, s in rows])
