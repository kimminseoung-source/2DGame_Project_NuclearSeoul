"""The infected: senses (sight cone, hearing, memory), the poised hang-back, the alerted turn,
and the warning -> strike -> recover attack. Rules from Project Zomboid's public rules and its
state files (docs/research/ZOMBOID_REA_ANALYSIS.md); the numbers are ours."""

import random
from math import atan2, cos, hypot, pi

import ui
from area import BLOCKS, move_body
from settings import ZOMBIE_REACH, ZOMBIE_RECOVER, ZOMBIE_SPEED, ZOMBIE_STRIKE, ZOMBIE_WINDUP
from vision_cone import ray_hit

# Infected senses (numbers are ours; the rules come from Zomboid's sight / hearing / memory).
SIGHT_RANGE = 260               # px an infected sees ahead of it
SIGHT_HALF = 1.1                # radians either side of where it faces
NOTICE_NEAR = 36                # px: so close it notices whatever way it faces
NOISE_STEP = 70                 # px the hero's footsteps carry
NOISE_ROLL = 140
NOISE_SLASH = 230
MEMORY = 3.0                    # s it keeps going to the last place it saw or heard the hero
WANDER_TURN = (2.0, 5.0)        # s between idle head turns
BLIND_WINDUP = 0.25             # s of warning when it strikes from outside the hero's sight
SEEN_BEFORE_STRIKE = 0.5        # s it must have seen the hero before it strikes (Zomboid: 0.5)
ALERT_TURN = (0.3, 0.6)         # s it spends turning toward a noise before going
GRAB_TIME = 0.9                 # s the hero is held when a blow lands with another one on him
GRAB_NEAR = ZOMBIE_REACH + 12   # px: "on the hero"


