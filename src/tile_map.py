"""Exploration map, collision, and floor rendering."""

import pico2d


TILE_SIZE = 48

# Map rows are written from top to bottom.
MAP = (
    "################",
    "#......#.......#",
    "#......#..###..#",
    "#.........#....#",
    "#..###....#....#",
    "#..#......##...#",
    "#..#...........#",
    "#......###.....#",
    "#..............#",
    "################",
)
WIDTH = len(MAP[0]) * TILE_SIZE
HEIGHT = len(MAP) * TILE_SIZE
SPAWN = (TILE_SIZE * 2.5, TILE_SIZE * 1.5)
SUPPLY = (TILE_SIZE * 5.5, TILE_SIZE * 3.5)
EXIT = (TILE_SIZE * 13.5, TILE_SIZE * 8.5)


class TileMap:
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

    def draw(self):
        for row, tiles in enumerate(reversed(MAP)):
            bottom = row * TILE_SIZE
            for col, tile in enumerate(tiles):
                left = col * TILE_SIZE
                if tile == "#":
                    color = (63, 73, 86)
                else:
                    color = (27, 37, 44) if (row + col) % 2 else (30, 40, 47)
                pico2d.draw_rectangle(
                    left, bottom, left + TILE_SIZE - 2, bottom + TILE_SIZE - 2,
                    *color, filled=True,
                )
