"""A spare gas-mask filter lying on the floor until the player picks it up."""

from math import hypot

import camera
import ui
from item_ui import draw_filter_icon
from tile_map import WIDTH


PICKUP_RANGE = 34


class FilterSupply:
    def __init__(self, x, y, player):
        self.x, self.y = x, y
        self.player = player

    def near(self, player):
        return hypot(player.x - self.x, player.y - self.y) <= PICKUP_RANGE

    def update(self):
        pass

    def draw(self):
        x = self.x - camera.x
        if not -40 < x < WIDTH + 40:
            return
        draw_filter_icon(x, self.y, scale=2 / 3)
        if self.player.state != "PICKUP" and self.near(self.player):
            ui.text(x - 24, self.y + 46, "E 줍기", ui.ACCENT)
        else:
            ui.text(x - 15, self.y + 18, "필터", ui.ACCENT)
