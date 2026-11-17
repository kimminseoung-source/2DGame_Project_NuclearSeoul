"""A staged demo with every action the hero has (2026-11-17 "우리가 한 동작들, 그거를 영상 안에 다
들어가면 좋겠음, 시연 안에"): walk, sneak, pick up, switch weapon, shoot, quick slash, aimed head
blow, shove-counter, roll, stomp, getting hit, bandage, the house, the bag, the way out.

    python <run_hidden.py> tools/presentation/record_showcase.py   -> docs/presentation/img/demo.gif

Staged, not played: for each scene an infected is set where the scene needs it (a crawler for the
stomp, one that strikes for the bandage) and some have less health so a scene does not drag on.
The hero is driven through the same calls the mouse and keys make; the game's rules are untouched.
Every 5th frame of 60 is kept (12 fps).
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

OUT = ROOT / "docs" / "presentation" / "img" / "demo.gif"
KEEP, SIZE = 5, (640, 360)
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False)
ui.enable_blending()
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
g = play.Game()
g.note_folded = True
g.to_spawn = 99                                          # more to come, so it never reads "구역 정리"...
g.spawn_in = 1e9                                         # ...but no arrivals: each scene brings its own
g.zombies[:] = []
g.used |= {"move", "attack", "roll", "charge", "sneak", "pick"}   # no key marks over the head
g.bag["bandage"] = 1
h = g.hero
frames, tick, log = [], 0, []
surface = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
MOVE = (sdl2.SDL_SCANCODE_W, sdl2.SDL_SCANCODE_A, sdl2.SDL_SCANCODE_S, sdl2.SDL_SCANCODE_D)


def screen(wx, wy):
    k = g.zoom * settings.DOT
    return (wx - g.cam[0]) * k, settings.HEIGHT - 1 - (wy - g.cam[1]) * k


def frame():
    """One game frame (and every 5th kept for the GIF)."""
    global tick
    g.update(1 / 60, keys)
    if tick % KEEP == 0:
        pico2d.clear_canvas()
        g.draw()
        pico2d.update_canvas()
        sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888,
                                  surface.contents.pixels, surface.contents.pitch)
        raw = ctypes.string_at(surface.contents.pixels, surface.contents.pitch * settings.HEIGHT)
        img = Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", surface.contents.pitch, 1)
        frames.append(img.convert("RGB").resize(SIZE, Image.BILINEAR))
    tick += 1


def wait(seconds, until=None):
    """Run frames for `seconds`, or until `until()` is true (then a short beat more)."""
    for _ in range(round(seconds * 60)):
        frame()
        if until is not None and until():
            for _ in range(18):
                frame()
            return True
    return False


def stop():
    for k in MOVE + (sdl2.SDL_SCANCODE_LCTRL,):
        keys[k] = 0


def steer(tx, ty):
    dx, dy = tx - h.x, ty - h.y
    d = hypot(dx, dy)
    if d > 1 and ray_hit(h.x, h.y, dx / d, dy / d, area.blocks_between(h.x, h.y, tx, ty)) < d:
        wx, wy = area.waypoint(h.x, h.y, tx, ty)
        dx, dy = wx - h.x, wy - h.y
    keys[sdl2.SDL_SCANCODE_D], keys[sdl2.SDL_SCANCODE_A] = dx > 6, dx < -6
    keys[sdl2.SDL_SCANCODE_W], keys[sdl2.SDL_SCANCODE_S] = dy > 6, dy < -6
    g.aim = screen(h.x + dx * 3, h.y + dy * 3)


def walk_to(tx, ty, seconds=8.0, near=20):
    for _ in range(round(seconds * 60)):
        if hypot(tx - h.x, ty - h.y) < near:
            break
        steer(tx, ty)
        frame()
    stop()


def foe(dx, dy, health=None, crawler=False, angry=True):
    """An infected set `dx, dy` from the hero, facing him and after him."""
    z = infected.Zombie(g.zombie_look, h.x + dx, h.y + dy, crawler=crawler)
    z.prone = crawler
    if health is not None:
        z.health = health
    if angry:
        z.state, z.target, z.memory = "chase", (h.x, h.y), 99
        z.seen_time = infected.SEEN_BEFORE_STRIKE
    z.heading = 3.14159 if dx > 0 else 0.0
    z.turn_in = 99
    g.zombies.append(z)
    return z


def aim_at(z, up=26):
    g.aim = screen(z.x, z.y + up)
    return g.aim


def strike(z, head=False, seconds=5.0):
    """Step in until it is in reach, then a quick blow (or, `head`: hold the blow raised at the head
    until the charge is full and let it go) - again until it falls."""
    up = 46 if head else 26
    for _ in range(round(seconds * 60)):
        if not z.alive:
            break
        d = hypot(z.x - h.x, z.y - h.y)
        reach = weapons.attack_range(h.weapon)
        if d > reach - 6:
            steer(z.x, z.y)
        else:
            stop()
        aim_at(z, up)
        if head:
            if h.ready is None and h.free:
                g.press(*g.aim)
            elif h.ready is not None and h.charge >= 1.0 and d <= reach + 4:
                g.release(*g.aim)
        elif h.free and d <= reach + 4:
            g.click(*g.aim)
        frame()
    stop()
    if h.ready is not None:
        g.release(*g.aim)
    wait(0.3)


def scene(name):
    zs = " ".join(f"{z.state[:5]}{'' if z.alive else '†'}{z.health}@{z.x - h.x:+.0f},{z.y - h.y:+.0f}" for z in g.zombies[-3:])
    log.append(f"{tick / 60:5.1f}s {name:24s} hero ({h.x:.0f},{h.y:.0f}) {h.weapon['name']} ammo {g.ammo} hp {h.hp:.0f} | {zs}")


# --- the scenes ---------------------------------------------------------------------------------
scene("걷기")
walk_to(h.x + 70, h.y, 1.0)
scene("줍기 (권총)")
gun = next(((x, y) for x, y, k in area.WEAPONS_LYING if k == "pistol"), None)
if gun:
    walk_to(*gun, 2.0, near=12)
    g.interact()
    wait(0.5)
scene("무기 바꾸기 Q (권총)")
g.key_down(sdl2.SDLK_q, keys)
wait(0.4)
scene("살금 (Ctrl)")
keys[sdl2.SDL_SCANCODE_LCTRL] = 1
walk_to(h.x + 60, h.y + 60, 1.4)
stop()
walk_to(300, 600, 2.5)                                   # out on the road
scene("총 쏘기")
z = foe(230, 0)
wait(0.5)
g.click(*aim_at(z))
wait(1.2, lambda: not z.alive)
scene("무기 바꾸기 Q (마체테)")
g.key_down(sdl2.SDLK_q, keys)
wait(0.4)
scene("빠른 베기")
z = foe(80, 0, health=3)
strike(z)
scene("머리 조준 (누르고 있다 놓기)")
z = foe(110, 0, health=9)
strike(z, head=True)
scene("받아치기 (우클릭)")
z = foe(50, 0, health=4)
for _ in range(300):
    aim_at(z)
    frame()
    if z.state == "windup" and z.timer <= 0.25 and hypot(z.x - h.x, z.y - h.y) <= play.SHOVE_REACH:
        g.right_click(*aim_at(z))
        break
wait(0.4)
strike(z)
scene("구르기 (Space)")
z = foe(70, 0, health=4)
wait(0.6)
keys[sdl2.SDL_SCANCODE_A] = 1
g.key_down(sdl2.SDLK_SPACE, keys)
wait(0.5)
stop()
scene("밟기 (기는 놈)")
c = foe(-50, 0, health=4, crawler=True)
for _ in range(240):
    if not c.alive:
        break
    d = hypot(c.x - h.x, c.y - h.y)
    if d > 30:
        steer(c.x, c.y)
    else:
        stop()
        if h.free:
            g.click(*aim_at(c, 6))
    aim_at(c, 6)
    frame()
stop()
wait(0.3)
scene("맞기 (출혈)")
hp = h.hp
wait(4.0, lambda: h.hp < hp)
wait(0.6, lambda: h.free)
strike(z)                                                # then put it down
scene("붕대 (1)")
g.key_down(sdl2.SDLK_1, keys)
wait(1.0)
scene("집 안 (지붕이 걷힘) · 물자")
door_x, door_y = area.BUILDINGS[0]["doors"][0] if area.BUILDINGS and "doors" in area.BUILDINGS[0] else (576, 768)
walk_to(door_x, door_y - 50, 4.0)
inside = [(x, y) for x, y, _ in area.SUPPLIES if area.building_at(x, y) is not None]
if inside:
    walk_to(*inside[0], 3.0, near=14)
    g.interact()
    wait(0.6)
scene("배낭 (Tab)")
g.key_down(sdl2.SDLK_TAB, keys)
log.append(f"      bag open after Tab: {g.bag_open}")
wait(1.6)
log.append(f"      bag open after 1.6 s: {g.bag_open}")
g.key_down(sdl2.SDLK_TAB, keys)
wait(0.2)
scene("탈출 (지하철 입구)")
walk_to(door_x, door_y - 60, 3.0)
ex = ((area.EXIT[0] + area.EXIT[2]) / 2, (area.EXIT[1] + area.EXIT[3]) / 2)
for _ in range(60 * 12):
    if g.near_exit():
        break
    steer(*ex)
    frame()
stop()
g.interact()
wait(1.2)

OUT.parent.mkdir(parents=True, exist_ok=True)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=round(1000 * KEEP / 60), loop=0)
print("\n".join(log))
print(f"total {tick / 60:.1f}s, kills {g.kills}, hp {h.hp:.0f}, left {g.left}, dead {bool(h.dead)}, "
      f"{OUT.stat().st_size / 1e6:.1f} MB")
