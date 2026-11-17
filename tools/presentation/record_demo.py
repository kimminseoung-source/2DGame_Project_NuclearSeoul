"""Record a demo of the alley as an animated GIF (2026-11-17 "시연 영상도 함께 들어가야 합니다"):
the game plays itself - walk, fight (aim at the head, shove a claw that is coming), go into the
house for supplies, leave by the subway entrance - and every 5th frame is kept (12 fps).

    python <run_hidden.py> tools/presentation/record_demo.py [seed]   -> docs/presentation/img/demo.gif

No video encoder needed: PowerPoint plays a GIF in the slide show. Run it with the hidden-window
runner so no window pops up. The hero is driven through the same calls the mouse and keys make
(press / release / right_click / interact, the WASD key state); nothing in the game is changed.
"""
import ctypes
import random
import sys
from math import hypot
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import pico2d  # noqa: E402
import sdl2  # noqa: E402
from PIL import Image  # noqa: E402
from pico2d import pico2d as canvas  # noqa: E402

import area  # noqa: E402
import infected  # noqa: E402
import play  # noqa: E402
import settings  # noqa: E402
import ui  # noqa: E402
import weapons  # noqa: E402
from vision_cone import ray_hit  # noqa: E402

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 3
OUT = ROOT / "docs" / "presentation" / "img" / "demo.gif"
KEEP = 5                       # every 5th frame of 60: 12 fps
SIZE = (640, 360)
MAX_SECONDS = 30               # the demo slide's length (2026-11-17 "30초로 가능해?")

keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False)
ui.enable_blending()
random.seed(SEED)
g = play.Game()
g.note_folded = True
h = g.hero
# two more infected for the demo, on the way: by the house and at the mouth of the south alley
for x, y in ((760, 736), (990, 400)):
    z = infected.Zombie(g.zombie_look, x, y)
    z.prone = False
    g.zombies.append(z)
frames = []
surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)


def screen(wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k


def grab():
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888,
                              surface.contents.pixels, surface.contents.pitch)
    raw = ctypes.string_at(surface.contents.pixels, surface.contents.pitch * settings.HEIGHT)
    img = Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", surface.contents.pitch, 1)
    frames.append(img.convert("RGB").resize(SIZE, Image.BILINEAR))


def steer(tx, ty):
    """Hold the WASD keys toward (tx, ty), going round what is in the way."""
    dx, dy = tx - h.x, ty - h.y
    d = hypot(dx, dy)
    if d > 1 and ray_hit(h.x, h.y, dx / d, dy / d, area.blocks_between(h.x, h.y, tx, ty)) < d:
        wx, wy = area.waypoint(h.x, h.y, tx, ty)
        dx, dy = wx - h.x, wy - h.y
    keys[sdl2.SDL_SCANCODE_D], keys[sdl2.SDL_SCANCODE_A] = dx > 6, dx < -6
    keys[sdl2.SDL_SCANCODE_W], keys[sdl2.SDL_SCANCODE_S] = dy > 6, dy < -6


def stop():
    for k in (sdl2.SDL_SCANCODE_W, sdl2.SDL_SCANCODE_A, sdl2.SDL_SCANCODE_S, sdl2.SDL_SCANCODE_D):
        keys[k] = 0


inside = [(x, y) for x, y, _ in area.SUPPLIES if area.building_at(x, y) is not None]
door = area.BUILDINGS[0]["box"]
door_x = (door[0] + door[2]) / 2
ex = ((area.EXIT[0] + area.EXIT[2]) / 2, (area.EXIT[1] + area.EXIT[3]) / 2)
pistols = [(x, y) for x, y, k in area.WEAPONS_LYING if k == "pistol"]
route = [("gun", pistols[0])] if pistols else []
route += [("go", (520, 480)), ("go", (576, 720))] + [("pick", p) for p in inside] + \
        [("go", (576, 720)), ("go", (990, 500)), ("go", ex), ("leave", ex)]
