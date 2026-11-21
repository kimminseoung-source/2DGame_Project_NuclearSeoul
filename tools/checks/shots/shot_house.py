"""The house at full size: from outside (roof on) and inside (roof off), zoom 4."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def grab(g):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp")
    return Image.open("docs/planning/_t.bmp").convert("RGB")


random.seed(5); g = play.Game(); g.to_spawn = 0; g.zombies[:] = []
g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}
g.note_folded = True
g.zoom = g.zoom_shown = 4
l, b, r, t = area.BUILDINGS[0]["box"]
shots = []
for label, (x, y), aim in (("밖: 지붕과 남쪽 벽", ((l + r) / 2 + 30, b - 70), (0.2, 1)),
                           ("안: 지붕이 걷히고 방이 보임", ((l + r) / 2 - 40, b + 100), (0.25, 1))):
    g.hero.x, g.hero.y = x, y
    g.aim = (settings.WIDTH / 2 + aim[0] * 300, settings.HEIGHT / 2 - aim[1] * 300)
    for _ in range(40): g.update(1 / 60, keys)
    shots.append((label, grab(g).crop((240, 0, 1040, 720))))
import os; os.remove("docs/planning/_t.bmp")
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 20)
sheet = Image.new("RGB", (1600, 760), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t_, im) in enumerate(shots):
    sheet.paste(im, (i * 800, 40)); d.text((i * 800 + 10, 8), t_, font=font, fill=(196, 170, 92))
sheet.save("docs/planning/house_inside_outside.png"); print(sheet.size)
