"""Night dark round the hero + vignette (src/mood_fx.py, 2026-11-26 "A+D", 밤 시야 2안).
Same scene with and without the layer: brightness near the hero / far away / in the corner, by day and
night and at low health, and what the layer costs per frame."""
import sys, ctypes, math, random, time; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, mood_fx
from pico2d import pico2d as canvas
from PIL import Image
W, H = settings.WIDTH, settings.HEIGHT
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(W, H, sync=False); ui.enable_blending()


def shot(g):
    pico2d.clear_canvas(); g.draw()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    im = Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
    sdl2.SDL_FreeSurface(s); pico2d.update_canvas()
    return im


def mean(im, box):
    c = im.crop(box).convert("L")
    return sum(c.get_flattened_data()) / (c.width * c.height)


def red_share(im, box):
    r, g, b = [sum(ch.get_flattened_data()) for ch in im.crop(box).split()]
    return r / max(1, r + g + b)


def scene(hour, hp=settings.HERO_HP):
    random.seed(1)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
    g.daylight.hour = hour
    for _ in range(20): g.update(1 / 60, keys)
    g.hero.hp = hp
    return g


real = mood_fx.draw
fails = []
out = {}
for name, hour, hp in (("낮", 12.0, 100), ("밤", 23.0, 100), ("밤 저체력", 23.0, 15)):
    g = scene(hour, hp)
    hx = (g.hero.x - g.cam[0]) * W / g.view_w; hy = H - (g.hero.y - g.cam[1]) * H / g.view_h
    near = (max(0, round(hx) - 60), max(0, round(hy) - 60), min(W, round(hx) + 60), min(H, round(hy) + 60))
    far_x = W - 140 if hx < W / 2 else 20
    far = (far_x, round(H / 2) - 60, far_x + 120, round(H / 2) + 60)
    corner = (0, 0, 120, 120)
    mood_fx.draw = lambda game: None; off = shot(g)
    mood_fx.draw = real; on = shot(g)
    r = {k: round(mean(on, b) / max(1, mean(off, b)), 3) for k, b in (("near", near), ("far", far), ("corner", corner))}
    r["corner_red"] = round(red_share(on, corner), 3)
    out[name] = r
    print(name, "hero", round(hx), round(hy), "밝기 비율(켬/끔)", r)

# by day only the vignette acts; night / day isolates the night layer
night_near = out["밤"]["near"] / out["낮"]["near"]; night_far = out["밤"]["far"] / out["낮"]["far"]
print("밤 층만: 주인공 주변", round(night_near, 3), "먼 곳", round(night_far, 3))
if night_near < 0.95: fails.append("밤에 주인공 주변이 어두워짐")
if abs(night_far - mood_fx.NIGHT_AMBIENT) > 0.08: fails.append("밤 먼 곳 밝기가 값과 다름")
if out["낮"]["corner"] > 0.95: fails.append("비네트가 안 보임")
if out["밤 저체력"]["corner_red"] <= out["밤"]["corner_red"] + 0.05: fails.append("저체력 붉은 비네트가 안 보임")
# expected night far brightness from the numbers: about NIGHT_AMBIENT
print("기대 밤 바깥 밝기", mood_fx.NIGHT_AMBIENT, "반지름", mood_fx.NIGHT_RADIUS)

g = scene(23.0, 15)
t = time.perf_counter()
for _ in range(200): mood_fx.draw(g)
ms = (time.perf_counter() - t) / 200 * 1000
print("mood_fx.draw 한 번", round(ms, 3), "ms")
if ms > 2.0: fails.append(f"너무 느림 {ms:.2f}ms")
pico2d.close_canvas()
print("FAIL: " + "; ".join(fails) if fails else "ok")
sys.exit(1 if fails else 0)
