"""Player movement and sprite animation."""

from math import hypot

import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
SNEAK_SPEED = 85
MAX_FRAME_TIME = 0.05
FRAME_WIDTH = 160
FRAME_HEIGHT = 224
FRAME_COUNT = 6
DRAW_HEIGHT = 50
DRAW_WIDTH = 36
IDLE_FRAME_TIME = 0.18
WALK_FRAME_TIME = 0.08
SNEAK_ANIMATION_RATE = 0.8
# Pixel bounds from the top-left of the pickup sprite sheet, in facing order.
PICKUP_FRAMES = (
    (219, 186, 473, 526),
    (769, 187, 1078, 522),
    (175, 785, 490, 1123),
    (781, 792, 1063, 1127),
)


class Player:
    def __init__(self, x, y, tile_map, idle_image, pickup_image, walk_image, sneak_image):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.idle_image = idle_image
        self.pickup_image = pickup_image
        self.walk_image = walk_image
        self.sneak_image = sneak_image
        self.sneaking = False
        self.direction = 0
        self.walk_time = 0.0
        self.idle_time = 0.0

    def update(self, frame_time):
        keys = sdl2.SDL_GetKeyboardState(None)
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        direction_x = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        direction_y = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        length = hypot(direction_x, direction_y)
        step_time = min(frame_time, MAX_FRAME_TIME)
        if length == 0:
            self.update_idle(step_time)
            return

        if direction_x:
            self.direction = 2 if direction_x > 0 else 1
        else:
            self.direction = 3 if direction_y > 0 else 0

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
            self.idle_time = 0.0
            animation_rate = SNEAK_ANIMATION_RATE if self.sneaking else 1.0
            self.walk_time += step_time * animation_rate
        else:
            self.update_idle(step_time)

    def update_idle(self, step_time):
        self.walk_time = 0.0
        self.idle_time = (self.idle_time + step_time) % (IDLE_FRAME_TIME * FRAME_COUNT)

    def start_pickup(self):
        self.walk_time = 0.0
        self.idle_time = 0.0

    def draw_pickup(self):
        left, top, right, bottom = PICKUP_FRAMES[self.direction]
        height = 34
        width = round(height * (right - left) / (bottom - top))
        self.pickup_image.clip_draw(
            left, self.pickup_image.h - bottom, right - left, bottom - top,
            self.x, self.y - 11 + height / 2, width, height,
        )

    def draw(self):
        if self.walk_time:
            image = self.sneak_image if self.sneaking else self.walk_image
            frame = int(self.walk_time / WALK_FRAME_TIME) % FRAME_COUNT
        else:
            image = self.idle_image
            frame = int(self.idle_time / IDLE_FRAME_TIME) % FRAME_COUNT
        row_bottom = (self.direction + 1) * FRAME_HEIGHT
        image.clip_draw(
            frame * FRAME_WIDTH, image.h - row_bottom,
            FRAME_WIDTH, FRAME_HEIGHT, self.x,
            self.y - PLAYER_HALF_SIZE + DRAW_HEIGHT / 2, DRAW_WIDTH, DRAW_HEIGHT,
        )
