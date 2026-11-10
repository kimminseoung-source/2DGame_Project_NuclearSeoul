"""The player character as a state machine (course LEC12 style, transitions.Machine).

States: IDLE, WALK, SNEAK, DASH, PICKUP, SWING, and COMBAT while the turn-based
fight moves the character. update() changes state and position, draw() only draws.
"""

from math import hypot

import pico2d
import sdl2
from transitions import Machine

import camera
import game_clock
from bat import BAT_DURATION, BatSwing


PLAYER_HALF_SIZE = 11
WALK_SPEED = 150
SNEAK_SPEED = 85
BASE_MOVEMENT_RATE = 0.7
DASH_SPEED = 340
DASH_DURATION = 0.14
DASH_COOLDOWN = 0.45
WALK_FRAME_TIME = 0.12
SNEAK_FRAME_TIME = 0.15
PICKUP_CONTACT = 0.28
PICKUP_DURATION = 0.58
FREE_STATES = ["IDLE", "WALK", "SNEAK"]


class Player:
    def __init__(self, x, y, tile_map, look):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.look = look         # character_look: draws poses, whatever the art
        self.sneaking = False
        self.direction = 1
        self.walk_time = 0.0
        self.idle_time = 0.0
        self.dash_time = 0.0
        self.dash_cooldown = 0.0
        self.dash_direction = (0.0, 0.0)
        self.pickup_time = 0.0
        self.swing = None
        self.speed_multiplier = 1.0
        self.frozen = False      # set when the run is over
        self.combat = None       # the fight that moves this character, if any
        self.events = []         # "pickup" and "bat_contact", read by the play loop

        self.machine = Machine(
            model=self,
            states=["IDLE", "WALK", "SNEAK", "DASH", "PICKUP", "SWING", "COMBAT"],
            transitions=[
                {"trigger": "walk", "source": ["IDLE", "SNEAK"], "dest": "WALK"},
                {"trigger": "sneak", "source": ["IDLE", "WALK"], "dest": "SNEAK"},
                {"trigger": "stop", "source": ["WALK", "SNEAK"], "dest": "IDLE"},
                {"trigger": "dash", "source": FREE_STATES, "dest": "DASH"},
                {"trigger": "dash_end", "source": "DASH", "dest": "IDLE"},
                {"trigger": "pick_up", "source": FREE_STATES, "dest": "PICKUP"},
                {"trigger": "pickup_end", "source": "PICKUP", "dest": "IDLE"},
                {"trigger": "swing_bat", "source": FREE_STATES, "dest": "SWING"},
                {"trigger": "swing_end", "source": "SWING", "dest": "IDLE"},
                {"trigger": "enter_combat", "source": "*", "dest": "COMBAT"},
                {"trigger": "leave_combat", "source": "COMBAT", "dest": "IDLE"},
            ],
            initial="IDLE",
            auto_transitions=False,
        )

    # State entry --------------------------------------------------------------

    def on_enter_IDLE(self):
        self.walk_time = 0.0
        self.sneaking = False

    def on_enter_DASH(self):
        self.dash_time = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN
        self.sneaking = False
        self.walk_time = 0.0

    def on_enter_PICKUP(self):
        self.pickup_time = 0.0
        self.walk_time = 0.0

    def on_enter_SWING(self):
        self.swing = BatSwing((self.direction, 0))
        self.walk_time = 0.0

    def on_exit_SWING(self):
        self.swing = None

    def on_enter_COMBAT(self):
        self.dash_time = 0.0
        self.walk_time = 0.0
        self.sneaking = False
        self.swing = None

    # Requests from the play loop --------------------------------------------

    def busy(self):
        return self.state in ("DASH", "PICKUP", "SWING")

    def start_dash(self):
        if self.state not in FREE_STATES or self.dash_cooldown:
            return
        dx, dy = self.movement_direction(sdl2.SDL_GetKeyboardState(None))
        if dx == dy == 0:
            dx = self.direction
        length = hypot(dx, dy)
        self.dash_direction = dx / length, dy / length
        self.dash()

    def start_pickup(self):
        if self.state in FREE_STATES:
            self.pick_up()

    def start_swing(self):
        if self.state in FREE_STATES:
            self.swing_bat()

    @staticmethod
    def movement_direction(keys):
        return (
            keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
            keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S],
        )

    # Update -------------------------------------------------------------------

    def update(self):
        dt = game_clock.frame_time
        if dt <= 0:
            return
        self.idle_time += dt
        if self.state == "COMBAT":
            return
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        step = game_clock.step()
        if self.state == "DASH":
            self.update_dash(step)
        elif self.state == "PICKUP":
            previous = self.pickup_time
            self.pickup_time += step
            if previous < PICKUP_CONTACT <= self.pickup_time:
                self.events.append("pickup")
            if self.pickup_time >= PICKUP_DURATION:
                self.pickup_end()
        elif self.state == "SWING":
            if self.swing.update(step):
                self.events.append("bat_contact")
            if self.swing.elapsed >= BAT_DURATION:
                self.swing_end()
        elif not self.frozen:
            self.update_walking(step)

    def update_dash(self, step):
        step_time = min(step, self.dash_time)
        self.dash_time -= step_time
        dx, dy = self.dash_direction
        if not self.move(dx * DASH_SPEED * step_time, dy * DASH_SPEED * step_time):
            self.dash_time = 0.0
        if not self.dash_time:
            self.dash_end()

    def update_walking(self, step):
        keys = sdl2.SDL_GetKeyboardState(None)
        sneaking = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT])
        if self.sneaking != sneaking:
            # Keep the animation phase when switching between walk and sneak speeds.
            previous_frame_time = SNEAK_FRAME_TIME if self.sneaking else WALK_FRAME_TIME
            next_frame_time = SNEAK_FRAME_TIME if sneaking else WALK_FRAME_TIME
            self.walk_time *= next_frame_time / previous_frame_time
            self.sneaking = sneaking
        direction_x, direction_y = self.movement_direction(keys)
        if direction_x == direction_y == 0:
            if self.state != "IDLE":
                self.stop()
            self.sneaking = sneaking
            self.walk_time = 0.0
            return
        if sneaking and self.state != "SNEAK":
            self.sneak()
        elif not sneaking and self.state != "WALK":
            self.walk()
        movement_time = step * BASE_MOVEMENT_RATE * self.speed_multiplier
        speed = SNEAK_SPEED if sneaking else WALK_SPEED
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

    # Draw ---------------------------------------------------------------------

    def draw(self):
        if self.state == "COMBAT":
            swing = self.combat.swing_for(self) if self.combat is not None else None
            if swing is not None:
                self.draw_swing(swing)
            else:
                self.draw_body()
        elif self.state == "SWING":
            self.draw_swing(self.swing)
        elif self.state == "PICKUP":
            # Down to the floor and back up again.
            progress = self.pickup_time / PICKUP_DURATION
            self.draw_pose("pickup", 1 - abs(2 * progress - 1))
        elif self.state == "DASH":
            self.draw_dash()
        else:
            self.draw_body()

    def draw_swing(self, swing):
        self.draw_pose("swing", swing.elapsed / BAT_DURATION)
        swing.draw_trail(self, camera.x)

    def draw_dash(self):
        progress = 1 - self.dash_time / DASH_DURATION
        if progress >= 0.24:
            self.draw_dash_trail(1 - progress)
        self.draw_pose("walk", progress * 0.36)

    def draw_body(self):
        if not self.walk_time:
            self.draw_pose("idle", self.idle_time)
        else:
            self.draw_pose("sneak" if self.sneaking else "walk", self.walk_time)

    def draw_dash_trail(self, strength):
        x, y = self.x - camera.x, self.y - 12
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
        return self.look.portrait_clip()

    def draw_pose(self, pose, time):
        self.look.draw(pose, time, self.x - camera.x, self.y - 12, self.direction)
