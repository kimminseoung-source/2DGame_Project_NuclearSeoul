"""Baseball bat timing, hit detection and test crate rendering."""

from math import cos, hypot, pi

import pico2d


BAT_CONTACT = 0.14
BAT_FOLLOW_THROUGH = 0.20
BAT_RECOVERY = 0.27
BAT_DURATION = 0.34
BAT_HITSTOP = 0.075
BAT_IMPACT_TIME = 0.18
BAT_PLAYBACK_RATE = 0.7
BAT_REACH = 40
BAT_DEPTH_REACH = 20
BAT_ARC = pi / 4
CRATE_POSITION = (432, 86)
# Offsets from the player to the right-facing bat tip and its trail.
SWING_TRAIL = {
    2: ((27, 16), (31, 18), (32, 22), (30, 27)),
    3: ((-20, 7), (-24, 8), (-26, 11), (-26, 15)),
}


class BatSwing:
    def __init__(self, direction):
        self.dx, self.dy = direction
        self.elapsed = 0.0

    def update(self, frame_time):
        previous_time = self.elapsed
        self.elapsed += frame_time * BAT_PLAYBACK_RATE
        return previous_time < BAT_CONTACT <= self.elapsed

    def hits(self, player, target):
        dx, dy = target[0] - player.x, target[1] - player.y
        distance = hypot(dx, dy)
        if distance > BAT_REACH or abs(dy) > BAT_DEPTH_REACH:
            return False
        if distance and (dx * self.dx + dy * self.dy) / hypot(self.dx, self.dy) < distance * cos(BAT_ARC):
            return False
        # Check the short line to the target only on the contact frame.
        steps = max(1, int(distance / 4) + 1)
        return all(
            player.tile_map.can_stand(player.x + dx * step / steps, player.y + dy * step / steps, 0)
            for step in range(1, steps + 1)
        )

    @property
    def frame(self):
        if self.elapsed < BAT_CONTACT:
            return 1
        if self.elapsed < BAT_FOLLOW_THROUGH:
            return 2
        if self.elapsed < BAT_RECOVERY:
            return 3
        return 4

    def draw_trail(self, player, camera_x):
        trail = SWING_TRAIL.get(self.frame)
        if trail is None:
            return
        x = player.x - camera_x
        y = player.y
        for index, ((x1, y1), (x2, y2)) in enumerate(zip(trail, trail[1:])):
            start_x, end_x = x + self.dx * x1, x + self.dx * x2
            pico2d.draw_line(start_x, y + y1, end_x, y + y2, 248 - 42 * index, 48, 50)
            if index < 2:
                pico2d.draw_line(start_x, y + y1 - 1, end_x, y + y2 - 1, 150, 29, 37)


def draw_crate(x, y, broken):
    if broken:
        pico2d.draw_line(x - 12, y - 4, x - 3, y + 4, 153, 103, 57)
        pico2d.draw_line(x + 1, y - 6, x + 12, y + 1, 153, 103, 57)
        return
    pico2d.draw_rectangle(x - 12, y - 10, x + 12, y + 10, 112, 73, 44, filled=True)
    pico2d.draw_rectangle(x - 11, y - 9, x + 11, y + 9, 208, 155, 95)
    pico2d.draw_line(x - 10, y - 8, x + 10, y + 8, 173, 120, 69)


def draw_impact(x, y, time_left):
    progress = 1 - time_left / BAT_IMPACT_TIME
    inner = 0.18 + progress * 0.65
    outer = inner + (1 - progress) * 0.52
    for dx, dy in ((-25, 8), (-15, 21), (4, 25), (22, 15), (26, -4), (12, -13)):
        pico2d.draw_line(
            x + dx * inner, y + dy * inner,
            x + dx * outer, y + dy * outer, 255, 214, 127,
        )
    if progress < 0.3:
        pico2d.draw_circle(x, y, 4, 255, 237, 191, filled=True)
