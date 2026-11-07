"""Exploration map, collision, and floor rendering."""

import pico2d


TILE_SIZE = 48

# Map rows are written from top to bottom.
MAP = (
    "################################",
    "#......####...........####.....#",
    "#..............................#",
    "#......####.#########....###...#",
    "#...........#########....###...#",
    "#...........#########..........#",
    "#......##...#########..........#",
    "#..............................#",
    "#......####...........####.....#",
    "################################",
)
WIDTH = 16 * TILE_SIZE
HEIGHT = len(MAP) * TILE_SIZE
SPAWN = (TILE_SIZE * 2.5, TILE_SIZE * 2.5)
SUPPLY = (TILE_SIZE * 6.5, TILE_SIZE * 2.5)
EXIT = (TILE_SIZE * 29.5, TILE_SIZE * 2.5)


class TileMap:
    width = len(MAP[0]) * TILE_SIZE

    def can_stand(self, x, y, half_size):
        left = int((x - half_size) // TILE_SIZE)
        right = int((x + half_size) // TILE_SIZE)
        bottom = int((y - half_size) // TILE_SIZE)
        top = int((y + half_size) // TILE_SIZE)

        if left < 0 or right >= len(MAP[0]) or bottom < 0 or top >= len(MAP):
            return False

        return all(
            MAP[len(MAP) - 1 - row][col] != "#"
            for row in range(bottom, top + 1)
            for col in range(left, right + 1)
        )

    def draw(self, camera_x=0):
        first_col = camera_x // TILE_SIZE
        last_col = (camera_x + WIDTH - 1) // TILE_SIZE
        for row, tiles in enumerate(reversed(MAP)):
            bottom = row * TILE_SIZE
            for col in range(first_col, last_col + 1):
                tile = tiles[col]
                left = col * TILE_SIZE - camera_x
                if tile == "#":
                    color = (63, 73, 86)
                else:
                    color = (27, 37, 44) if (row + col) % 2 else (30, 40, 47)
                pico2d.draw_rectangle(
                    left, bottom, left + TILE_SIZE - 2, bottom + TILE_SIZE - 2,
                    *color, filled=True,
                )
