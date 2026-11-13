"""Short-lived visual effects that remove themselves from the game world."""

from math import sin

import pico2d

import camera
import game_clock
import game_world
import hit_feel
import ui
from weapon import IMPACT_TIME, draw_impact


class Impact:
    """The star burst where a blow lands."""

    def __init__(self, x, y, scale=1.0):
        self.x, self.y = x, y
        self.scale = scale
        self.time_left = IMPACT_TIME

    def update(self):
        self.time_left -= game_clock.frame_time
        if self.time_left <= 0:
            game_world.remove_object(self)

    def draw(self):
        draw_impact(self.x - camera.x, self.y + 5, max(0.0, self.time_left), self.scale)


class DodgeFlash:
    """A white ring bursting from the hero on a perfect dodge."""

    LIFE = 0.3

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.age = 0.0

    def update(self):
        self.age += game_clock.frame_time
        if self.age >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        progress = self.age / self.LIFE
        alpha = round(230 * (1 - progress))
        for extra in (0, 1):
            pico2d.draw_circle(self.x - camera.x, self.y + 14, round(10 + 34 * progress) + extra,
                               255, 255, 255, alpha)


class DamageNumber:
    """The damage a blow dealt, popping up over the target in real-time combat.

    Size, colour and pop come from hit_feel, so every attack (any weapon, any enemy) shows
    its weight the same way; damage to the hero is drawn in the hero colour.
    """

    LIFE = 0.7
    POP_TIME = 0.16

    def __init__(self, x, y, amount, hit_weight, color=None):
        self.x, self.y = x, y
        self.amount = amount
        self.feel = hit_feel.feel(hit_weight)
        self.color = color or self.feel.number_color
        self.age = 0.0

    def update(self):
        self.age += game_clock.frame_time
        if self.age >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        rise = 14 * self.age / self.LIFE
        pop = 1 + self.feel.pop * max(0.0, 1 - self.age / self.POP_TIME)
        ui.text_center(self.x - camera.x, self.y + 58 + rise, str(self.amount), self.color,
                       round(self.feel.number_size * 0.7 * pop))


class SlashMark:
    """A blow kept during the time warp: a glowing cut on the target that stays (frozen in
    time) until the burst lands it, then removes itself."""

    ANGLES = ((-10, 14, 10, -10), (-12, -4, 12, 10), (-6, 18, 8, -14), (-14, 6, 14, -2))

    def __init__(self, target, index):
        self.target = target
        self.line = self.ANGLES[index % len(self.ANGLES)]
        self.age = 0.0

    def update(self):
        self.age += game_clock.hero_frame_time
        if not self.target.stored_hits:
            game_world.remove_object(self)

    def draw(self):
        x, y = self.target.x - camera.x, self.target.y + 16
        x1, y1, x2, y2 = self.line
        glow = round(170 + 60 * (0.5 + 0.5 * sin(self.age * 18)))
        for offset in (-1, 0, 1):
            pico2d.draw_line(x + x1, y + y1 + offset, x + x2, y + y2 + offset, glow, 255, glow,
                             255 if offset == 0 else 110)

