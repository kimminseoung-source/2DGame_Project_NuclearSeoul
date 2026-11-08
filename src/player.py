"""Player movement and sprite animation."""

from math import hypot

import pico2d
import sdl2


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
SNEAK_SPEED = 85
BASE_MOVEMENT_RATE = 0.7
MAX_FRAME_TIME = 0.05
DASH_SPEED = 340
DASH_DURATION = 0.14
DASH_COOLDOWN = 0.45
MOVEMENT_FRAME_WIDTH = 77
ACTION_FRAME_WIDTH = 97
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
        self.dash_time = 0.0
        self.dash_cooldown = 0.0
        self.dash_direction = (0.0, 0.0)

    @staticmethod
    def movement_direction(keys):
        return (
            keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
            keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S],
        )

    def start_dash(self):
        if self.dash_time or self.dash_cooldown:
            return
        dx, dy = self.movement_direction(sdl2.SDL_GetKeyboardState(None))
        if dx == dy == 0:
            dx = self.direction
        length = hypot(dx, dy)
        self.dash_direction = dx / length, dy / length
        self.dash_time = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN
        self.sneaking = False
        self.walk_time = 0.0

    def update(self, frame_time, speed_multiplier=1.0):
        if self.dash_time:
            step_time = min(frame_time, MAX_FRAME_TIME, self.dash_time)
            self.dash_time -= step_time
            dx, dy = self.dash_direction
            if not self.move(dx * DASH_SPEED * step_time, dy * DASH_SPEED * step_time):
                self.dash_time = 0.0
            return

        keys = sdl2.SDL_GetKeyboardState(None)
        sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        if self.sneaking != sneaking:
            previous_frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
            next_frame_time = SNEAK_FRAME_TIME if sneaking else WALK_FRAME_TIME
            self.walk_time *= next_frame_time / previous_frame_time
            self.sneaking = sneaking
        direction_x, direction_y = self.movement_direction(keys)
        if direction_x == direction_y == 0:
            self.walk_time = 0.0
            return

        step_time = min(frame_time, MAX_FRAME_TIME)
        speed = SNEAK_SPEED if self.sneaking else WALK_SPEED
        movement_time = step_time * BASE_MOVEMENT_RATE * speed_multiplier
        distance_per_axis = speed * movement_time / hypot(direction_x, direction_y)
        if self.move(direction_x * distance_per_axis, direction_y * distance_per_axis):
            self.walk_time += movement_time
        else:
            self.walk_time = 0.0

    def move(self, dx, dy):
        old_position = self.x, self.y
        next_x, next_y = self.x + dx, self.y + dy

        # Resolve axes separately so diagonal movement can slide along walls.
        if self.tile_map.can_stand(next_x, self.y, PLAYER_HALF_SIZE):
            self.x = next_x
        if self.tile_map.can_stand(self.x, next_y, PLAYER_HALF_SIZE):
            self.y = next_y
        return (self.x, self.y) != old_position

    def start_pickup(self):
        self.walk_time = 0.0

    def draw(self, camera_x=0):
        if self.dash_time:
            progress = 1 - self.dash_time / DASH_DURATION
            if progress < 0.24:
                self.draw_frame("sneak", 1, camera_x)
            else:
                self.draw_dash_trail(camera_x, 1 - progress)
                self.draw_frame("walk", 1 if progress < 0.65 else 3, camera_x)
            return

        action = "sneak" if self.sneaking else "walk"
        frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
        frame = 0
        if self.walk_time:
            frame = WALK_CYCLE[int(self.walk_time / frame_time) % len(WALK_CYCLE)]
        self.draw_frame(action, frame, camera_x)

    def draw_dash_trail(self, camera_x, strength):
        x, y = self.x - camera_x, self.y - 12
        dx, dy = self.dash_direction
        shade = round(60 + 62 * strength)
        for side, length in ((-2, 13), (2, 8)):
            start_x, start_y = x - 9 * dx - side * dy, y - 9 * dy + side * dx
            pico2d.draw_line(
                start_x, start_y, start_x - dx * length * strength,
                start_y - dy * length * strength, shade, shade - 10, shade - 22,
            )

    def portrait_clip(self):
        """Source rectangle of the right-facing idle frame, cropped to head and torso."""
        image = self.sprites["walk"]
        return image, 16, image.h - 2 * FRAME_HEIGHT + 20, 46, 38

    def draw_frame(self, action, frame, camera_x):
        row = int(self.direction > 0)
        image = self.sprites[action]
        width = ACTION_FRAME_WIDTH if action == "action" else MOVEMENT_FRAME_WIDTH
        image.clip_draw(
            frame * width, image.h - (row + 1) * FRAME_HEIGHT,
            width, FRAME_HEIGHT,
            self.x - camera_x, self.y - 12 + FRAME_HEIGHT / 2,
        )
