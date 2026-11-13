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


class ComboNumber:
    """The running total of a flurry on one target: grows and pops with every cut."""

    LIFE = 1.0

    def __init__(self, target):
        self.target = target
        self.total = 0
        self.count = 0
        self.age = 0.0
        self.feel = hit_feel.feel(hit_feel.LIGHT)

    def add(self, amount, hit_weight):
        self.total += amount
        self.count += 1
        self.feel = hit_feel.feel(hit_weight)
        self.age = 0.0

    def update(self):
        self.age += game_clock.real_frame_time
        if self.age >= self.LIFE:
            game_world.remove_object(self)

    def draw(self):
        pop = 1 + 0.6 * max(0.0, 1 - self.age / 0.12)
        size = round((18 + min(16, self.count * 1.5)) * pop)
        x, y = self.target.x - camera.x, self.target.y + 66 + 10 * min(1.0, self.age / self.LIFE)
        ui.text_center(x, y, str(self.total), self.feel.number_color, size)
        if self.count > 1:
            ui.text_center(x, y + size * 0.8, f"{self.count}연격", (200, 255, 210), 13)


class ScreenFlash:
    """A white flash over the street that fades out (the flurry being let loose)."""

    def __init__(self, life=0.18, strength=170):
        self.life = life
        self.strength = strength
        self.age = 0.0

    def update(self):
        self.age += game_clock.real_frame_time
        if self.age >= self.life:
            game_world.remove_object(self)

    def draw(self):
        alpha = round(self.strength * (1 - self.age / self.life))
        pico2d.draw_rectangle(0, 0, ui.SCREEN_WIDTH, ui.WORLD_HEIGHT, 255, 255, 255, alpha, filled=True)


class WarpTint:
    """While the time warp runs: the street drains to a cold blue with darker edges, and the
    hero glows green, brighter with every charge level."""

    BANDS = 10

    def __init__(self, warp, hero):
        self.warp = warp
        self.hero = hero
        self.age = 0.0

    def update(self):
        self.age += game_clock.real_frame_time

    def draw(self):
        blend = self.warp.blend
        if blend <= 0:
            return
        width, height = ui.SCREEN_WIDTH, ui.WORLD_HEIGHT - 64
        pico2d.draw_rectangle(0, 0, width, height, 20, 40, 70, round(70 * blend), filled=True)
        for band in range(self.BANDS):                      # darker towards the edges
            inset = band * 9
            alpha = round(blend * 26 * (1 - band / self.BANDS))
            pico2d.draw_rectangle(inset, inset, width - inset, height - inset, 0, 0, 0, alpha)
            for t in range(9):
                pico2d.draw_rectangle(inset + t, inset + t, width - inset - t, height - inset - t,
                                      0, 0, 0, alpha)
        if self.warp.held:
            level = self.warp.reached
            x, y = self.hero.x - camera.x, self.hero.y + 16
            pulse = 0.5 + 0.5 * sin(self.age * 12)
            for ring in range(level + 1):
                radius = round(18 + ring * 7 + pulse * 3)
                pico2d.draw_circle(x, y, radius, 120, 255, 160, round(blend * (70 + 50 * level) * (1 - ring * 0.2)))

