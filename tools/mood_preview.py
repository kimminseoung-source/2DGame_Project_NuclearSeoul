"""Mood / UI candidates (docs/research/MOOD_UI_2026-11-25.md 4장) side by side: now vs candidate.
Game code is not changed: the default game is shot in a hidden window, effects are laid on with PIL.
The numbers in PARAMS are meant to be carried into the game as they are.
    .venv\\Scripts\\python.exe tools/checks/run_hidden.py tools/mood_preview.py"""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pico2d, sdl2
import play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont, ImageChops

OUT = ROOT / "docs/planning/mood_preview"
OUT.mkdir(parents=True, exist_ok=True)
W, H = settings.WIDTH, settings.HEIGHT
PARAMS = {
    "A_night_dark": {"ambient": 0.45, "light_radius_px": 150, "soft_px": 90, "light_tint": [255, 226, 180]},
    "D_vignette": {"start": 0.45, "strength": 0.75, "low_hp_strength": 0.70, "low_hp_color": [120, 0, 0]},
    "G_arrow": {"margin_px": 28, "size_px": 24, "color": [120, 225, 90], "only_when": "화면 밖 원거리 피폭체가 쏠 때"},
    "H_teach": {"show_first_n": 3, "hide_empty_quick_slots": True},
}
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()


def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    bmp = OUT / "_t.bmp"
    sdl2.SDL_SaveBMP(s, str(bmp).encode()); sdl2.SDL_FreeSurface(s)
    im = Image.open(bmp).convert("RGB"); bmp.unlink()
    return im


def scene(hour, hide_teach=False):
    g = play.Game()
    g.daylight.hour = hour
    g.to_spawn = 0
    if hide_teach and hasattr(g, "TEACH"):
        g.used.update(a for a, _ in g.TEACH)
    for _ in range(40):
        g.update(1 / 60, keys)
    g.daylight.hour = hour
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    return g, grab()


def to_screen(g, wx, wy):
    z = getattr(g, "zoom", 1) if play.DOT_LOOK else settings.SCALE
    return (wx - g.cam[0]) * z, H - 1 - (wy - g.cam[1]) * z


def radial(size, cx, cy, fn):
    m = Image.new("L", size)
    px = m.load()
    for y in range(0, size[1], 2):
        for x in range(0, size[0], 2):
            v = fn(math.hypot(x - cx, y - cy))
            for dy in (0, 1):
                for dx in (0, 1):
                    if x + dx < size[0] and y + dy < size[1]:
                        px[x + dx, y + dy] = v
    return m


def night_dark(im, hx, hy):
    p = PARAMS["A_night_dark"]
    r, s, amb = p["light_radius_px"], p["soft_px"], p["ambient"]
    def f(d):
        t = 0 if d < r else min(1, (d - r) / s)
        return round(255 * (1 - t * (1 - amb)))
    mask = radial(im.size, hx, hy, f)
    lit = ImageChops.multiply(im, Image.merge("RGB", [mask] * 3))
    warm = Image.new("RGB", im.size, tuple(p["light_tint"]))
    glow = radial(im.size, hx, hy, lambda d: round(40 * max(0, 1 - d / r)))
    return Image.composite(ImageChops.multiply(lit, warm), lit, glow)


def vignette(im, low_hp=False):
    p = PARAMS["D_vignette"]
    st = p["low_hp_strength"] if low_hp else p["strength"]
    R = math.hypot(W / 2, H / 2)
    mask = radial(im.size, W / 2, H / 2, lambda d: round(255 * st * max(0, (d / R - p["start"]) / (1 - p["start"])) ** 1.5))
    col = tuple(p["low_hp_color"]) if low_hp else (0, 0, 0)
    return Image.composite(Image.new("RGB", im.size, col), im, mask)


def arrow(im, g, hx, hy):
    p = PARAMS["G_arrow"]
    tx, ty = hx + 900, hy - 260                      # an imagined spitter off the right edge
    a = math.atan2(ty - hy, tx - hx)
    m = p["margin_px"]
    k = min((W / 2 - m) / max(1e-6, abs(math.cos(a))), (H / 2 - m) / max(1e-6, abs(math.sin(a))))
    ex, ey = W / 2 + math.cos(a) * k, H / 2 + math.sin(a) * k
    s = p["size_px"]
    pts = [(ex + math.cos(a) * s, ey + math.sin(a) * s),
           (ex + math.cos(a + 2.5) * s, ey + math.sin(a + 2.5) * s),
           (ex + math.cos(a - 2.5) * s, ey + math.sin(a - 2.5) * s)]
    im = im.copy(); d = ImageDraw.Draw(im)
    d.polygon(pts, fill=tuple(p["color"]), outline=(20, 40, 15))
    return im, (round(ex), round(ey))


def font(n=22):
    for f in ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/gulim.ttc"):
        try:
            return ImageFont.truetype(f, n)
        except OSError:
            pass
    return ImageFont.load_default()


def pair(left, right, title, label_l, label_r, name):
    w, h = W // 2, H // 2
    sheet = Image.new("RGB", (w * 2 + 12, h + 44), (18, 18, 20))
    d = ImageDraw.Draw(sheet); fn = font(20)
    d.text((8, 8), f"{title}   왼쪽: {label_l}   오른쪽: {label_r}", fill=(235, 235, 235), font=fn)
    sheet.paste(left.resize((w, h)), (0, 44)); sheet.paste(right.resize((w, h)), (w + 12, 44))
    sheet.save(OUT / name)
    return str((OUT / name).relative_to(ROOT)).replace("\\", "/")


def main():
    pico2d.open_canvas(W, H, sync=False); ui.enable_blending()
    out = {}
    gd, day = scene(12.0)
    gn, night = scene(23.0)
    _, night_clean = scene(23.0, hide_teach=True)
    pico2d.close_canvas()
    hx = (gn.hero.x - gn.cam[0]) * W / gn.view_w; hy = H - (gn.hero.y - gn.cam[1]) * H / gn.view_h   # camera stops at map edges
    out["hero_screen"] = [round(hx), round(hy)]
    a = night_dark(night, hx, hy)
    out["A"] = pair(night, a, "A 밤 어둠", "지금(밤 23시)", "후보: 주인공 주변만 밝음", "A_night_dark.png")
    out["D"] = pair(day, vignette(day), "D 비네트", "지금(낮)", "후보: 가장자리 은은히", "D_vignette.png")
    out["D_lowhp"] = pair(day, vignette(day, low_hp=True), "D 비네트(체력 낮음)", "지금", "후보: 붉고 진하게", "D_vignette_lowhp.png")
    g_im, pos = arrow(day, gd, W / 2, H / 2)
    out["G"] = pair(day, g_im, "G 화면 밖 화살표", "지금", "후보: 오른쪽 위 초록 화살표", "G_offscreen_arrow.png"); out["G_pos"] = pos
    out["H"] = pair(night, night_clean, "H 안내 정리", "지금", "후보: 머리 위 안내 숨김", "H_teach_hidden.png")
    out["ALL"] = pair(night, vignette(a), "A+D 함께(밤)", "지금", "후보: 어둠+비네트", "AD_together.png")
    out["diff_H_mean"] = round(sum(ImageChops.difference(night, night_clean).convert("L").get_flattened_data()) / (W * H), 3)
    out["params"] = PARAMS
    (OUT / "params.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "params"}, ensure_ascii=False))


main()
