"""The player character as a state machine (course LEC12 style, transitions.Machine).

States: IDLE, WALK, SNEAK, DASH, PICKUP, SWING (the weapon's combo, real-time), and
COMBAT, kept for the archived turn-based fight. update() changes state and position,
draw() only draws.
"""

from math import hypot

import pico2d
import sdl2
from transitions import Machine

import camera
import game_clock
import weapon
from nav import PX_PER_M_X, metres


PLAYER_HALF_SIZE = 11
# Leg cycles cover 1.30 m (walk) and 1.09 m (sneak) of ground, measured from how fast the
# planted foot slides back in Blender. At these speeds the legs play 1.7x and 1.2x as fast
# as authored: a brisk walk and a careful sneak, both still natural, feet planted.
WALK_SPEED_M = 2.0           # metres per second
SNEAK_SPEED_M = 1.3
RUN_SPEED_M = 4.8            # Shift held while moving
DASH_SPEED = 340
DASH_DURATION = 0.14
DASH_COOLDOWN = 0.45
PICKUP_CONTACT = 0.28
PICKUP_DURATION = 0.58
HURT_TIME = 0.3              # seconds the hit reaction shows
HURT_PUSH = 90               # px/s the blow pushes the hero back while hurt
FREE_STATES = ["IDLE", "WALK", "SNEAK"]


