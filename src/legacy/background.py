"""The street or shelter backdrop drawn behind everything else."""

import camera


class Background:
    def __init__(self, tile_map):
        self.tile_map = tile_map

    def update(self):
        pass

    def draw(self):
        self.tile_map.draw(camera.x)
