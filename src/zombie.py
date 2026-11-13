"""A regular infected as a state machine (course LEC12 style, transitions.Machine).

Real-time AI: idle -> chase -> windup ("!", the tell to dodge) -> strike -> recover -> chase,
with knockback and stunned after a blow, and dead when its health runs out. (The archived
turn-based fight could set the pose directly with transition() and pause the AI.)
"""

from math import hypot

import pico2d
from transitions import Machine

import camera
import dodge
import game_clock
import ui
from tile_map import WRECK_HALF_DEPTH, WRECK_LEFT, WRECK_RIGHT, WRECK_Y


ZOMBIE_RADIUS = 10
ALERT_DISTANCE = 128
CHASE_SPEED = 38              # px/s, about 70% of the player's walk (1.7 m/s = 54 px/s)
ATTACK_REACH = 27
ATTACK_DEPTH = 15
WINDUP_TIME = 0.55            # long enough to see the "!" and dash away
MAX_HP = 9
DAMAGE = 2                    # hit points one claw takes from the hero
DEATH_TIME = 0.6
STRIKE_TIME = 0.18
SWIPE_VISIBLE_TIME = 0.075
WALK_CYCLE = (3, 4, 5, 4)
WALK_FRAME_TIME = 0.16
RECOVERY_TIME = 0.72
KNOCKBACK_TIME = 0.24
KNOCKBACK_SPEED = 220
STAGGER_TIME = 0.38
WRECK_STUN_TIME = 1.65
STATES = ["idle", "chase", "windup", "strike", "recover", "knockback", "stunned", "dead"]


