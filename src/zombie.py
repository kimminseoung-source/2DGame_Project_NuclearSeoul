"""One charging infected for the street combat prototype."""

import pico2d

from tile_map import WRECK_LEFT, WRECK_RIGHT, WRECK_Y, WRECK_HALF_DEPTH


ZOMBIE_RADIUS = 10
ALERT_DISTANCE = 128
CHARGE_DEPTH = 16
WINDUP_TIME = 0.48
CHARGE_TIME = 0.40
CHARGE_SPEED = 310
RECOVERY_TIME = 0.72
KNOCKBACK_TIME = 0.24
KNOCKBACK_SPEED = 220
STAGGER_TIME = 0.38
WRECK_STUN_TIME = 1.65


class Zombie:
    def __init__(self, image, tile_map):
        self.image = image
        self.tile_map = tile_map
        self.x, self.y = 570, WRECK_Y
        self.direction = -1
        self.push_direction = 0
        self.state = "idle"
        self.time_left = 0.0

    def transition(self, state, duration=0):
        self.state = state
        self.time_left = duration

    def knock_back(self, direction):
        if self.state in ("knockback", "stunned"):
            return False
        self.push_direction = direction
        self.transition("knockback", KNOCKBACK_TIME)
        return True

    def move(self, dx):
        target = self.x + dx
        wreck_edge = WRECK_LEFT - ZOMBIE_RADIUS if dx > 0 else WRECK_RIGHT + ZOMBIE_RADIUS
        crosses_edge = self.x <= wreck_edge <= target if dx > 0 else target <= wreck_edge <= self.x
        if crosses_edge and abs(self.y - WRECK_Y) < WRECK_HALF_DEPTH + ZOMBIE_RADIUS:
            self.x = wreck_edge
            return True
        if self.tile_map.can_stand(target, self.y, ZOMBIE_RADIUS):
            self.x = target
        return False

    def update(self, dt, player):
        dx, dy = player.x - self.x, player.y - self.y
        if self.state == "idle":
            distance = ALERT_DISTANCE * (0.45 if player.sneaking else 1)
            if abs(dx) <= distance and abs(dy) <= CHARGE_DEPTH:
                self.direction = -1 if dx < 0 else 1
                self.transition("windup", WINDUP_TIME)
            return None

        step = min(dt, self.time_left)
        self.time_left -= step
        if self.state == "windup":
            if not self.time_left:
                self.transition("charge", CHARGE_TIME)
        elif self.state == "charge":
            before = self.x
            hit_wreck = self.move(self.direction * CHARGE_SPEED * step)
            if abs(dy) <= CHARGE_DEPTH and min(before, self.x) - 14 <= player.x <= max(before, self.x) + 14:
                self.transition("recover", RECOVERY_TIME)
                return "player_hit"
            if hit_wreck or not self.time_left:
                self.transition("recover", RECOVERY_TIME)
        elif self.state == "knockback":
            if self.move(self.push_direction * KNOCKBACK_SPEED * step):
                self.transition("stunned", WRECK_STUN_TIME)
                return "wreck_hit"
            if not self.time_left:
                self.transition("stunned", STAGGER_TIME)
        elif not self.time_left:
            self.transition("idle")
        return None

    def draw_warning(self, camera_x):
        if self.state != "windup":
            return
        start = self.x - camera_x
        end = start + self.direction * CHARGE_SPEED * CHARGE_TIME
        for y in (self.y - 12 - CHARGE_DEPTH, self.y - 12 + CHARGE_DEPTH):
            pico2d.draw_line(start, y, end, y, 174, 74, 47)

    def draw(self, camera_x, font):
        if self.state == "windup":
            frame = 1
        elif self.state == "charge":
            frame = 2
        elif self.state == "stunned":
            frame = 3
        else:
            frame = 0
        self.image.clip_composite_draw(
            frame * 84, 0, 84, 58, 0, "h" if self.direction < 0 else "",
            self.x - camera_x, self.y - 12 + 29, 84, 58,
        )
        if self.state == "windup":
            font.draw(self.x - camera_x - 4, self.y + 48, "!", (255, 153, 91))
