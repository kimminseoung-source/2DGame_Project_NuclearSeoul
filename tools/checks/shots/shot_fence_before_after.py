"""Devlog pictures for study note 01: the station without the fence (old rule) vs with it."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area, infected
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
OUT = "docs/study/img"


def grab(g):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


def watch_station(g):
    """The hero stands just outside the station, looking at the people (as if just arrived)."""
    l, b, r, t = g.station_zone
    g.hero.x, g.hero.y = (l + r) / 2 - 40, t + 60
    g.aim = (560, 300)


def run(fence, seed):
    random.seed(seed)
    g = play.Game(); g.dev.god = True
    if not fence:                                   # the old rule, for the picture only
        g.station_open = True
        infected.Zombie.keep_out = []
    frames, attacked = [], None
    for f in range(90 * 60):
        g.hero.x, g.hero.y = 120, 300                # the hero is far away, looting
        g.update(1 / 60, keys)
        if attacked is None and any(z.alive and z.state in ("windup", "strike") and getattr(z, "prey", g.hero) is not g.hero
                                    for z in g.zombies):
            attacked = f
        if attacked is not None and (f - attacked) % 6 == 0 and len(frames) < 50:
            watch_station(g); frames.append(grab(g).resize((640, 360)))
    watch_station(g)
    for _ in range(20): g.update(1 / 60, keys)
    alive = sum(s.alive for s in g.people)
    return g, grab(g), frames, alive, (attacked or 0) / 60


g, before, frames, alive_b, when = run(False, 4)
print("no fence: first attack on the people at", round(when, 1), "s | alive", alive_b, "/ 3 | gif frames", len(frames))
if frames:
    frames[0].save(f"{OUT}/01_before.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)
g, after, _, alive_a, _ = run(True, 4)
print("fence: alive", alive_a, "/ 3")
font = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 22)
sheet = Image.new("RGB", (1280, 400), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for i, (im, label) in enumerate(((before, f"전: 울타리 없음 · 도착하면 {alive_b}/3"), (after, f"후: 울타리 · 도착하면 {alive_a}/3"))):
    sheet.paste(im.resize((640, 360)), (i * 640, 40))
    d.text((i * 640 + 10, 8), label, font=font, fill=(226, 90, 70) if i == 0 else (120, 200, 120))
sheet.save(f"{OUT}/01_before_after.png")
pico2d.close_canvas(); print("ok")