class Zombie:
    def __init__(self, image, tile_map, target):
        self.image = image
        self.tile_map = tile_map
        self.target = target          # the player it hunts
        self.x, self.y = 570, WRECK_Y
        self.direction = -1
        self.push_direction = 0
        self.time_left = 0.0
        self.alerted = False
        self.walk_time = 0.0
        self.walk_distance = 0.0     # metres walked; any unit's look can drive its legs with it
        self.detour = None
        self.in_combat = False
        self.frozen = False           # paused during a hit-stop
        self.event = None             # "player_hit", "player_dodged", "wreck_hit" or "gone" (play loop)
        self.max_hp = MAX_HP
        self.hp = MAX_HP
        self.push_speed = KNOCKBACK_SPEED

        self.machine = Machine(
            model=self,
            states=STATES,
            transitions=[
                {"trigger": "notice", "source": "idle", "dest": "chase"},
                {"trigger": "reach", "source": "chase", "dest": "windup"},
                {"trigger": "swipe", "source": "windup", "dest": "strike"},
                {"trigger": "recover_now", "source": "strike", "dest": "recover"},
                {"trigger": "resume", "source": ["recover", "stunned"], "dest": "chase"},
                {"trigger": "shoved", "source": "*", "dest": "knockback"},
                {"trigger": "stun", "source": "knockback", "dest": "stunned"},
                {"trigger": "die", "source": "*", "dest": "dead"},
            ],
            initial="idle",
            auto_transitions=False,
        )

    # State entry --------------------------------------------------------------

    def on_enter_windup(self):
        self.time_left = WINDUP_TIME

    def on_enter_strike(self):
        self.time_left = STRIKE_TIME

    def on_enter_recover(self):
        self.time_left = RECOVERY_TIME

    def on_enter_knockback(self):
        self.time_left = KNOCKBACK_TIME

    def on_enter_dead(self):
        self.time_left = DEATH_TIME

    def transition(self, state, duration=0):
        """Set a pose directly (used by the turn-based fight)."""
        self.machine.set_state(state)
        self.time_left = duration

    # Exploration behaviour ----------------------------------------------------

    @property
    def alive(self):
        return self.state != "dead"

    def hurt(self, damage, direction, push_speed):
        """A blow from any weapon: lose health, then fall or get pushed back."""
        self.hp = max(0, self.hp - damage)
        self.alerted = True
        self.direction = -direction
        if not self.hp:
            self.push_direction = direction
            self.die()
            return
        self.push_speed = push_speed
        self.push_direction = direction
        self.detour = None
        self.shoved()

    def knock_back(self, direction):
        if self.state in ("knockback", "stunned", "dead"):
            return False
        self.push_direction = direction
        self.alerted = True
        self.detour = None
        self.shoved()
        return True

    def push(self, dx):
        target = self.x + dx
        wreck_edge = WRECK_LEFT - ZOMBIE_RADIUS if dx > 0 else WRECK_RIGHT + ZOMBIE_RADIUS
        crosses_edge = self.x <= wreck_edge <= target if dx > 0 else target <= wreck_edge <= self.x
        if crosses_edge and abs(self.y - WRECK_Y) < WRECK_HALF_DEPTH + ZOMBIE_RADIUS:
            self.x = wreck_edge
            return True
        if self.tile_map.can_stand(target, self.y, ZOMBIE_RADIUS):
            self.x = target
        return False

    def in_reach(self, dx, dy):
        return abs(dx) <= ATTACK_REACH and abs(dy) <= ATTACK_DEPTH

    def chase(self, dt):
        target_x, target_y = self.target.x, self.target.y
        if self.detour is not None:
            axis, clearance = self.detour
            if axis == "y" and abs(self.x - target_x) > 3:
                target_y = clearance
                if abs(self.y - clearance) > 1:
                    target_x = self.x
            elif axis == "x" and abs(self.y - target_y) > 3:
                target_x = clearance
                if abs(self.x - clearance) > 1:
                    target_y = self.y
            else:
                self.detour = None

        dx, dy = target_x - self.x, target_y - self.y
        distance = hypot(dx, dy)
        if not distance:
            return
        ratio = min(1, CHASE_SPEED * dt / distance)
        next_x, next_y = self.x + dx * ratio, self.y + dy * ratio
        before = self.x, self.y
        x_clear = self.tile_map.can_stand(next_x, self.y, ZOMBIE_RADIUS)
        if x_clear:
            self.x = next_x
            if abs(dx) > 1:
                self.direction = 1 if dx > 0 else -1
        y_clear = self.tile_map.can_stand(self.x, next_y, ZOMBIE_RADIUS)
        if y_clear:
            self.y = next_y
        if not x_clear and self.detour is None:
            side = 1 if self.y >= WRECK_Y else -1
            self.detour = "y", WRECK_Y + side * (WRECK_HALF_DEPTH + ZOMBIE_RADIUS + 2)
        elif not y_clear and self.detour is None:
            left = WRECK_LEFT - ZOMBIE_RADIUS - 2
            right = WRECK_RIGHT + ZOMBIE_RADIUS + 2
            edge = min((left, right), key=lambda x: abs(self.x - x))
            self.detour = "x", edge
        if before != (self.x, self.y):
            self.walk_time += dt

    def update(self):
        if self.in_combat or self.frozen or game_clock.frame_time <= 0:
            return
        self.event = None
        dt = game_clock.step()
        if self.state == "dead":
            self.time_left -= dt
            self.push(self.push_direction * 40 * dt)
            if self.time_left <= 0:
                self.event = "gone"
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        if self.state == "idle":
            alert_distance = ALERT_DISTANCE * (0.45 if self.target.sneaking else 1)
            if not self.alerted and hypot(dx, dy) > alert_distance:
                return
            self.alerted = True
            self.notice()
        if self.state == "chase":
            if self.in_reach(dx, dy):
                self.direction = -1 if dx < 0 else 1
                self.detour = None
                self.reach()
            else:
                self.chase(dt)
            return

        step = min(dt, self.time_left)
        self.time_left -= step
        if self.state == "windup":
            if not self.time_left:
                self.swipe()
                if self.in_reach(dx, dy) and dx * self.direction >= 0:
                    self.event = "player_hit"
                elif dodge.is_perfect(self.target, dx, dy, ATTACK_REACH, ATTACK_DEPTH):
                    self.event = "player_dodged"
        elif self.state == "strike":
            if not self.time_left:
                self.recover_now()
        elif self.state == "knockback":
            if self.push(self.push_direction * self.push_speed * step):
                self.stun()
                self.time_left = WRECK_STUN_TIME
                self.event = "wreck_hit"
            elif not self.time_left:
                self.stun()
                self.time_left = STAGGER_TIME
        elif not self.time_left:
            self.resume()

    # Draw ---------------------------------------------------------------------

    def portrait_clip(self):
        """Source rectangle of the idle frame, cropped to head and torso."""
        return self.image, 20, 20, 46, 38

    def draw(self):
        x = self.x - camera.x
        if self.state == "windup":
            frame = 1
        elif self.state == "strike":
            frame = 6 if self.time_left > STRIKE_TIME - SWIPE_VISIBLE_TIME else 7
        elif self.state == "chase":
            frame = WALK_CYCLE[int(self.walk_time / WALK_FRAME_TIME) % len(WALK_CYCLE)]
        elif self.state in ("stunned", "dead"):
            frame = 2
        else:
            frame = 0
        if self.state == "dead":
            # Topple backwards and fade by blinking.
            if int(self.time_left * 20) % 2 == 0:
                tilt = (1 - self.time_left / DEATH_TIME) * 1.4 * self.push_direction
                self.image.clip_composite_draw(frame * 84, 0, 84, 58, -tilt, "h" if self.direction < 0 else "",
                                               x, self.y - 12 + 29 - 14 * (1 - self.time_left / DEATH_TIME), 84, 58)
            return
        self.image.clip_composite_draw(
            frame * 84, 0, 84, 58, 0, "h" if self.direction < 0 else "",
            x, self.y - 12 + 29, 84, 58,
        )
        if frame == 6:
            self.draw_swipe(x)
        if self.state == "windup":
            ui.text(x - 4, self.y + 48, "!", (255, 153, 91))

    def draw_swipe(self, x):
        direction = self.direction
        y = self.y
        for offset in (0, 4, 8):
            pico2d.draw_line(
                x + 22 * direction, y + 20 - offset,
                x + 34 * direction, y + 16 - offset, 213, 205, 181,
            )
            pico2d.draw_line(
                x + 34 * direction, y + 16 - offset,
                x + 37 * direction, y + 8 - offset, 151, 140, 124,
            )
