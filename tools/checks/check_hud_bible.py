"""HUD by the art bible (2026-11-25): melee / pistol with rounds / empty pistol / items in the bag.
The rounds sit by the cursor (canvas px from the aim). Saves docs/planning/hud_bible_states.png."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, weapons, hud
import pixel_ui as px
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
random.seed(4)
g = play.Game(); g.dev.freeze = True
for _ in range(20): g.update(1 / 60, keys)
g.aim = (760, 300)
shots = []
def shot(label):
    g.update(1 / 60, keys)
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
    shots.append((label, im))
shot("근접(마체테)")
g.hero.weapon = weapons.WEAPONS["pistol"]; g.ammo = 6
shot("권총 6발")
g.ammo = 0; g.clock = 0.0
shot("권총 0발")
for k in list(g.bag)[:2]: g.bag[k] = 2
g.message, g.message_at = "붕대를 주웠다", g.clock
g.ammo = 15
shot("권총 15발 + 물건 + 알림")
cx, cy = round(760 / px.K) + 9, round(300 / px.K) + 6
print("cursor", (760, 300), "-> ammo ticks at canvas", (cx, cy), "screen", (cx * px.K, cy * px.K))
f = ImageFont.truetype("malgun.ttf", 20)
rows = []
for lab, im in shots:
    rows.append((lab, im.crop((0, 560, 1280, 720)), im.crop((700, 260, 900, 340)).resize((400, 160), Image.NEAREST)))
sheet = Image.new("RGB", (1280 + 410, len(rows) * 190), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for i, (lab, bottom, near) in enumerate(rows):
    y = i * 190
    d.text((6, y + 2), lab, font=f, fill=(230, 224, 210))
    sheet.paste(bottom, (0, y + 28)); sheet.paste(near, (1288, y + 28))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/hud_bible_states.png"); print("ok")
