"""The hero: WASD movement, the aimed slash with a short lunge, the roll, being grabbed."""

from math import atan2, cos, hypot, sin

import sdl2

from area import HERO_START, move_body
from settings import (CHEST, HERO_HP, ROLL_COOLDOWN, ROLL_SPEED, ROLL_TIME, RUN_SPEED, SLASH_COOLDOWN,
                      SLASH_HIT, SLASH_LUNGE, SLASH_TIME)


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

    @property
    def invulnerable(self):
        return self.roll > 0 or self.hurt > 0

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
        if self.dead:
            self.dead += dt
            return
        mx = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        my = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        self.moving = False
        if self.grabbed > 0:
            self.grabbed -= dt
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
            move_body(self, mx / length * RUN_SPEED * dt, my / length * RUN_SPEED * dt)
            self.run_distance += RUN_SPEED * dt / 32
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
        elif self.roll > 0:
            face = 1 if self.roll_dir[0] >= 0 else -1
            self.look.draw("run", (1 - self.roll / ROLL_TIME) * 0.5, x, y - 2, face,
                           distance=self.run_distance + (1 - self.roll / ROLL_TIME) * 3)
        elif self.slash:
            self.look.draw("swing", self.slash["time"] / SLASH_TIME, x, y, self.facing,
                           contact=SLASH_HIT / SLASH_TIME)
        elif self.moving:
            self.look.draw("run", self.time, x, y, self.facing, distance=self.run_distance)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)
