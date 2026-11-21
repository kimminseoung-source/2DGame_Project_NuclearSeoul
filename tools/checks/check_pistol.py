"""The pistol: pick up -> 6 rounds; a shot hits the first infected on the line, not through a wall;
the bang wakes a far one; empty -> no shot. Then shots of aiming and firing."""
import sys, random; sys.path.insert(0, "src")
from math import hypot, pi
import pico2d, sdl2, play, settings, ui, infected, weapons, area
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2); g = play.Game(); g.to_spawn = 0; g.note_folded = True
g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}
h = g.hero


def screen(wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k


def run(n):
    for _ in range(n): g.update(1 / 60, keys)


def grab():
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, b"docs/planning/_t.bmp")
    return Image.open("docs/planning/_t.bmp").convert("RGB")


gun = next(w for w in g.ground_weapons if w[2] == "pistol")
h.x, h.y = gun[0], gun[1]
run(2); g.interact(); run(40)
print("picked: ammo", g.ammo, "| in bag", g.bag.get("w:pistol"))
g.equip("pistol"); print("in hand:", h.weapon["name"], "| sounds:", g.sounds.has("shot"), g.sounds.has("dry"))
# on the open road: one infected 200 ahead, one 320 ahead behind it, one far off to the side (unaware)
h.x, h.y = 300, 600
zs = [infected.Zombie(g.zombie_look, h.x + d, h.y + dy) for d, dy in ((200, 0), (320, 0), (-10, -330))]
for z in zs:
    z.prone = False; z.state = "idle"; z.heading = 0; z.turn_in = 99
g.zombies[:] = zs
g.cam = [h.x - g.view_w / 2 + 120, h.y - g.view_h / 2]; g.clamp_camera()
run(5)
sx, sy = screen(zs[0].x, zs[0].y + 24)
g.aim = (sx, sy)
g.press(sx, sy); run(40)
aim_shot = grab()
before = [z.health for z in zs]
g.release(sx, sy)
fire_shot = None
for i in range(12):
    g.update(1 / 60, keys)
    if fire_shot is None and any(type(e).__name__ == "Tracer" for e in g.effects):
        fire_shot = grab()
run(30)
print("shot 1: health", before, "->", [z.health if z.alive else "dead" for z in zs], "| ammo", g.ammo,
      "| far one heard:", zs[2].state)
# behind a wall: the wreck / a building between
wall = max((b for b, look in zip(area.BLOCKS, area.BLOCK_LOOKS) if look == "building"), key=lambda b: b[2] - b[0])
l, b, r, t = wall
h.x, h.y = (l + r) / 2, b - 30
z = infected.Zombie(g.zombie_look, (l + r) / 2, t + 30); z.prone = False; z.state = "idle"; z.turn_in = 99
g.zombies[:] = [z]; run(30)
g.cam = [h.x - g.view_w / 2, h.y - g.view_h / 2]; g.clamp_camera(); run(2)
hp = z.health; g.click(*screen(z.x, z.y + 24)); run(40)
print("through a building: health", hp, "->", z.health, "| ammo", g.ammo)
while g.ammo > 0:
    g.click(*screen(h.x + 100, h.y)); run(40)
n = len(g.effects); g.click(*screen(h.x + 100, h.y)); run(3)
print("empty: ammo", g.ammo, "| slash started:", h.slash is not None)
import os; os.remove("docs/planning/_t.bmp")
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 20)
a, c = aim_shot.crop((240, 150, 1040, 570)), (fire_shot or aim_shot).crop((240, 150, 1040, 570))
sheet = Image.new("RGB", (1620, 460), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
sheet.paste(a, (0, 40)); sheet.paste(c, (820, 40))
d.text((8, 10), "조준: 점선이 총알이 가는 길", font=f, fill=(196, 170, 92)); d.text((828, 10), "발사: 총구 불빛과 탄 궤적", font=f, fill=(196, 170, 92))
sheet.save("docs/planning/pistol_ingame.png"); print("fire frame caught:", fire_shot is not None)
