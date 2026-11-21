"""Day / dusk / night: the same scene, how much is seen outside the cone."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
shots = []
for hour in (14.0, 19.0, 22.0):
    random.seed(1)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
    g.aim = (1100, 200)                                   # looking up-right, away from the infected behind
    g.daylight.hour = hour
    for _ in range(20): g.update(1 / 60, keys)
    seen = sum(1 for z in g.zombies if z.alive and g.vision.visible((g.hero.x, g.hero.y), g.look, z.x, z.y))
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    pico2d.update_canvas()
    shots.append((f"{g.daylight.clock} {g.daylight.name} · 보이는 피폭체 {seen}", Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")))
    print(hour, g.daylight.name, "fog", round(g.vision.fog), "infected seen", seen, "/", sum(z.alive for z in g.zombies))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 20)
sheet = Image.new("RGB", (1280, 3 * 390), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for k, (label, im) in enumerate(shots):
    sheet.paste(im.resize((640, 360)), (0, k * 390 + 30)); d.text((8, k * 390 + 4), label, font=f, fill=(196, 170, 92))
sheet.crop((0, 0, 640, 3 * 390)).save("docs/planning/daylight.png")
pico2d.close_canvas(); print("ok")
