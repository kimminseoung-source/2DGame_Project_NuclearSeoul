"""hero_3d frame counts in the game: breathing alternates; a chop goes windup -> hit -> recover -> standing.
Run with BUSAN_HERO=hero_3d BUSAN_AREA=arena through run_hidden.py from the project root."""
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
g = play.Game()
look = g.hero.look if hasattr(g.hero, "look") else g.hero_look
print("hero folder", play.HERO_PX, "breath dirs", len(look.anims.get("breath", {})), "walk frames", len(look.anims["walk"]["south"]))
# 1. breathing: two different pictures over time
a = -pi / 2
p0, p1 = look.picture("idle", 0.0, a), look.picture("idle", look.BREATH_TIME + 0.01, a)
print("breath", p0[2], p0[4], "->", p1[2], p1[4], "different:", p0[0] is not p1[0])
# 2. chop key poses over the swing
spec_dirs = list(look.keys["chop"])
seq = []
for t in [i / 40 for i in range(41)]:
    k = look.key_pose("chop", t, 0.5, -pi / 4)
    name = "stand" if not k else next(s for s in ("windup", "hit", "recover")
                                      if look.named.get(("mp_chop", "south-east", str(look.keys["chop"]["south-east"][s]["frame"]))) is k[0])
    if not seq or seq[-1] != name:
        seq.append(name)
print("chop order", seq)
# 3. picture strip: south-east chop in the arena
g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
for _ in range(5): g.update(1 / 60, keys)
ang = -pi / 4
shots = []
for _ in range(4):
    x, y = hp(); g.aim = (x + cos(ang) * 200, y - sin(ang) * 200); g.update(1 / 60, keys)
g.hero.slash_cooldown = 0; g.hero.stamina.value = 999
g.hero.start_slash(g.hero.x + cos(ang) * 50, g.hero.y + sin(ang) * 50)
for n in range(70):
    x, y = hp(); g.aim = (x + cos(ang) * 200, y - sin(ang) * 200); g.update(1 / 60, keys)
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    if n % 6 == 0:
        cx, cy = hp(); shots.append(im.crop((int(cx) - 90, int(cy) - 130, int(cx) + 90, int(cy) + 40)))
sheet = Image.new("RGB", (len(shots) * 180, 170)); [sheet.paste(s, (i * 180, 0)) for i, s in enumerate(shots)]
sheet.save("docs/planning/hero3d_chop3_game.png")
pico2d.close_canvas(); print("ok")
