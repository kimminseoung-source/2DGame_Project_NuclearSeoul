"""First playable exploration prototype for 부산까지."""

from math import hypot
from pathlib import Path
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
SUPPLY = (TILE_SIZE * 5.5, TILE_SIZE * 3.5)
EXIT = (TILE_SIZE * 13.5, TILE_SIZE * 8.5)
PLAYER_PIXELS = (
    "...hhhh...",
    "..hhhhhh..",
    "..hvvvvh..",
    "..hvvvvh..",
    "...hmmh...",
    "..jjjjjj..",
    ".jjjjjjjj.",
    ".j.jjjj.j.",
    "...jjjj...",
    "...b..b...",
    "..bb..bb..",
)
PLAYER_COLORS = {
    "h": (217, 175, 91), "v": (41, 76, 85), "m": (138, 177, 168),
    "j": (144, 129, 78), "b": (78, 92, 101),
}


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


def draw_player(x, y):
    # A small pixel sprite, anchored at the centre of the collision box.
    for row, pixels in enumerate(PLAYER_PIXELS):
        for col, pixel in enumerate(pixels):
            if pixel != ".":
                left = x - 15 + col * 3
                bottom = y + 18 - row * 3
                pico2d.draw_rectangle(
                    left, bottom, left + 2, bottom + 2,
                    *PLAYER_COLORS[pixel], filled=True,
                )


def interact(x, y, has_filter):
    if not has_filter and hypot(x - SUPPLY[0], y - SUPPLY[1]) <= 34:
        return True, False, "Filter collected. Find the green exit."
    if hypot(x - EXIT[0], y - EXIT[1]) <= 34:
        if has_filter:
            return True, True, "Shelter reached! Press R to retry."
        return False, False, "Collect the filter before leaving."
    return has_filter, False, "Move closer to the filter or exit."


def draw_world(x, y, has_filter, finished, message, font):
    pico2d.clear_canvas()
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

    ex, ey = EXIT
    pico2d.draw_rectangle(ex - 17, ey - 19, ex + 17, ey + 19, 62, 169, 128, filled=True)
    pico2d.draw_rectangle(ex - 12, ey - 15, ex + 12, ey + 13, 23, 66, 61, filled=True)
    font.draw(ex - 16, ey - 30, "EXIT", (135, 231, 185))
    if not has_filter:
        sx, sy = SUPPLY
        pico2d.draw_rectangle(sx - 10, sy - 13, sx + 10, sy + 12, 235, 184, 82, filled=True)
        pico2d.draw_rectangle(sx - 8, sy - 4, sx + 8, sy + 3, 76, 57, 37, filled=True)
        font.draw(sx - 23, sy - 25, "FILTER", (252, 218, 143))

    draw_player(x, y)
    pico2d.draw_rectangle(0, HEIGHT, WIDTH - 1, HEIGHT + 63, 15, 23, 31, filled=True)
    font.draw(16, HEIGHT + 44, "WASD Move   E Interact   Esc Quit", (181, 197, 209))
    font.draw(16, HEIGHT + 18, message, (133, 231, 184) if finished else (245, 222, 169))
    font.draw(WIDTH - 133, HEIGHT + 44, f"Filter {int(has_filter)}/1", (245, 222, 169))
    pico2d.update_canvas()


def main():
    pico2d.open_canvas(WIDTH, HEIGHT + 64, sync=True)
    x, y = SPAWN
    has_filter = finished = False
    message = "Find the filter and reach the next shelter."
    previous_time = perf_counter()
    try:
        font_path = Path(pico2d.__file__).parent / "data" / "ConsolaMalgun.ttf"
        font = pico2d.load_font(str(font_path), 16)
        while True:
            for event in pico2d.get_events():
                if event.type == sdl2.SDL_QUIT:
                    return
                if event.type != sdl2.SDL_KEYDOWN:
                    continue
                if event.key == sdl2.SDLK_ESCAPE:
                    return
                if event.key == sdl2.SDLK_e and not finished:
                    has_filter, finished, message = interact(x, y, has_filter)
                if event.key == sdl2.SDLK_r and finished:
                    x, y = SPAWN
                    has_filter = finished = False
                    message = "Find the filter and reach the next shelter."

            keys = sdl2.SDL_GetKeyboardState(None)
            horizontal = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
            vertical = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
            now = perf_counter()
            if not finished:
                x, y = move_player(x, y, horizontal, vertical, now - previous_time)
            previous_time = now
            draw_world(x, y, has_filter, finished, message, font)
    finally:
        pico2d.close_canvas()


if __name__ == "__main__":
    main()
