"""The hand-made alley: the whole map (no darkness), then in game at the start, the house door, inside."""
import sys, random, json; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
A = area.AREA_PATH; D = settings.DOT
data = json.loads((A / "area.json").read_text(encoding="utf-8")); W, H = data["size"]
# 1) the whole map as built, roof on, wrecks drawn
over = Image.open(A / "ground.png").convert("RGBA")
for bd in data["buildings"]:
    l, b, r, t = bd["box"]; roof = Image.open(A / f"{bd['roof']}.png").convert("RGBA")
    over.alpha_composite(roof, (round(l * D), round((H - t) * D)))
for l, b, r, t, look in data["blocks"]:
    p = Path = None
    for folder in (A, settings.ROOT / "assets" / settings.AREA_DIR):
        f = folder / f"{look}.png"
        if look.startswith("wreck") and f.exists():
            im = Image.open(f).convert("RGBA")
            over.alpha_composite(im, (round((l + r) / 2 * D - im.width / 2), round((H - b + 3) * D) - im.height)); break
dd = ImageDraw.Draw(over)
for x, y, k in data["supplies"] + data["weapons"]:
    X, Y = x * D, (H - y) * D; dd.rectangle((X - 3, Y - 3, X + 3, Y + 3), fill=(240, 220, 120), outline=(28, 24, 22))
for x, y in data["zombie_starts"]:
    X, Y = x * D, (H - y) * D; dd.rectangle((X - 4, Y - 4, X + 4, Y + 4), fill=(120, 200, 90), outline=(28, 24, 22))
X, Y = data["hero_start"][0] * D, (H - data["hero_start"][1]) * D; dd.ellipse((X - 6, Y - 6, X + 6, Y + 6), fill=(80, 160, 255))
for (x, y), s in data["entrances"]:
    X, Y = x * D, (H - y) * D; dd.ellipse((X - 6, Y - 6, X + 6, Y + 6), fill=(210, 60, 60))
e = data["exit"]; dd.rectangle((e[0] * D, (H - e[3]) * D, e[2] * D, (H - e[1]) * D), outline=(60, 230, 120), width=2)
over = over.resize((over.width * 2, over.height * 2), Image.NEAREST)
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 18); f.size
leg = Image.new("RGB", (over.width, over.height + 40), (20, 20, 22)); ld = ImageDraw.Draw(leg); ld.fontmode = "1"
leg.paste(over, (0, 40))
ld.text((8, 10), "손으로 설계한 골목 44×32m · 파랑 시작, 빨강 좀비 들어오는 곳, 초록 좀비, 노랑 물자·무기, 초록 테두리 출구", font=f, fill=(196, 170, 92))
leg.save("docs/planning/alley_map.png")


def grab(g):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp")
    return Image.open("docs/planning/_t.bmp").convert("RGB").resize((640, 360))


random.seed(5); g = play.Game(); g.to_spawn = 0; g.note_folded = True
g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}
bd = data["buildings"][0]; dx, dy = bd["doors"][0]; l, b, r, t = bd["box"]
shots = []
for label, (x, y), look in (("시작", area.HERO_START, (1, 0.2)), ("집 문 앞", (dx, dy - 70), (0, 1)),
                            ("집 안", ((l + r) / 2 - 60, b + 120), (0.3, 1))):
    g.hero.x, g.hero.y = x, y
    g.cam = [x - g.view_w / 2, y - g.view_h / 2]; g.clamp_camera()
    g.aim = (settings.WIDTH / 2 + look[0] * 300, settings.HEIGHT / 2 - look[1] * 300)
    for _ in range(30): g.update(1 / 60, keys)
    shots.append((label, grab(g)))
import os; os.remove("docs/planning/_t.bmp")
sheet = Image.new("RGB", (640 * 3, 390), (20, 20, 22)); sd = ImageDraw.Draw(sheet); sd.fontmode = "1"
for i, (t_, im) in enumerate(shots):
    sheet.paste(im, (i * 640, 30)); sd.text((i * 640 + 8, 6), t_, font=f, fill=(196, 170, 92))
sheet.save("docs/planning/alley_ingame.png"); print("ok")
