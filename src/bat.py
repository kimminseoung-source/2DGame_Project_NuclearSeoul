"""Baseball bat timing, hit detection and impact effect."""

from math import cos, hypot, pi

import pico2d


# Seconds from the start of the swing. A longer wind-up gathers weight before the blow;
# the strike itself stays quick so the hit feels sharp.
BAT_CONTACT = 0.30
BAT_FOLLOW_THROUGH = 0.40
BAT_DURATION = 0.60
BAT_IMPACT_TIME = 0.18
BAT_REACH = 40
BAT_DEPTH_REACH = 20
BAT_ARC = pi / 4
# Offsets from the player to the right-facing trail of the blow, drawn just after contact.
SWING_TRAIL = ((27, 16), (31, 18), (32, 22), (30, 27))


class BatSwing:
    def __init__(self, direction):
        self.dx, self.dy = direction
        self.elapsed = 0.0

    def update(self, frame_time):
        previous_time = self.elapsed
        self.elapsed += frame_time
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

    # Every attack exposes progress (0..1) and the progress at which it lands (contact), so a
    # character's look can put its impact frame exactly on the hit (character_look.SheetLook).
    contact = BAT_CONTACT / BAT_DURATION

    @property
    def progress(self):
        return min(1.0, self.elapsed / BAT_DURATION)

    @property
    def done(self):
        return self.elapsed >= BAT_DURATION

    def draw_trail(self, player, camera_x):
        if not BAT_CONTACT <= self.elapsed < BAT_FOLLOW_THROUGH:
            return
        trail = SWING_TRAIL
        x = player.x - camera_x
        y = player.y
        for index, ((x1, y1), (x2, y2)) in enumerate(zip(trail, trail[1:])):
            start_x, end_x = x + self.dx * x1, x + self.dx * x2
            pico2d.draw_line(start_x, y + y1, end_x, y + y2, 248 - 42 * index, 48, 50)
            if index < 2:
                pico2d.draw_line(start_x, y + y1 - 1, end_x, y + y2 - 1, 150, 29, 37)


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
