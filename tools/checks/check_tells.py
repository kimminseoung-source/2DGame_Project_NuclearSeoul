"""Attack tells: the faint red wedge while an infected winds up. Drawn red pixels must lie in the claw's
real wedge (drawn = logic); start / middle / counter window; out-of-reach is sparser; draw time."""
import sys, ctypes, random, time; sys.path.insert(0, "src")
from math import atan2, cos, sin, pi, hypot
import pico2d, sdl2, play, settings, ui, attack_tells as at
from infected import COUNTER_WINDOW
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
for _ in range(5): g.update(1 / 60, keys)
z = next(z for z in g.zombies if z.alive)
g.zombies[:] = [z]
k = g.zoom * settings.DOT
COLS = {at.EDGE, at.FILL, at.EDGE_NOW, at.FILL_NOW}
def setup(dist, fraction):
    z.x, z.y = g.hero.x + dist, g.hero.y + 6
    z.heading = atan2(g.hero.y - z.y, g.hero.x - z.x)
    z.state, z.timer = "windup", z.windup * (1 - fraction)
def frame():
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas(); return im
def red_pixels(im):
    px = im.load(); out = []
    for sy in range(H):
        for sx in range(W):
            if px[sx, sy] in COLS: out.append((sx, sy))
    return out
shots, report = [], []
for name, dist, f in (("시작", 26, 0.05), ("중간", 26, 0.5), ("받아치기 때", 26, 1 - COUNTER_WINDOW / z.windup * 0.5),
                      ("범위 밖 (멀리)", 60, 0.5)):
    setup(dist, f)
    for _ in range(1): pass
    g.dev.tells = False; base = frame(); g.dev.tells = True
    im = frame()
    a, b = im.load(), base.load()
    pts = [(sx, sy) for sy in range(H) for sx in range(W) if a[sx, sy] != b[sx, sy]]   # what the tells drew
    x, y, r, ang, half = at.wedge_of(z)
    bad, worst = 0, 0.0
    dotpx = g.zoom                                     # screen px per art pixel
    for sx, sy in pts:
        wx, wy = sx / k + g.cam[0], (H - 1 - sy) / k + g.cam[1]
        d = hypot(wx - x, wy - y)
        off = abs((atan2(wy - y, wx - x) - ang + pi) % (2 * pi) - pi)
        out = max(0.0, d - r, d * max(0.0, off - half))   # world units outside the wedge
        if out * k > dotpx:                             # more than one art pixel outside
            bad += 1
        worst = max(worst, out * k / dotpx)
    report.append(f"{name}: 빨간 점 {len(pts)}개, 1도트 넘게 벗어남 {bad}개(가장 멀리 {worst:.1f}도트), 받아치기 때 {z.timer <= COUNTER_WINDOW}, 맞을 수 있음 {at.can_hit(z, g.hero.x, g.hero.y)}")
    hx, hy = (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
    shots.append((name, im.crop((int(hx) - 120, int(hy) - 110, int(hx) + 160, int(hy) + 70))))
# draw time with and without
setup(26, 0.5)
def timed(n=40):
    t0 = time.perf_counter()
    for _ in range(n): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    return (time.perf_counter() - t0) / n * 1000
on = timed(); g.dev.tells = False; off = timed(); g.dev.tells = True
report.append(f"한 프레임 그리기: 예고 켬 {on:.2f}ms, 끔 {off:.2f}ms")
print("\n".join(report))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 15)
sheet = Image.new("RGB", (len(shots) * 280, 210), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for i, (n, im) in enumerate(shots):
    sheet.paste(im, (i * 280, 26)); d.text((i * 280 + 6, 4), n, font=f, fill=(220, 200, 140))
sheet.save("docs/planning/attack_tells.png")
pico2d.close_canvas(); print("ok")
