"""Who can be seen, day vs night: only the cone's length changes; outside the cone and behind walls never."""
import sys; sys.path.insert(0, "src")
from math import cos, sin, pi
import pico2d, sdl2, play, settings, ui, area
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True
eye = (600.0, 470.0)                     # open road
for hour in (13, 22):
    g.daylight.hour = hour
    g.update(1 / 60, keys)
    g.vision.fog, g.vision.reach = g.daylight.fog, g.daylight.reach
    look = 0.0
    row = []
    for label, d, a in (("앞 250", 250, 0), ("앞 400", 400, 0), ("앞 500", 500, 0), ("옆 200", 200, pi / 2),
                        ("뒤 80 (몸 주변)", 80, pi), ("뒤 200", 200, pi)):
        x, y = eye[0] + cos(a) * d, eye[1] + sin(a) * d
        row.append(f"{label}: {'보임' if g.vision.visible(eye, look, x, y) else '안 보임'}")
    print(f"{hour}시 {g.daylight.name} (시야 {g.daylight.reach:.0f}, 화면 어둡기 {g.daylight.fog:.0f}) | " + " · ".join(row))
# behind a wreck, both times
j = area.BLOCK_LOOKS.index("wreck_1"); l, b, r, t = area.BLOCKS[j]
e2, behind = (l - 150, (b + t) / 2), (r + 30, (b + t) / 2)
for hour in (13, 22):
    g.daylight.hour = hour; g.vision.reach = g.daylight.reach; g.vision.fog = g.daylight.fog
    print(f"{hour}시 폐차 뒤 30: {'보임' if g.vision.visible(e2, 0.0, *behind) else '안 보임'} | 그려진 어둡기 {g.vision.darkness(e2, 0.0, *behind, drawn=True):.0f} (벽 뒤도 건물이 보이게)")
pico2d.close_canvas(); print("ok")
