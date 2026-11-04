"""First playable exploration prototype for 부산까지."""

from math import hypot
from time import perf_counter

import pico2d
import sdl2


TILE_SIZE = 48
PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
MAX_FRAME_TIME = 0.05

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


def can_stand(x, y):
    left = int((x - PLAYER_HALF_SIZE) // TILE_SIZE)
    right = int((x + PLAYER_HALF_SIZE) // TILE_SIZE)
    bottom = int((y - PLAYER_HALF_SIZE) // TILE_SIZE)
    top = int((y + PLAYER_HALF_SIZE) // TILE_SIZE)

    if left < 0 or right >= len(MAP[0]) or bottom < 0 or top >= len(MAP):
        return False

    return all(
        MAP[len(MAP) - 1 - row][col] != "#"
        for row in range(bottom, top + 1)
        for col in range(left, right + 1)
    )


def move_player(x, y, direction_x, direction_y, frame_time):
    length = hypot(direction_x, direction_y)
    if length == 0:
        return x, y

    distance = WALK_SPEED * min(frame_time, MAX_FRAME_TIME)
    next_x = x + direction_x / length * distance
    next_y = y + direction_y / length * distance

    # Resolve each axis separately so the player can slide along walls.
    if can_stand(next_x, y):
        x = next_x
    if can_stand(x, next_y):
        y = next_y
    return x, y


def draw_world(x, y):
    pico2d.clear_canvas()
    for row, tiles in enumerate(reversed(MAP)):
        bottom = row * TILE_SIZE
        for col, tile in enumerate(tiles):
            left = col * TILE_SIZE
            color = (70, 82, 94) if tile == "#" else (32, 43, 49)
            pico2d.draw_rectangle(
                left, bottom, left + TILE_SIZE - 2, bottom + TILE_SIZE - 2,
                *color, filled=True,
            )

    pico2d.draw_rectangle(
        x - PLAYER_HALF_SIZE, y - PLAYER_HALF_SIZE,
        x + PLAYER_HALF_SIZE - 1, y + PLAYER_HALF_SIZE - 1,
        222, 180, 89, filled=True,
    )
    pico2d.update_canvas()


def main():
    pico2d.open_canvas(WIDTH, HEIGHT, sync=True)
    x, y = SPAWN
    previous_time = perf_counter()
    try:
        while True:
            if any(
                event.type == sdl2.SDL_QUIT
                or (event.type == sdl2.SDL_KEYDOWN and event.key == sdl2.SDLK_ESCAPE)
                for event in pico2d.get_events()
            ):
                break

            keys = sdl2.SDL_GetKeyboardState(None)
            horizontal = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
            vertical = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
            now = perf_counter()
            x, y = move_player(x, y, horizontal, vertical, now - previous_time)
            previous_time = now
            draw_world(x, y)
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