class Zombie:
    def __init__(self, look, x, y):
        self.look = look
        self.x, self.y = float(x), float(y)
        self.facing = -1
        self.heading = random.uniform(-pi, pi)     # where it looks (its own sight cone)
        self.turn_in = random.uniform(*WANDER_TURN)
        self.state = "idle"          # idle, search (going to a seen/heard spot), chase, windup...
        self.target = None           # last place it saw or heard the hero
        self.memory = 0.0
        self.timer = 0.0
        self.windup = ZOMBIE_WINDUP
        self.seen_time = 0.0         # how long it has kept the hero in sight
        self.turn_from = self.turn_to = 0.0
        self.time = random.random()
        self.walk = 0.0
        self.death = (0.0, 0.0)

    @property
    def alive(self):
        return self.state != "dead"

    def kill(self, dx, dy):
        self.state, self.timer = "dead", 0.0
        length = hypot(dx, dy) or 1
        self.death = (dx / length * 160, dy / length * 160)

    def sees(self, hero):
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = hypot(dx, dy)
        if hero.dead or dist > SIGHT_RANGE:
            return False
        if dist > NOTICE_NEAR:
            off = abs((atan2(dy, dx) - self.heading + pi) % (2 * pi) - pi)
            if off > SIGHT_HALF:
                return False
        return dist < 1 or ray_hit(self.x, self.y, dx / dist, dy / dist, BLOCKS) >= dist

    def hear(self, x, y, radius):
        if hypot(x - self.x, y - self.y) > radius:
            return
        if self.state == "idle":
            # Zomboid's alerted turn: first look toward the noise, then go.
            self.state, self.timer = "alert", random.uniform(*ALERT_TURN)
            self.turn_from, self.turn_to = self.heading, atan2(y - self.y, x - self.x)
            self.target, self.memory = (x, y), MEMORY
        elif self.state in ("search", "alert"):
            self.target, self.memory = (x, y), MEMORY

    def walk_to(self, x, y, dt):
        dx, dy = x - self.x, y - self.y
        dist = hypot(dx, dy)
        if dist < 1:
            return dist
        self.heading = atan2(dy, dx)
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        step = min(dist, ZOMBIE_SPEED * dt)
        move_body(self, dx / dist * step, dy / dist * step)
        self.walk += step / 32
        return dist

    def update(self, dt, hero, game):
        self.time += dt
        if self.state == "dead":
            self.timer += dt
            move_body(self, self.death[0] * dt, self.death[1] * dt)
            self.death = (self.death[0] * 0.9, self.death[1] * 0.9)
            return None
        dx, dy = hero.x - self.x, hero.y - self.y
        dist = hypot(dx, dy)
        event = None
        if not game.senses:
            if self.state in ("idle", "search") and dist < 300:          # the old rule
                self.state = "chase"
        elif self.state in ("idle", "alert", "search", "chase", "poised"):
            if self.sees(hero):
                self.seen_time += dt
                if self.state != "poised":
                    self.state = "chase"
                self.target, self.memory = (hero.x, hero.y), MEMORY
            else:
                self.seen_time = 0.0
                if self.state in ("chase", "poised"):
                    self.state = "search"                                # lost sight: go where it was
        if self.state == "idle":
            self.turn_in -= dt
            if self.turn_in <= 0:                                        # look around now and then
                self.heading += random.uniform(-1.6, 1.6)
                self.facing = 1 if cos(self.heading) >= 0 else -1
                self.turn_in = random.uniform(*WANDER_TURN)
        elif self.state == "alert":
            self.timer -= dt
            turn = (self.turn_to - self.turn_from + pi) % (2 * pi) - pi
            self.heading = self.turn_from + turn * max(0.0, 1 - self.timer / ALERT_TURN[1])
            self.facing = 1 if cos(self.heading) >= 0 else -1
            if self.timer <= 0:
                self.heading, self.state = self.turn_to, "search"
        elif self.state == "search":
            self.memory -= dt
            if self.walk_to(*self.target, dt) < 6 or self.memory <= 0:
                self.state, self.turn_in = "idle", 0.6                   # nothing here: give up
        elif self.state in ("chase", "poised"):
            if dist <= ZOMBIE_REACH and game.senses and self.seen_time < SEEN_BEFORE_STRIKE:
                self.state = "poised"            # just spotted: hang back, poised (Zomboid 0.5 s)
                self.heading = atan2(dy, dx)
                self.facing = 1 if dx > 0 else -1
            elif dist <= ZOMBIE_REACH:
                # From outside the hero's sight the warning is short (Zomboid: from the side
                # and behind they are far more dangerous).
                blind = game.senses and not game.hero_sees(self)
                self.windup = BLIND_WINDUP if blind else ZOMBIE_WINDUP
                self.state, self.timer = "windup", self.windup
                self.heading = atan2(dy, dx)
            else:
                self.state = "chase"
                self.walk_to(hero.x, hero.y, dt)
        elif self.state in ("windup", "strike", "recover"):
            self.timer -= dt
            if self.timer <= 0:
                if self.state == "windup":
                    self.state, self.timer = "strike", ZOMBIE_STRIKE
                    if dist <= ZOMBIE_REACH + 8:
                        event = "hit"
                elif self.state == "strike":
                    self.state, self.timer = "recover", ZOMBIE_RECOVER
                else:
                    self.state = "chase"
        return event

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.state == "dead":
            if self.timer < 1.2 or int(self.timer * 12) % 2 == 0:
                self.look.draw("down", min(1.0, self.timer * 2), x, y, 1 if self.death[0] < 0 else -1)
        elif self.state == "windup":
            self.look.draw("attack", 0.25 * (1 - self.timer / self.windup), x, y, self.facing)
            ui.text_center(x, y + 66, "!", (255, 120, 80), 22)
        elif self.state == "strike":
            self.look.draw("attack", 0.45, x, y, self.facing)
        elif self.state == "recover":
            self.look.draw("attack", 0.5 + 0.5 * (1 - self.timer / ZOMBIE_RECOVER), x, y, self.facing)
        elif self.state == "poised":
            self.look.draw("attack", 0.08, x, y, self.facing)        # arms up, not yet striking
        elif self.state in ("chase", "search"):
            self.look.draw("walk", self.time, x, y, self.facing, distance=self.walk)
            if self.state == "search":
                ui.text_center(x, y + 66, "?", (220, 200, 120), 18)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)
