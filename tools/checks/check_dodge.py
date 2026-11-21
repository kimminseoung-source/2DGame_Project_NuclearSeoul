"""Dodge look, east only: 3 styles x moments, hidden window; the body uses the east walking picture
(not the old side sheet); afterimages lie behind it; frame time."""
import sys, ctypes, random, time; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dodge_fx
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
from pico2d import pico2d as canvas
W, H = settings.WIDTH, settings.HEIGHT
def grab():
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * H)
    return Image.frombuffer("RGBA", (W, H), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")
random.seed(2)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
g.zombies[:] = []
for _ in range(5): g.update(1 / 60, keys)
g.hero.x += 140
k = g.zoom * settings.DOT
RT = settings.ROLL_TIME
moments = [("출발", 1), ("1/3", int(RT * 60 / 3)), ("2/3", int(RT * 60 * 2 / 3)), ("끝", int(RT * 60)), ("끝 +0.1초", int(RT * 60) + 6)]
rows = []
for st in dodge_fx.STYLES:
    dodge_fx.style = st
    shots = []
    for name, n in moments:
        g.effects.clear(); h = g.hero; h.roll = 0; h.roll_cooldown = 0; h.trail = dodge_fx.Trail()
        import stamina; h.stamina.value = stamina.MAX; h.stamina.rest_in = 0
        g.update(1 / 60, keys)
        x0 = h.x
        keys[sdl2.SDL_SCANCODE_D] = 1
        ev = sdl2.SDL_Event(); 
        g.key_down(sdl2.SDLK_SPACE, keys) if hasattr(g, "key_down") else None
        keys[sdl2.SDL_SCANCODE_D] = 0
        for _ in range(n): g.update(1 / 60, keys)
        pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas()
        pic = g.hero.look.picture("run", 0.2, 0.0)
        hx, hy = (h.x - g.cam[0]) * k, H - 1 - (h.y - g.cam[1]) * k
        shots.append((name, im.crop((int(hx) - 230, int(hy) - 130, int(hx) + 70, int(hy) + 30)), h.x - x0, len(h.trail.ghosts)))
        h.x = x0
    rows.append((st, shots))
    print(st, [(s[0], round(s[2]), s[3]) for s in shots])
# frame time with a dodge on
dodge_fx.style = "ghost_dust"
h = g.hero; h.roll = RT; h.trail = dodge_fx.Trail()
for _ in range(8): g.update(1 / 60, keys)
t0 = time.perf_counter()
for _ in range(30): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
print(f"한 프레임 그리기(잔상 {len(h.trail.ghosts)}개): {(time.perf_counter() - t0) / 30 * 1000:.2f}ms")
f = ImageFont.truetype("malgun.ttf", 18)
cw, ch = 300, 160
sheet = Image.new("RGB", (cw * len(moments) + 140, (ch + 30) * len(rows) + 10), (30, 30, 34)); d = ImageDraw.Draw(sheet)
for r, (st, shots) in enumerate(rows):
    y = 10 + r * (ch + 30)
    d.text((8, y + ch // 2), dodge_fx.STYLE_NAMES[st], font=f, fill=(240, 230, 200))
    for c, (name, im, *_ ) in enumerate(shots):
        sheet.paste(im, (130 + c * cw, y + 24))
        d.text((130 + c * cw + 4, y), name, font=f, fill=(180, 180, 190))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "docs/planning/dodge_styles_east.png")
print("ok")
