"""Player movement and drawing."""

from math import hypot

import pico2d
import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
MAX_FRAME_TIME = 0.05

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


class Player:
    def __init__(self, x, y, tile_map):
        self.x, self.y = x, y
        self.tile_map = tile_map

    def update(self, frame_time):
        keys = sdl2.SDL_GetKeyboardState(None)
        direction_x = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        direction_y = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        x, y = self.x, self.y
        length = hypot(direction_x, direction_y)
        if length == 0:
            return

        distance = WALK_SPEED * min(frame_time, MAX_FRAME_TIME)
        next_x = x + direction_x / length * distance
        next_y = y + direction_y / length * distance

        # Resolve each axis separately so the player can slide along walls.
        if self.tile_map.can_stand(next_x, y, PLAYER_HALF_SIZE):
            x = next_x
        if self.tile_map.can_stand(x, next_y, PLAYER_HALF_SIZE):
            y = next_y
        self.x, self.y = x, y

    def draw(self):
        x, y = self.x, self.y
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
