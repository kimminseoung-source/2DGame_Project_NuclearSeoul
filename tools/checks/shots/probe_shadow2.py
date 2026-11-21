"""Same scene as shot_cone.py: darkness at points around the wreck, and which blocker shadows them."""
import sys; sys.path.insert(0, "src")
from math import hypot
import pico2d, sdl2, play, settings, ui, area, vision_cone
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
i = area.BLOCK_LOOKS.index("wreck_1"); l, b, r, t = area.BLOCKS[i]
g = play.Game(); g.dev.freeze = True; g.daylight.hour = 22
g.hero.x, g.hero.y = l - 150, (b + t) / 2 - 22
for _ in range(40): g.update(1 / 60, keys)
k = g.zoom * settings.DOT
g.aim = (((l + r) / 2 - g.cam[0]) * k, settings.HEIGHT - ((b + t) / 2 + 22 - g.cam[1]) * k)
for _ in range(3): g.update(1 / 60, keys)
eye = (g.hero.x, g.hero.y)
for label, (x, y) in (("on the car", (272, 656)), ("right behind", (340, 656)), ("above the car", (272, 700)),
                       ("above-right", (350, 700)), ("further up", (300, 740))):
    dx, dy = x - eye[0], y - eye[1]; d = hypot(dx, dy)
    blk = area.sight_blocks(min(eye[0], x), min(eye[1], y), max(eye[0], x), max(eye[1], y))
    hit = vision_cone.ray_hit(eye[0], eye[1], dx / d, dy / d, blk)
    who = [bb for bb in blk if vision_cone.ray_hit(eye[0], eye[1], dx / d, dy / d, [bb]) == hit and hit < d]
    print(f"{label:14s} ({x},{y}) dist {d:5.0f} darkness {g.vision.darkness(eye, g.look, x, y):6.1f} | shadow starts {hit:6.1f} by {who[:1]}")
print("wreck rect", (l, b, r, t), "| look", round(g.look, 3))
pico2d.close_canvas()
