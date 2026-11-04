"""Player movement and sprite animation."""

from math import hypot

import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
MAX_FRAME_TIME = 0.05
FRAME_WIDTH = 160
FRAME_HEIGHT = 248
FRAME_CENTERS = (178, 478, 777, 1074)
ROW_BOTTOMS = (283, 592, 901, 1208)
WALK_FRAMES = (1, 2, 3, 2)
WALK_FRAME_TIME = 0.12
# Pixel bounds from the top-left of the pickup sprite sheet, in facing order.
PICKUP_FRAMES = (
    (219, 186, 473, 526),
    (769, 187, 1078, 522),
    (175, 785, 490, 1123),
    (781, 792, 1063, 1127),
)


class Player:
    def __init__(self, x, y, tile_map, image, pickup_image):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.image = image
        self.pickup_image = pickup_image
        self.direction = 0
        self.walk_time = 0.0

    def update(self, frame_time):
        keys = sdl2.SDL_GetKeyboardState(None)
        direction_x = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        direction_y = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        length = hypot(direction_x, direction_y)
        if length == 0:
            self.walk_time = 0.0
            return

        if direction_x:
            self.direction = 2 if direction_x > 0 else 1
        else:
            self.direction = 3 if direction_y > 0 else 0

        step_time = min(frame_time, MAX_FRAME_TIME)
        distance = WALK_SPEED * step_time
        next_x = self.x + direction_x / length * distance
        next_y = self.y + direction_y / length * distance
        old_position = self.x, self.y

        # Resolve each axis separately so the player can slide along walls.
        if self.tile_map.can_stand(next_x, self.y, PLAYER_HALF_SIZE):
            self.x = next_x
        if self.tile_map.can_stand(self.x, next_y, PLAYER_HALF_SIZE):
            self.y = next_y

        if (self.x, self.y) != old_position:
            self.walk_time += step_time
        else:
            self.walk_time = 0.0

    def face_pickup(self, x, y):
        dx, dy = x - self.x, y - self.y
        if abs(dx) >= abs(dy) and dx:
            self.direction = 2 if dx > 0 else 1
        elif dy:
            self.direction = 3 if dy > 0 else 0
        self.walk_time = 0.0

    def draw_pickup(self):
        left, top, right, bottom = PICKUP_FRAMES[self.direction]
        height = 34
        width = round(height * (right - left) / (bottom - top))
        self.pickup_image.clip_draw(
            left, self.pickup_image.h - bottom, right - left, bottom - top,
            self.x, self.y - 11 + height / 2, width, height,
        )

    def draw(self):
        frame = 0
        if self.walk_time:
            frame = WALK_FRAMES[int(self.walk_time / WALK_FRAME_TIME) % len(WALK_FRAMES)]
        self.image.clip_draw(
            FRAME_CENTERS[frame] - FRAME_WIDTH // 2,
            self.image.h - ROW_BOTTOMS[self.direction],
            FRAME_WIDTH, FRAME_HEIGHT,
            self.x, self.y + 13, 32, 50,
        )
