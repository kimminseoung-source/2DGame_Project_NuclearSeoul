"""Player movement and sprite animation."""

from math import hypot

import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
SNEAK_SPEED = 85
BASE_MOVEMENT_RATE = 0.7
MAX_FRAME_TIME = 0.05
MOVEMENT_FRAME_WIDTH = 77
ACTION_FRAME_WIDTH = 96
FRAME_HEIGHT = 58
WALK_FRAME_TIME = 0.12
SNEAK_FRAME_TIME = 0.15
WALK_CYCLE = (1, 2, 3, 2)


class Player:
    def __init__(self, x, y, tile_map, sprites):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.sprites = sprites
        self.sneaking = False
        self.direction = 1
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
        if direction_x:
            self.direction = direction_x
        if direction_x == direction_y == 0:
            self.walk_time = 0.0
            return

        step_time = min(frame_time, MAX_FRAME_TIME)
        speed = SNEAK_SPEED if self.sneaking else WALK_SPEED
        movement_time = step_time * BASE_MOVEMENT_RATE * speed_multiplier
        distance_per_axis = speed * movement_time / hypot(direction_x, direction_y)
        next_x = self.x + direction_x * distance_per_axis
        next_y = self.y + direction_y * distance_per_axis
        old_position = self.x, self.y

        # Resolve each axis separately so the player can slide along walls.
        if self.tile_map.can_stand(next_x, self.y, PLAYER_HALF_SIZE):
            self.x = next_x
        if self.tile_map.can_stand(self.x, next_y, PLAYER_HALF_SIZE):
            self.y = next_y

        if (self.x, self.y) != old_position:
            self.walk_time += movement_time
        else:
            self.walk_time = 0.0

    def start_pickup(self):
        self.walk_time = 0.0

    def draw(self, camera_x=0):
        action = "sneak" if self.sneaking else "walk"
        frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
        frame = 0
        if self.walk_time:
            frame = WALK_CYCLE[int(self.walk_time / frame_time) % len(WALK_CYCLE)]
        self.draw_frame(action, frame, camera_x)

    def draw_frame(self, action, frame, camera_x):
        row = int(self.direction > 0)
        image = self.sprites[action]
        width = ACTION_FRAME_WIDTH if action == "action" else MOVEMENT_FRAME_WIDTH
        image.clip_draw(
            frame * width, image.h - (row + 1) * FRAME_HEIGHT,
            width, FRAME_HEIGHT,
            self.x - camera_x, self.y - 12 + FRAME_HEIGHT / 2,
        )
