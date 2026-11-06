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
    ((83, 41, 245, 287), (386, 43, 551, 291), (696, 43, 861, 291), (1005, 43, 1167, 289)),
    ((93, 346, 247, 591), (384, 346, 561, 591), (698, 346, 858, 591), (1011, 346, 1164, 591)),
    ((83, 644, 228, 888), (368, 646, 547, 888), (695, 646, 855, 888), (1004, 646, 1152, 888)),
    ((89, 957, 248, 1205), (390, 958, 545, 1208), (702, 958, 859, 1208), (1008, 958, 1167, 1206)),
)
SNEAK_STEPS = (1, 3, 2, 3)
SNEAK_FRAME_TIME = 0.15


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

    def update(self, frame_time, speed_multiplier=1.0):
        keys = sdl2.SDL_GetKeyboardState(None)
        sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        if self.sneaking != sneaking:
            self.walk_time = 0.0
            self.sneaking = sneaking
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

    def draw_sneak(self):
        frame = 0
        if self.walk_time:
            frame = SNEAK_STEPS[int(self.walk_time / SNEAK_FRAME_TIME) % len(SNEAK_STEPS)]
        # The back-view step frames advance the same foot in the artwork.
        flip = "h" if self.direction == 3 and frame == 2 else ""
        if flip:
            frame = 1
        left, top, right, bottom = SNEAK_FRAMES[self.direction][frame]
        height = 43
        width = round(height * (right - left) / (bottom - top))
        self.sneak_image.clip_composite_draw(
            left, self.sneak_image.h - bottom, right - left, bottom - top,
            0, flip, self.x, self.y - 11 + height / 2, width, height,
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
