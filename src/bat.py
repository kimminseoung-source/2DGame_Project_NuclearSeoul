"""Baseball bat timing, hit detection and test crate rendering."""

from math import atan2, cos, hypot, pi, sin

import pico2d


BAT_CONTACT = 0.14
BAT_DURATION = 0.34
BAT_REACH = 58
BAT_ARC = pi / 4
CRATE_POSITION = (432, 120)
ATTACK_CELL_WIDTH = 77
ATTACK_CELL_HEIGHT = 58


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

    def draw_right_attack(self, player, camera_x, image):
        column = 0 if self.elapsed < 0.10 else 1 if self.elapsed < 0.22 else 2
        image.clip_draw(
            column * ATTACK_CELL_WIDTH, 0,
            ATTACK_CELL_WIDTH, ATTACK_CELL_HEIGHT,
            player.x - camera_x, player.y - 12 + ATTACK_CELL_HEIGHT / 2,
        )

    def draw(self, player, camera_x):
        facing = atan2(self.dy, self.dx)
        sweep = min(1.0, max(0.0, (self.elapsed - 0.06) / 0.16))
        angle = facing + BAT_ARC * (2 * sweep - 1)
        x, y = player.x - camera_x, player.y + 2
        grip_x, grip_y = x + 12 * cos(angle), y + 12 * sin(angle)
        tip_x, tip_y = x + 43 * cos(angle), y + 43 * sin(angle)
        for offset in (-1, 0, 1):
            pico2d.draw_line(grip_x, grip_y + offset, tip_x, tip_y + offset, 168, 113, 64)
        pico2d.draw_circle(tip_x, tip_y, 3, 202, 149, 87, filled=True)


def draw_carried_bat(player, camera_x):
    # Carry at the side, with the handle tucked into the glove.
    hand_x = player.x - camera_x + 6
    hand_y = player.y + (5 if player.sneaking else 8)
    tip_x, tip_y = hand_x + 16, hand_y - 7
    pico2d.draw_line(hand_x, hand_y, tip_x, tip_y, 80, 51, 34)
    pico2d.draw_line(hand_x, hand_y + 1, tip_x, tip_y + 1, 169, 113, 64)
    pico2d.draw_circle(tip_x, tip_y, 2, 188, 132, 74, filled=True)


def draw_crate(x, y, broken):
    if broken:
        pico2d.draw_line(x - 12, y - 4, x - 3, y + 4, 153, 103, 57)
        pico2d.draw_line(x + 1, y - 6, x + 12, y + 1, 153, 103, 57)
        return
    pico2d.draw_rectangle(x - 12, y - 10, x + 12, y + 10, 112, 73, 44, filled=True)
    pico2d.draw_rectangle(x - 11, y - 9, x + 11, y + 9, 208, 155, 95)
    pico2d.draw_line(x - 10, y - 8, x + 10, y + 8, 173, 120, 69)
