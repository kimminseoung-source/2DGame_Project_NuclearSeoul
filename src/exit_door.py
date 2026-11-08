"""The way out of an area: the shelter door or the street's exit marker."""

from math import hypot

import camera
import pico2d
import ui
from tile_map import WIDTH


USE_RANGE = 34


class ExitDoor:
    def __init__(self, x, y, in_shelter):
        self.x, self.y = x, y
        self.in_shelter = in_shelter

    def near(self, player):
        return hypot(player.x - self.x, player.y - self.y) <= USE_RANGE

    def update(self):
        pass

    def draw(self):
        x = self.x - camera.x
        if not -40 < x < WIDTH + 40:
            return
        if not self.in_shelter:
            # The shelter's door is part of its picture; the street needs a marker.
            pico2d.draw_rectangle(x - 16, self.y - 12, x + 16, self.y + 40, 46, 105, 92, filled=True)
            pico2d.draw_rectangle(x - 16, self.y - 12, x + 16, self.y + 40, 97, 197, 156)
        ui.text(x - 16, self.y + 48, "출구", (135, 231, 185))
