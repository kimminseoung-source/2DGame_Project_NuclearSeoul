"""Short-lived visual effects that remove themselves from the game world."""

import camera
import game_clock
import game_world
import hit_feel
import ui
from weapon import IMPACT_TIME, draw_impact


class Impact:
    """The star burst where a blow lands."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.time_left = IMPACT_TIME

    def update(self):
        self.time_left -= game_clock.frame_time
        if self.time_left <= 0:
            game_world.remove_object(self)

    def draw(self):
        draw_impact(self.x - camera.x, self.y + 5, max(0.0, self.time_left))


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