class Player:
    def __init__(self, x, y, tile_map, look):
        self.x, self.y = x, y
        self.tile_map = tile_map
        self.look = look         # character_look: draws poses, whatever the art
        self.sneaking = False
        self.running = False
        self.direction = 1
        self.walk_time = 0.0     # seconds spent moving (0 while standing)
        self.walk_distance = 0.0 # metres walked, drives the leg cycle so feet never slide
        self.idle_time = 0.0
        self.dash_time = 0.0
        self.dash_cooldown = 0.0
        self.dash_direction = (0.0, 0.0)
        self.dash_age = float("inf")   # seconds since the last dash started (perfect dodge)
        self.counter_time = 0.0        # a landed blow is a counter while this runs (dodge.py)
        self.counter_target = None     # the enemy whose blow was perfectly dodged
        self.afterimage = 0.0          # 0..1, set by the play loop during the time warp
        self.afterimages = []          # recent (x, y) for the warp's after-images
        self.afterimage_time = 0.0
        self.ghost = None              # (x, y, alpha) while drawing an after-image
        self.charging = False          # holding the time-warp charge in place (set by the play loop)
        self.pickup_time = 0.0
        self.swing = None        # the MeleeAttack in progress
        self.weapon = weapon.MACHETE
        self.combo_queued = False
        self.hurt_time = 0.0
        self.hurt_direction = 0
        self.speed_multiplier = 1.0
        self.frozen = False      # set when the run is over
        self.combat = None       # the fight that moves this character, if any
        self.events = []         # "pickup" and "attack_contact", read by the play loop

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
                {"trigger": "attack", "source": FREE_STATES, "dest": "SWING"},
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
        self.dash_age = 0.0
        self.dash_time = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN
        self.sneaking = False
        self.walk_time = 0.0

    def on_enter_PICKUP(self):
        self.pickup_time = 0.0
        self.walk_time = 0.0

    def on_enter_SWING(self):
        self.swing = weapon.MeleeAttack(self.weapon.swings[0], (self.direction, 0), 0)
        self.combo_queued = False
        self.walk_time = 0.0

    def on_exit_SWING(self):
        self.swing = None
        self.combo_queued = False

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

    def start_finisher(self):
        """The time-warp release: the weapon's finisher, marked to loose a flurry."""
        if self.state not in FREE_STATES:
            return False
        self.attack()
        index = len(self.weapon.swings) - 1          # no combo continues after it
        self.swing = weapon.MeleeAttack(self.weapon.finisher, (self.direction, 0), index)
        self.swing.flurry = True
        return True

    def start_swing(self):
        """Attack, or queue the combo's next swing if one is already under way."""
        if self.state in FREE_STATES:
            self.attack()
        elif self.state == "SWING" and self.swing.combo_index + 1 < len(self.weapon.swings)                 and self.swing.elapsed >= self.swing.swing.contact * 0.5:
            self.combo_queued = True

    @property
    def invulnerable(self):
        """A dash slips through blows."""
        return self.state == "DASH"

    def take_hit(self, from_direction):
        """Show the hit reaction and slide back a little; the play loop takes the health."""
        self.hurt_time = HURT_TIME
        self.hurt_direction = from_direction

    @staticmethod
    def movement_direction(keys):
        return (
            keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A],
            keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S],
        )

    # Update -------------------------------------------------------------------

    def update(self):
        # The hero runs on its own clock: faster than the world during the time warp.
        dt = game_clock.hero_frame_time
        if dt <= 0:
            return
        self.record_afterimage(dt)
        self.idle_time += dt
        if self.state == "COMBAT":
            return
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.dash_age += dt
        self.counter_time = max(0.0, self.counter_time - dt)
        step = game_clock.hero_step()
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
            lunge_x, lunge_y = self.swing.lunge_step(step)
            if lunge_x or lunge_y:
                self.move(lunge_x, lunge_y)
            if self.swing.update(step):
                self.events.append("attack_contact")
            index = self.swing.combo_index
            if self.combo_queued and self.swing.recovering and index + 1 < len(self.weapon.swings):
                # Cut the recovery short and go straight into the next swing of the combo.
                self.swing = weapon.MeleeAttack(self.weapon.swings[index + 1], (self.direction, 0), index + 1)
                self.combo_queued = False
            elif self.swing.done:
                self.swing_end()
        elif not self.frozen:
            self.update_walking(step)
        if self.hurt_time > 0:
            self.hurt_time = max(0.0, self.hurt_time - step)
            self.move(self.hurt_direction * HURT_PUSH * step, 0)

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
        # Ctrl sneaks, Shift runs (2026-11-13: combat focus, Shift is the usual run key).
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LCTRL] or keys[sdl2.SDL_SCANCODE_RCTRL])
        direction_x, direction_y = self.movement_direction(keys)
        self.running = bool(keys[sdl2.SDL_SCANCODE_LSHIFT] or keys[sdl2.SDL_SCANCODE_RSHIFT]) and not self.sneaking
        if self.charging:                  # gathering power in place
            direction_x = direction_y = 0
        if direction_x == direction_y == 0:
            if self.state != "IDLE":
                self.stop()
            self.walk_time = 0.0
            return
        if self.sneaking and self.state != "SNEAK":
            self.sneak()
        elif not self.sneaking and self.state != "WALK":
            self.walk()
        movement_time = step * self.speed_multiplier
        speed = (SNEAK_SPEED_M if self.sneaking else RUN_SPEED_M if self.running else WALK_SPEED_M) * PX_PER_M_X
        distance_per_axis = speed * movement_time / hypot(direction_x, direction_y)
        old = (self.x, self.y)
        if self.move(direction_x * distance_per_axis, direction_y * distance_per_axis):
            self.walk_time += movement_time
            self.walk_distance += metres(old, (self.x, self.y))
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

    AFTERIMAGE_EVERY = 0.035     # seconds between after-image positions
    AFTERIMAGE_COUNT = 3

    def record_afterimage(self, dt):
        if self.afterimage <= 0:
            self.afterimages.clear()
            return
        self.afterimage_time += dt
        if self.afterimage_time >= self.AFTERIMAGE_EVERY:
            self.afterimage_time = 0.0
            self.afterimages.append((self.x, self.y))
            del self.afterimages[:-self.AFTERIMAGE_COUNT]

    def draw(self):
        # Time warp: faded copies of the current pose where the hero just was.
        for index, (x, y) in enumerate(self.afterimages):
            if (x, y) != (self.x, self.y):
                self.ghost = (x, y, self.afterimage * 0.18 * (index + 1))
                self.draw_state()
        self.ghost = None
        self.draw_state()

    def draw_state(self):
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
        elif self.hurt_time > 0:
            self.draw_pose("hurt", 1 - self.hurt_time / HURT_TIME)
        else:
            self.draw_body()

    def draw_swing(self, swing):
        sheet = getattr(getattr(swing, "swing", None), "sheet", "swing")   # MeleeAttack or archived BatSwing
        if getattr(swing, "lunge_from", None):
            self.draw_lunge_ghosts(swing, sheet)
        self.draw_pose(sheet, swing.progress, swing.contact)
        if self.ghost is None:
            swing.draw_trail(self, camera.x)

    def draw_dash(self):
        progress = 1 - self.dash_time / DASH_DURATION
        if progress >= 0.24:
            self.draw_dash_trail(1 - progress)
        self.draw_pose("walk", progress * 0.36)

    def draw_body(self):
        if self.charging:
            # The finisher's raised blade, held while the charge builds.
            finisher = self.weapon.finisher
            contact = finisher.contact / finisher.duration
            self.draw_pose(finisher.sheet, contact * 0.8, contact)
            return
        if not self.walk_time:
            # Holding Ctrl crouches at once, even before moving.
            self.draw_pose("sneak_idle" if self.sneaking else "idle", self.idle_time)
        else:
            pose = "sneak" if self.sneaking else "run" if self.running else "walk"
            self.draw_pose(pose, self.walk_time, distance=self.walk_distance)

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

    LUNGE_GHOST_TIME = 0.16    # s after the lunge starts that its after-images stay

    def draw_lunge_ghosts(self, swing, sheet):
        """Faded copies of the hero along a counter's lunge, so the jump reads as speed."""
        fade = 1 - swing.elapsed / self.LUNGE_GHOST_TIME
        if fade <= 0:
            return
        from_x, from_y = swing.lunge_from
        for share, alpha in ((0.0, 0.35), (0.5, 0.55)):
            x = from_x + (self.x - from_x) * share
            y = from_y + (self.y - from_y) * share
            self.look.draw(sheet, swing.progress, x - camera.x, y - 12, self.direction,
                           contact=swing.contact, alpha=alpha * fade)

    def portrait_clip(self):
        """Source rectangle of the right-facing idle frame, cropped to head and torso."""
        return self.look.portrait_clip()

    def pose_anchor(self):
        """Screen point the look draws the feet at; effects tied to the sprite use it too."""
        return self.x - camera.x, self.y - 12

    def draw_pose(self, pose, time, contact=None, distance=None):
        if self.ghost is not None:
            x, y, alpha = self.ghost
            self.look.draw(pose, time, x - camera.x, y - 12, self.direction,
                           contact=contact, distance=distance, alpha=alpha)
            return
        self.look.draw(pose, time, *self.pose_anchor(), self.direction,
                       contact=contact, distance=distance)
