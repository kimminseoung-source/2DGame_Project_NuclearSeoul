"""Darkness along the line hero -> wreck centre -> beyond, as the game computes and draws it."""
import sys; sys.path.insert(0, "src")
from math import atan2, hypot, cos, sin
import pico2d, sdl2, play, settings, ui, area, vision_cone
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
i = area.BLOCK_LOOKS.index("wreck_1"); l, b, r, t = area.BLOCKS[i]
g = play.Game(); g.dev.freeze = True; g.daylight.hour = 22
g.hero.x, g.hero.y = l - 120, (b + t) / 2
for _ in range(30): g.update(1 / 60, keys)
k = g.zoom * settings.DOT
target = ((l + r) / 2, (b + t) / 2)
g.aim = ((target[0] - g.cam[0]) * k, settings.HEIGHT - (target[1] - g.cam[1]) * k)
for _ in range(3): g.update(1 / 60, keys)
eye = (g.hero.x, g.hero.y)
print("eye", [round(v) for v in eye], "look", round(g.look, 3), "toward wreck", round(atan2(target[1] - eye[1], target[0] - eye[0]), 3))
ang = atan2(target[1] - eye[1], target[0] - eye[0])
for d in (60, 100, 115, 125, 150, 175, 200, 205, 215, 240, 300):
    x, y = eye[0] + cos(ang) * d, eye[1] + sin(ang) * d
    where = "in wreck" if l <= x <= r and b <= y <= t else ("behind" if x > r else "before")
    print(f"d {d:3d} ({x:.0f},{y:.0f}) {where:8s} darkness {g.vision.darkness(eye, g.look, x, y):6.1f}  visible {g.vision.visible(eye, g.look, x, y)}")
blk = area.sight_blocks(eye[0] - 400, eye[1] - 400, eye[0] + 400, eye[1] + 400)
print("ray_hit along it:", round(vision_cone.ray_hit(eye[0], eye[1], cos(ang), sin(ang), blk), 1), "| wreck far side at", round((r - eye[0]) / cos(ang), 1))
pico2d.close_canvas()
