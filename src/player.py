"""Player movement and sprite animation."""

from math import hypot

import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
SNEAK_SPEED = 85
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

# Pixel bounds from the top-left, ordered down, left, right, up.
SNEAK_FRAMES = (
    (192, 131, 462, 535),
    (756, 138, 1071, 531),
    (193, 746, 482, 1141),
    (795, 737, 1064, 1141),
)


class Player:
    def __init__(self, x, y, tile_map, image, pickup_image, sneak_image):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.image = image
        self.pickup_image = pickup_image
        self.sneak_image = sneak_image
        self.sneaking = False
        self.direction = 0
        self.walk_time = 0.0

    def update(self, frame_time):
        keys = sdl2.SDL_GetKeyboardState(None)
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
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
        speed = SNEAK_SPEED if self.sneaking else WALK_SPEED
        distance = speed * step_time
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

    def start_pickup(self):
        self.walk_time = 0.0

    def draw_pickup(self):
        left, top, right, bottom = PICKUP_FRAMES[self.direction]
        height = 34
        width = round(height * (right - left) / (bottom - top))
        self.pickup_image.clip_draw(
            left, self.pickup_image.h - bottom, right - left, bottom - top,
            self.x, self.y - 11 + height / 2, width, height,
        )

    def draw_sneak(self):
        left, top, right, bottom = SNEAK_FRAMES[self.direction]
        height = 38
        width = round(height * (right - left) / (bottom - top))
        bob = int(self.walk_time / 0.2) % 2
        self.sneak_image.clip_draw(
            left, self.sneak_image.h - bottom, right - left, bottom - top,
            self.x, self.y - 11 + height / 2 + bob, width, height,
        )

    def draw(self):
        if self.sneaking:
            self.draw_sneak()
            return
        frame = 0
        if self.walk_time:
            frame = WALK_FRAMES[int(self.walk_time / WALK_FRAME_TIME) % len(WALK_FRAMES)]
        self.image.clip_draw(
            FRAME_CENTERS[frame] - FRAME_WIDTH // 2,
            self.image.h - ROW_BOTTOMS[self.direction],
            FRAME_WIDTH, FRAME_HEIGHT,
            self.x, self.y + 13, 32, 50,
        )
