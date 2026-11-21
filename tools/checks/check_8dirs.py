"""3D hero, 8 directions: the attack uses each direction's own pictures (no borrowing); a board of
aim -> wind-up -> hit -> recover per direction, and aim-walking. BUSAN_HERO=hero_3d BUSAN_AREA=arena."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, weapons, character_look
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
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
g.zombies.clear()
look = g.hero_look
# 1. own direction for every aim
own = []
for i, d in enumerate(character_look.DIRS):
    kp = look.key_pose("chop", 0.2, 0.5, i * pi / 4)
    own.append(kp[3] == d if kp else False)
print("attack uses its own direction:", all(own), own)
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
def aim_at(a):
    x, y = hp(); g.aim = (x + cos(a) * 200, y - sin(a) * 200)
def shot():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    cx, cy = hp(); return im.crop((int(cx) - 70, int(cy) - 105, int(cx) + 70, int(cy) + 30))
g.hero.weapon = weapons.WEAPONS["pipe"]
for _ in range(5): g.update(1 / 60, keys)
names = {"east": "동", "north-east": "북동", "north": "북", "north-west": "북서", "west": "서",
         "south-west": "남서", "south": "남", "south-east": "남동"}
cols = []
for i, d in enumerate(character_look.DIRS):
    a = i * pi / 4
    shots = []
    g.hero.start_ready()
    for _ in range(10): aim_at(a); g.update(1 / 60, keys); g.hero.ready = 1.0
    shots.append(shot())
    g.hero.slash_cooldown = 0; g.hero.stamina.value = 999
    g.hero.start_slash(g.hero.x + cos(a) * 50, g.hero.y + sin(a) * 50)
    seen, n = [], 0
    while g.hero.slash and n < 120:
        aim_at(a); g.update(1 / 60, keys); s = g.hero.slash
        if s:
            kp = look.key_pose(s["pose"], s["time"] / s["whole"], s["hit_at"] / s["whole"], s["angle"])
            if kp and (not seen or seen[-1] is not kp[0]):
                seen.append(kp[0]); shots.append(shot())
        n += 1
    for _ in range(15): g.update(1 / 60, keys)
    # aim-walking toward the aim
    keys[sdl2.SDL_SCANCODE_D] = 1 if cos(a) > 0.3 else 0; keys[sdl2.SDL_SCANCODE_A] = 1 if cos(a) < -0.3 else 0
    keys[sdl2.SDL_SCANCODE_W] = 1 if sin(a) > 0.3 else 0; keys[sdl2.SDL_SCANCODE_S] = 1 if sin(a) < -0.3 else 0
    g.hero.start_ready()
    for m in range(14): aim_at(a); g.update(1 / 60, keys); g.hero.ready = 1.0
    shots.append(shot())
    for key in (sdl2.SDL_SCANCODE_D, sdl2.SDL_SCANCODE_A, sdl2.SDL_SCANCODE_W, sdl2.SDL_SCANCODE_S): keys[key] = 0
    g.hero.ready = None
    for _ in range(10): g.update(1 / 60, keys)
    g.hero.x, g.hero.y = 500, 320
    for _ in range(3): g.update(1 / 60, keys)
    cols.append((names[d], shots))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
rows = max(len(s) for _, s in cols)
sheet = Image.new("RGB", (60 + len(cols) * 140, 24 + rows * 135), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for r, lab in enumerate(["조준", "준비", "치기", "회복", "조준 걷기"][:rows]):
    d.text((4, 24 + r * 135 + 60), lab, font=f, fill=(220, 200, 140))
for c, (lab, shots) in enumerate(cols):
    d.text((60 + c * 140 + 55, 4), lab, font=f, fill=(220, 200, 140))
    for r, im in enumerate(shots): sheet.paste(im, (60 + c * 140, 24 + r * 135))
sheet.save("docs/planning/hero3d_8dirs_attack.png")
pico2d.close_canvas(); print("ok", [len(s) for _, s in cols])
