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

SNEAK_FRAME_TIME = 0.15
SNEAK_TRANSITION_TIME = 0.12
SNEAK_KNEE_DROP = 4
SNEAK_LEG_HEIGHT = 22


class Player:
    def __init__(self, x, y, tile_map, image, pickup_image):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.image = image
        self.pickup_image = pickup_image
        self.sneaking = False
        self.sneak_bend = 0.0
        self.direction = 0
        self.walk_time = 0.0

    def update(self, frame_time, speed_multiplier=1.0):
        step_time = min(frame_time, MAX_FRAME_TIME)
        keys = sdl2.SDL_GetKeyboardState(None)
        sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        if self.sneaking != sneaking:
            previous_frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
            next_frame_time = SNEAK_FRAME_TIME if sneaking else WALK_FRAME_TIME
            self.walk_time *= next_frame_time / previous_frame_time
            self.sneaking = sneaking
        bend_step = step_time / SNEAK_TRANSITION_TIME
        if self.sneaking:
            self.sneak_bend = min(1.0, self.sneak_bend + bend_step)
        else:
            self.sneak_bend = max(0.0, self.sneak_bend - bend_step)
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

        speed = SNEAK_SPEED if self.sneaking else WALK_SPEED
        distance = speed * step_time * speed_multiplier
        next_x = self.x + direction_x / length * distance
        next_y = self.y + direction_y / length * distance
        old_position = self.x, self.y

        # Resolve each axis separately so the player can slide along walls.
        if self.tile_map.can_stand(next_x, self.y, PLAYER_HALF_SIZE):
            self.x = next_x
        if self.tile_map.can_stand(self.x, next_y, PLAYER_HALF_SIZE):
            self.y = next_y

        if (self.x, self.y) != old_position:
            self.walk_time += step_time * speed_multiplier
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

    def draw(self):
        frame = 0
        if self.walk_time:
            frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
            frame = WALK_FRAMES[int(self.walk_time / frame_time) % len(WALK_FRAMES)]
        left = FRAME_CENTERS[frame] - FRAME_WIDTH // 2
        bottom = self.image.h - ROW_BOTTOMS[self.direction]
        drop = round(SNEAK_KNEE_DROP * self.sneak_bend)
        if drop:
            self.draw_bent_walk(left, bottom, drop)
            return
        self.image.clip_draw(
            left, bottom,
            FRAME_WIDTH, FRAME_HEIGHT,
            self.x, self.y + 13, 32, 50,
        )

    def draw_bent_walk(self, left, bottom, drop):
        # Keep the upper body at its original scale and the boots at ground level.
        ground = self.y - 12
        source_leg_height = round(FRAME_HEIGHT * SNEAK_LEG_HEIGHT / 50)
        leg_height = SNEAK_LEG_HEIGHT - drop
        upper_height = 50 - SNEAK_LEG_HEIGHT
        facing = (0, -1, 1, 0)[self.direction]
        for row in range(leg_height):
            start = round(row * source_leg_height / leg_height)
            end = round((row + 1) * source_leg_height / leg_height)
            # The middle of the leg moves forward. The boot and hip stay aligned.
            knee = 1 - abs(2 * row / (leg_height - 1) - 1)
            offset = facing * round(knee * drop / 2)
            self.image.clip_draw(
                left, bottom + start, FRAME_WIDTH, end - start,
                self.x + offset, ground + row + 0.5, 32, 1,
            )
        self.image.clip_draw(
            left, bottom + source_leg_height, FRAME_WIDTH, FRAME_HEIGHT - source_leg_height,
            self.x, ground + leg_height + upper_height / 2, 32, upper_height,
        )
