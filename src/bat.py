"""Baseball bat timing, hit detection and test crate rendering."""

from math import cos, hypot, pi

import pico2d


BAT_CONTACT = 0.14
BAT_DURATION = 0.34
BAT_PLAYBACK_RATE = 0.7
BAT_REACH = 58
BAT_ARC = pi / 4
CRATE_POSITION = (432, 120)


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
        if distance > BAT_REACH:
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
        if self.elapsed < 0.10:
            return 1
        if self.elapsed < 0.22:
            return 2
        return 3


def draw_crate(x, y, broken):
    if broken:
        pico2d.draw_line(x - 12, y - 4, x - 3, y + 4, 153, 103, 57)
        pico2d.draw_line(x + 1, y - 6, x + 12, y + 1, 153, 103, 57)
        return
    pico2d.draw_rectangle(x - 12, y - 10, x + 12, y + 10, 112, 73, 44, filled=True)
    pico2d.draw_rectangle(x - 11, y - 9, x + 11, y + 9, 208, 155, 95)
    pico2d.draw_line(x - 10, y - 8, x + 10, y + 8, 173, 120, 69)
