"""Paper doll check: the weapon drawn at the hand point (drawn = logic), behind the body facing
north, swing angles, frame time; plus a picture sheet (8 directions x 4 weapons, walk, swing)."""
import sys, ctypes, random, time; sys.path.insert(0, "src")
from math import cos, sin, pi, degrees, hypot
import pico2d, sdl2, play, settings, ui, weapons, character_look
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


def shot(g):
    pico2d.clear_canvas(); g.draw(); im = grab(); pico2d.update_canvas(); return im


random.seed(1)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.daylight.hour = 14
for z in g.zombies: z.x, z.y = -5000, -5000
look = g.hero_look
k = g.zoom * settings.DOT
def hp(): return (g.hero.x - g.cam[0]) * k, H - 1 - (g.hero.y - g.cam[1]) * k
def to_screen(px, py):            # look coordinates (world - camera) -> screen pixel (y down)
    return px * k, H - 1 - py * k
def aim_at(a):
    for _ in range(3):
        x, y = hp(); g.aim = (x + 260 * cos(a), y - 260 * sin(a)); g.update(1 / 60, keys)


# 1) drawn = logic: draw only the weapon (body hidden) on a white screen and find its grip.
def weapon_only_grip(g):
    """Screen pixel of the weapon end nearest the hand, drawing the weapon alone on white."""
    pico2d.clear_canvas()
    sdl2.SDL_SetRenderDrawColor(canvas.renderer, 255, 255, 255, 255); sdl2.SDL_RenderClear(canvas.renderer)
    pic = look.picture("idle", 0, g.hero.angle)
    image, under, key, d, i = pic
    kk = look.k
    x, feet = g.hero.x - g.cam[0], g.hero.y - g.cam[1]
    cy = feet - under / kk + image.h / kk / 2
    pt = look.hand(key, d, i)
    gx = x + (pt[0] + 0.5 - image.w / 2) / kk; gy = cy + (image.h / 2 - pt[1] - 0.5) / kk
    ang, _ = look.weapon_angle("idle", 0, None, g.hero.angle, d)
    # the play canvas is drawn at DOT then blown up: draw through the game's own path instead
    return gx, gy, ang
errors = []
for i in range(8):
    a = i * pi / 4
    aim_at(a)
    im = shot(g)
    hand = g.hero.hand
    sx, sy = to_screen(*hand)
    # the weapon pixels around the hand: grey/steel or wood colours not in the body palette are hard to
    # separate, so compare with the same frame drawn without a weapon
    g.hero.weapon_backup = g.hero.weapon
    held = g.hero.held
    g.hero.held = lambda: None
    bare = shot(g)
    g.hero.held = held
    diff = [(x, y) for y in range(int(sy) - 60, int(sy) + 60) for x in range(int(sx) - 60, int(sx) + 60)
            if 0 <= x < W and 0 <= y < H and im.getpixel((x, y)) != bare.getpixel((x, y))]
    if not diff:
        errors.append((degrees(a), "no weapon pixels")); continue
    near = min(hypot(x - sx, y - sy) for x, y in diff) / (g.zoom)          # canvas px from the hand point
    d = character_look.DIRS[round(g.hero.angle / (pi / 4)) % 8]
    # behind check facing north: some weapon pixels must be hidden by the body (fewer changed pixels)
    print(f"{d:10s} hand at screen ({sx:.0f},{sy:.0f})  nearest weapon pixel {near:.2f} canvas px  changed {len(diff)}")
    errors.append((d, near))
bad = [e for e in errors if not isinstance(e[1], float) or e[1] > 1.0]
print("drawn grip within 1 canvas px of the hand point:", "OK" if not bad else bad)

# 2) swing angles: chop sweeps aim+60 -> aim-60 at the hit
a = -pi / 2
for t, c in ((0.0, 0.5), (0.25, 0.5), (0.5, 0.5), (0.75, 0.5), (1.0, 0.5)):
    ang, push = look.weapon_angle("chop", t, c, a, "south")
    print(f"chop t={t:.2f}: {degrees(ang - a):+.0f} deg from the aim")
for t in (0.0, 0.3, 0.6, 1.0):
    ang, push = look.weapon_angle("stab", t, 0.6, a, "south")
    print(f"stab t={t:.1f}: push {push:.1f} px")

# 3) frame time
aim_at(-pi / 2)
t0 = time.perf_counter()
for _ in range(60):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
print(f"frame {1000 * (time.perf_counter() - t0) / 60:.1f} ms")

# 4) picture sheet
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 14)
CW, CH = 150, 150
sheet = Image.new("RGB", (8 * CW, 6 * (CH + 20)), (20, 20, 22)); dr = ImageDraw.Draw(sheet)
def cell(im, col, row, label):
    x, y = hp()
    sheet.paste(im.crop((int(x) - CW // 2, int(y) - CH + 30, int(x) + CW // 2, int(y) + 30)), (col * CW, row * (CH + 20) + 20))
    dr.text((col * CW + 4, row * (CH + 20) + 3), label, font=f, fill=(196, 170, 92))
for row, (wkey, wname) in enumerate((("pipe", "쇠파이프"), ("axe", "도끼"), ("knife", "식칼"), ("pistol", "권총"))):
    g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == wkey) if isinstance(weapons.WEAPONS, dict) \
        else next(w for w in weapons.WEAPONS if w["sprite"] == wkey)
    for col in range(8):
        a = col * pi / 4; aim_at(a)
        cell(shot(g), col, row, f"{wname} {degrees(a):.0f}°")
g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
# swing frames toward south-east (row 5), every few frames of one chop
aim_at(-pi / 4)
g.hero.slash_cooldown = 0
g.hero.start_slash(g.hero.x + 100, g.hero.y - 100)
col = 0
for n in range(80):
    if not g.hero.slash or col >= 8: break
    x, y = hp(); g.aim = (x + 200, y + 200); g.update(1 / 60, keys)
    if n % 3 == 0 and g.hero.slash:
        s_ = g.hero.slash
        cell(shot(g), col, 4, f"휘두르기 {s_['time'] / s_['whole']:.2f}"); col += 1
# walking south (row 6)
keys[sdl2.SDL_SCANCODE_S] = 1
for col in range(8):
    for _ in range(3):
        x, y = hp(); g.aim = (x, y + 300); g.update(1 / 60, keys)
    cell(shot(g), col, 5, f"걷기 {col}")
keys[sdl2.SDL_SCANCODE_S] = 0
sheet.save("docs/planning/paper_doll_ingame.png")
pico2d.close_canvas(); print("ok")
