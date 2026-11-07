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
MOVEMENT_DIRECTIONS = {
    (0, -1): 0, (-1, 0): 1, (1, 0): 2, (0, 1): 3,
    (-1, -1): 4, (1, -1): 5, (-1, 1): 6, (1, 1): 7,
}


class Player:
    def __init__(self, x, y, tile_map, image, pickup_image, sneak_image, diagonal_images):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.image = image
        self.pickup_image = pickup_image
        self.sneak_image = sneak_image
        self.diagonal_walk, self.diagonal_sneak, self.diagonal_pickup = diagonal_images
        self.sneaking = False
        self.direction = 0
        self.walk_time = 0.0

    def update(self, frame_time, speed_multiplier=1.0):
        keys = sdl2.SDL_GetKeyboardState(None)
        sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        if self.sneaking != sneaking:
            previous_frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
            next_frame_time = SNEAK_FRAME_TIME if sneaking else WALK_FRAME_TIME
            self.walk_time *= next_frame_time / previous_frame_time
            self.sneaking = sneaking
        direction_x = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        direction_y = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        length = hypot(direction_x, direction_y)
        if length == 0:
            self.walk_time = 0.0
            return

        self.direction = MOVEMENT_DIRECTIONS[(direction_x, direction_y)]

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
        if self.direction >= 4:
            self.draw_diagonal(self.diagonal_pickup, 0)
            return
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
        height = 46
        width = round(height * (right - left) / (bottom - top))
        self.sneak_image.clip_composite_draw(
            left, self.sneak_image.h - bottom, right - left, bottom - top,
            0, flip, self.x, self.y - 12 + height / 2, width, height,
        )

    def draw(self):
        if self.direction >= 4:
            image = self.diagonal_sneak if self.sneaking else self.diagonal_walk
            frame = 0
            if self.walk_time:
                frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
                steps = SNEAK_STEPS if self.sneaking else WALK_FRAMES
                frame = steps[int(self.walk_time / frame_time) % len(steps)]
            self.draw_diagonal(image, frame)
            return
        if self.sneaking:
            self.draw_sneak()
            return
        frame = 0
        if self.walk_time:
            frame = WALK_FRAMES[int(self.walk_time / WALK_FRAME_TIME) % len(WALK_FRAMES)]
        if frame == 3 and self.direction in (0, 3):
            self.draw_reverse_step()
            return
        self.image.clip_draw(
            FRAME_CENTERS[frame] - FRAME_WIDTH // 2,
            self.image.h - ROW_BOTTOMS[self.direction],
            FRAME_WIDTH, FRAME_HEIGHT,
            self.x, self.y + 13, 32, 50,
        )

    def draw_reverse_step(self):
        # Reuse the opposite leg pose while keeping the sleeves and patch in place.
        leg_height = 89
        leg_draw_height = 18
        bottom = self.image.h - ROW_BOTTOMS[self.direction]
        ground = self.y - 12
        self.image.clip_composite_draw(
            FRAME_CENTERS[1] - FRAME_WIDTH // 2, bottom, FRAME_WIDTH, leg_height,
            0, "h", self.x, ground + leg_draw_height / 2, 32, leg_draw_height,
        )
        self.image.clip_draw(
            FRAME_CENTERS[3] - FRAME_WIDTH // 2, bottom + leg_height,
            FRAME_WIDTH, FRAME_HEIGHT - leg_height,
            self.x, ground + leg_draw_height + 16, 32, 32,
        )

    def draw_diagonal(self, image, frame):
        columns = 1 if image is self.diagonal_pickup else 4
        frame_width = image.w // columns
        draw_width = round(frame_width * 50 / FRAME_HEIGHT)
        row = self.direction - 4
        image.clip_draw(
            (frame % columns) * frame_width, image.h - (row + 1) * FRAME_HEIGHT,
            frame_width, FRAME_HEIGHT,
            self.x, self.y + 13, draw_width, 50,
        )