step, holding, shoved, tick, done_at = 0, False, 0.0, 0, None
look = (h.x + 200, h.y)

while tick < MAX_SECONDS * 60 and (done_at is None or tick < done_at + 60):
    foe = min((z for z in g.zombies if z.alive and hypot(z.x - h.x, z.y - h.y) < 170
               and area.building_at(z.x, z.y) == area.building_at(h.x, h.y)),
              key=lambda z: hypot(z.x - h.x, z.y - h.y), default=None)
    shoved = max(0.0, shoved - 1 / 60)
    if h.ready is None:
        holding = False                                   # the stance was lost (hit, rolled)
    gun = h.weapon.get("shot") is not None
    if gun and g.ammo <= 0 and h.free:                    # out of rounds: back to the blade
        g.equip("machete")
        gun = False
    if gun and g.ammo > 0 and foe is None:               # a gun reaches further: look further
        foe = min((z for z in g.zombies if z.alive and hypot(z.x - h.x, z.y - h.y) < 300
                   and area.building_at(z.x, z.y) == area.building_at(h.x, h.y)
                   and g.vision.visible((h.x, h.y), g.look, z.x, z.y)),
                  key=lambda z: hypot(z.x - h.x, z.y - h.y), default=None)
    if foe is not None and gun and not g.left and not h.dead:    # shoot it, chest high
        stop()
        look = (foe.x, foe.y + (8 if foe.prone else 26))
        g.aim = screen(*look)
        if h.free and shoved <= 0:
            g.click(*g.aim)
            shoved = 0.35                                  # a breath between shots
    elif foe is not None and not g.left and not h.dead:   # a fight
        d = hypot(foe.x - h.x, foe.y - h.y)
        look = (foe.x, foe.y + (10 if foe.prone else 46))  # the head
        sx, sy = screen(*look)
        g.aim = (sx, sy)
        reach = weapons.attack_range(h.weapon)
        if foe.state == "windup" and d <= play.SHOVE_REACH and foe.timer <= 0.3 and shoved <= 0 and not holding:
            g.right_click(sx, sy)                          # shove it as the claw is about to land
            shoved = 0.8
        elif not holding and h.free and shoved <= 0.45:
            g.press(sx, sy)
            holding = True
        elif holding and (h.charge >= 1.0 and d <= reach + 8 or d < 30):
            g.release(sx, sy)
            holding = False
        if d > reach + 4:
            steer(foe.x, foe.y)
        else:
            stop()
    elif step < len(route) and not h.dead:
        if holding:
            g.release(*g.aim)                              # nothing to hit any more: lower it
            holding = False
        kind, (tx, ty) = route[step]
        d = hypot(tx - h.x, ty - h.y)
        look = (h.x + (tx - h.x) * 4, h.y + (ty - h.y) * 4) if d > 20 else look
        g.aim = screen(*look)
        if kind == "leave":
            stop()
            if g.near_exit():
                g.interact()
                done_at = tick
                step += 1
            else:
                steer(tx, ty)
        elif d < (28 if kind in ("pick", "gun") else 22):
            if kind in ("pick", "gun"):
                g.interact()
            if kind == "gun":
                for _ in range(25):                        # the pick-up motion, then the gun in hand
                    g.update(1 / 60, keys)
                g.equip("pistol")
            step += 1
        else:
            steer(tx, ty)
    else:
        stop()
    g.update(1 / 60, keys)
    if tick % KEEP == 0:
        pico2d.clear_canvas()
        g.draw()
        pico2d.update_canvas()
        grab()
    tick += 1
    if h.dead and done_at is None:
        done_at = tick

OUT.parent.mkdir(parents=True, exist_ok=True)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=round(1000 * KEEP / 60), loop=0, optimize=False)
print(f"seed {SEED}: {tick / 60:.1f}s, {len(frames)} frames, kills {g.kills}, hp {h.hp:.0f}, left {g.left}, "
      f"dead {bool(h.dead)}, step {step}/{len(route)}, {OUT.stat().st_size / 1e6:.1f} MB")
