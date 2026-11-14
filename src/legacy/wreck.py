"""The wrecked car on the street. It belongs to the map, so it stays after fights."""

import camera
from tile_map import WRECK_LEFT, WRECK_RIGHT, WRECK_Y


class Wreck:
    def __init__(self, image):
        self.image = image
        self.x = (WRECK_LEFT + WRECK_RIGHT) / 2
        self.y = WRECK_Y   # depth used for draw ordering on the ground layer

    def update(self):
        pass

    def draw(self):
        self.image.draw(self.x - camera.x, self.y - 12 + self.image.h / 2)
