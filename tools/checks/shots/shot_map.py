"""The real-size area: at the start, at a door outside, inside the same building; frame time."""
import sys, random, time, json; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
data = json.loads((area.AREA_PATH / "area.json").read_text(encoding="utf-8"))


def grab(g):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp")
    return Image.open("docs/planning/_t.bmp").convert("RGB").resize((640, 360))


random.seed(5); g = play.Game(); g.to_spawn = 0
g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}
# a building with a south door, the hero 1.5 m outside it, then 1.5 m inside
bi, bd = max(((i, b) for i, b in enumerate(data["buildings"]) if b["doors"]),
             key=lambda ib: -abs(ib[1]["doors"][0][1] - 1280) - abs(ib[1]["doors"][0][0] - 2900))
dx, dy = bd["doors"][0]
out_pt = next((dx + ox, dy + oy) for ox, oy in ((0, -48), (0, 48), (48, 0), (-48, 0))
              if area.building_at(dx + ox, dy + oy) is None and not area.blocked(dx + ox, dy + oy))
in_pt = (2 * dx - out_pt[0], 2 * dy - out_pt[1])
shots = []
l, b, r, t = bd["box"]
inner = ((l + r) / 2 - 40, b + 90)
for label, (x, y), look in (("시작 (길 끝에서 들어옴)", area.HERO_START, (0, 1)), ("집 문 앞 (밖)", out_pt, (0, 1)),
                            ("집 안 (지붕이 걷힘)", inner, (0.3, 1))):
    g.hero.x, g.hero.y = x, y
    g.aim = (settings.WIDTH / 2 + look[0] * 300, settings.HEIGHT / 2 - look[1] * 300)
    for _ in range(20): g.update(1 / 60, keys)
    shots.append((label + f" in={area.building_at(g.hero.x, g.hero.y)}", grab(g)))
t = time.perf_counter()
for _ in range(60):
    g.update(1 / 60, keys); pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
print("frame ms", round((time.perf_counter() - t) / 60 * 1000, 1), "| blocks", len(area.BLOCKS),
      "| door building", bi, "out", out_pt, "in", in_pt)
import os; os.remove("docs/planning/_t.bmp")
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 16)
sheet = Image.new("RGB", (640 * 3, 390), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t_, im) in enumerate(shots):
    sheet.paste(im, (i * 640, 30)); d.text((i * 640 + 8, 6), t_, font=font, fill=(196, 170, 92))
sheet.save("docs/planning/map_seoul_station_ingame.png")
