"""The hero: WASD movement (Ctrl sneaks), the aimed slash with a short lunge, the roll, being
grabbed, being slowed by blows (Zomboid: each hit slows you, up to half speed)."""

from math import atan2, cos, hypot, sin

import sdl2

from area import HERO_START, move_body
from settings import (CHEST, HERO_HP, ROLL_COOLDOWN, ROLL_SPEED, ROLL_TIME, RUN_SPEED, SLASH_COOLDOWN,
                      SLASH_HIT, SLASH_LUNGE, SLASH_TIME)


PICKUP_TIME = 0.35          # s of the pick-up motion (2026-11-15 "간단하게")
SNEAK_SPEED = 0.45          # Ctrl held: share of the normal speed
HIT_SLOW = 0.25             # each blow taken slows the hero this much more...
MAX_SLOW = 0.5              # ...up to half speed (Zomboid's attack slow cap)
SLOW_RECOVER = 0.2          # per second back to full speed


class Hero:
    def __init__(self, look):
        self.look = look
        self.x, self.y = HERO_START
        self.facing = 1
        self.hp = HERO_HP
        self.hurt = 0.0
        self.slash = None
        self.slash_cooldown = 0.0
        self.roll = 0.0
        self.roll_dir = (1.0, 0.0)
        self.roll_cooldown = 0.0
        self.lunge = (0.0, 0.0)
        self.run_distance = 0.0
        self.time = 0.0
        self.dead = 0.0
        self.moving = False
        self.grabbed = 0.0           # held by two or more infected (only a roll breaks free)
        self.pickup = 0.0            # s left of the short pick-up motion (E)
        self.sneaking = False        # Ctrl held: slow, quiet, harder to spot
        self.slowed = 0.0            # 0..MAX_SLOW from blows taken

    @property
    def invulnerable(self):
        return self.roll > 0 or self.hurt > 0

    def noticeability(self):
        """How easily an infected that has the hero in view spots him (Zomboid: sneaking lowers it)."""
        if self.roll > 0 or self.slash:
            return 1.6
        if not self.moving:
            return 0.35
        return 0.5 if self.sneaking else 1.0

    def take_blow(self):
        self.slowed = min(MAX_SLOW, self.slowed + HIT_SLOW)

    def start_slash(self, ax, ay):
        if self.slash or self.roll > 0 or self.slash_cooldown > 0 or self.dead or self.grabbed > 0:
            return
        angle = atan2(ay - (self.y + CHEST), ax - self.x)
        self.facing = 1 if cos(angle) >= 0 else -1
        self.slash = {"time": 0.0, "angle": angle, "hit": False}
        speed = SLASH_LUNGE / SLASH_HIT * 0.5
        self.lunge = (cos(angle) * speed, sin(angle) * speed)

    def start_roll(self, mx, my):
        if self.roll > 0 or self.roll_cooldown > 0 or self.dead:
            return
        length = hypot(mx, my)
        self.roll_dir = (mx / length, my / length) if length else (float(self.facing), 0.0)
        self.roll = ROLL_TIME
        self.slash = None
        self.grabbed = 0.0           # rolling tears free

    def update(self, dt, keys, aim_x):
        self.time += dt
        self.hurt = max(0.0, self.hurt - dt)
        self.slash_cooldown = max(0.0, self.slash_cooldown - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        self.slowed = max(0.0, self.slowed - SLOW_RECOVER * dt)
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LCTRL] or keys[sdl2.SDL_SCANCODE_RCTRL])
        if self.dead:
            self.dead += dt
            return
        mx = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        my = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        self.moving = False
        if self.grabbed > 0:
            self.grabbed -= dt
            return
        if self.pickup > 0:                    # crouched for a moment, picking something up
            self.pickup -= dt
            return
        if self.roll > 0:
            self.roll -= dt
            move_body(self, self.roll_dir[0] * ROLL_SPEED * dt, self.roll_dir[1] * ROLL_SPEED * dt)
            if self.roll <= 0:
                self.roll_cooldown = ROLL_COOLDOWN
        elif self.slash:
            self.slash["time"] += dt
            move_body(self, self.lunge[0] * dt, self.lunge[1] * dt)
            self.lunge = (self.lunge[0] * 0.82, self.lunge[1] * 0.82)
            if self.slash["time"] >= SLASH_TIME:
                self.slash = None
                self.slash_cooldown = SLASH_COOLDOWN
        elif mx or my:
            length = hypot(mx, my)
            speed = RUN_SPEED * (SNEAK_SPEED if self.sneaking else 1.0) * (1 - self.slowed)
            move_body(self, mx / length * speed * dt, my / length * speed * dt)
            self.run_distance += speed * dt / 32
            self.moving = True
            if mx:
                self.facing = mx
        elif aim_x is not None:
            self.facing = 1 if aim_x >= self.x else -1

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.dead:
            self.look.draw("down", min(1.0, self.dead * 1.5), x, y, self.facing)
        elif self.hurt > 0 and int(self.hurt * 20) % 2 == 0:
            return
        elif self.pickup > 0:
            self.look.draw("pickup", 1 - self.pickup / PICKUP_TIME, x, y, self.facing)
        elif self.roll > 0:
            face = 1 if self.roll_dir[0] >= 0 else -1
            self.look.draw("run", (1 - self.roll / ROLL_TIME) * 0.5, x, y - 2, face,
                           distance=self.run_distance + (1 - self.roll / ROLL_TIME) * 3)
        elif self.slash:
            self.look.draw("swing", self.slash["time"] / SLASH_TIME, x, y, self.facing,
                           contact=SLASH_HIT / SLASH_TIME)
        elif self.moving:
            pose = "sneak" if self.sneaking else "run"
            self.look.draw(pose, self.time, x, y, self.facing, distance=self.run_distance)
        else:
            self.look.draw("sneak_idle" if self.sneaking else "idle", self.time, x, y, self.facing)
