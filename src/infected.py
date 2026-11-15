"""The infected: senses (sight cone, hearing, memory), the poised hang-back, the alerted turn,
and the warning -> strike -> recover attack. Rules from Project Zomboid's public rules and its
state files and decompiled rules (docs/research/ZOMBOID_REA_ANALYSIS.md parts 1-3); the numbers
are ours. Spotting is a chance, not instant: the nearer, the likelier, and a hero standing still or
sneaking is spotted far less (Zomboid's spot chance)."""

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
MEMORY = 8.0                    # s it keeps going to the last place it saw or heard the hero (was 3)
SPOT_RATE = 2.2                 # chance per second of spotting a hero in full view, right in front
SPOT_SURE = 54                  # px: this close it spots at once
SPOT_IDLE = 0.6                 # an idle (unalert) infected spots less...
SPOT_ALERT = 1.5                # ...one already searching spots more
FRONT_SOUND = 0.6               # radians: a sound this close to where it faces needs no turn
WANDER_TURN = (2.0, 5.0)        # s between idle head turns
SPOTTED_TIME = 0.8              # s the "!" stays after it spots the hero
BLIND_WINDUP = 0.25             # s of warning when it strikes from outside the hero's sight
SEEN_BEFORE_STRIKE = 0.5        # s it must have seen the hero before it strikes (Zomboid: 0.5)
ALERT_TURN = (0.3, 0.6)         # s it spends turning toward a noise before going
GRAB_TIME = 0.9                 # s the hero is held when a blow lands with another one on him
GRAB_NEAR = ZOMBIE_REACH + 12   # px: "on the hero"
STAGGER_TIME = 0.8              # s it reels after a shove
DOWN_TIME = 1.8                 # s on the ground after a shove knocks it over
DOWN_CHANCE = 0.35              # chance a shove knocks it over (Zomboid: shove, then stomp)
SHOVE_PUSH = 70                 # px/s it is pushed back
# Toughness (2026-11-16 "좀보이드처럼"): an infected that is facing the hero takes several slashes;
# each one makes it flinch (its attack is broken off) or, sometimes, knocks it down. One that is
# unaware, reeling from a shove or on the ground still dies to a single slash (helpless).
HITS = (2, 3)                   # slashes an aware infected takes
FLINCH_TIME = 0.35              # s it reels from a slash that does not kill it (not helpless)
HIT_DOWN_CHANCE = 0.2           # chance such a slash knocks it down instead
HIT_PUSH = 55                   # px/s a slash knocks it back


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
        self.spotted = 0.0           # s left of the "!" shown the moment it spots the hero
        self.seen_time = 0.0         # how long it has kept the hero in sight
        self.turn_from = self.turn_to = 0.0
        self.time = random.random()
        self.walk = 0.0
        self.death = (0.0, 0.0)
        self.push = (0.0, 0.0)
        self.health = random.randint(*HITS)

    @property
    def alive(self):
        return self.state != "dead"

    def kill(self, dx, dy):
        self.state, self.timer = "dead", 0.0
        length = hypot(dx, dy) or 1
        self.death = (dx / length * 160, dy / length * 160)

    def reel(self, from_x, from_y, push, state, time):
        """Knocked back from (from_x, from_y) into `state` (stagger, flinch or down) for `time` s;
        an attack being wound up is broken off."""
        dx, dy = self.x - from_x, self.y - from_y
        length = hypot(dx, dy) or 1
        self.push = (dx / length * push, dy / length * push)
        self.state, self.timer = state, time
        self.seen_time = 0.0
        self.target, self.memory = (from_x, from_y), MEMORY    # it knows where the blow came from

    def shoved(self, from_x, from_y):
        """Pushed by the hero: it reels or falls."""
        if random.random() < DOWN_CHANCE:
            self.reel(from_x, from_y, SHOVE_PUSH, "down", DOWN_TIME)
        else:
            self.reel(from_x, from_y, SHOVE_PUSH, "stagger", STAGGER_TIME)

    def hurt(self, from_x, from_y):
        """A slash on an aware infected: True when it was the last one it could take."""
        self.health -= 1
        if self.health <= 0:
            return True
        if random.random() < HIT_DOWN_CHANCE:
            self.reel(from_x, from_y, HIT_PUSH, "down", DOWN_TIME)
        else:
            self.reel(from_x, from_y, HIT_PUSH, "flinch", FLINCH_TIME)
        return False

    @property
    def helpless(self):
        """Reeling, on the ground, or unaware of the hero: a sure, quiet finisher."""
        return self.state in ("idle", "alert", "search", "stagger", "down")

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

    def hear(self, x, y, radius, origin=None):
        """A noise of `radius` px; (x, y) is where it seems to come from (a muffled sound is
        misplaced), `origin` where it really is - the distance check uses the real spot."""
        ox, oy = origin or (x, y)
        if hypot(ox - self.x, oy - self.y) > radius:
            return
        toward = atan2(y - self.y, x - self.x)
        ahead = abs((toward - self.heading + pi) % (2 * pi) - pi) <= FRONT_SOUND
        if self.state == "idle" and ahead:                   # in front: no need to turn, just go
            self.state, self.target, self.memory = "search", (x, y), MEMORY
        elif self.state == "idle":
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
        self.spotted = max(0.0, self.spotted - dt)
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
        elif self.state in ("idle", "alert", "search") and self.sees(hero):
            # In view but not yet spotted: a chance each moment (Zomboid's spot chance).
            rate = SPOT_RATE * max(0.0, 1 - dist / SIGHT_RANGE) * hero.noticeability()
            rate *= SPOT_IDLE if self.state == "idle" else SPOT_ALERT
            if dist <= SPOT_SURE or random.random() < rate * dt:
                self.state, self.seen_time = "chase", 0.0
                self.target, self.memory = (hero.x, hero.y), MEMORY
        elif self.state in ("chase", "poised"):
            if self.sees(hero):
                self.seen_time += dt
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
        elif self.state in ("stagger", "flinch", "down"):
            self.timer -= dt
            if self.state != "down" or self.timer > DOWN_TIME - 0.25:
                move_body(self, self.push[0] * dt, self.push[1] * dt)
                self.push = (self.push[0] * 0.88, self.push[1] * 0.88)
            if self.timer <= 0:
                self.state, self.seen_time = "chase", SEEN_BEFORE_STRIKE   # back up, angry
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

    show_marks = True        # "!" / "?" over the head
    blink_corpse = True      # the corpse blinks; off in the realistic look (bodies stay)

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        if self.state == "dead":
            if not self.blink_corpse or self.timer < 1.2 or int(self.timer * 12) % 2 == 0:
                self.look.draw("down", min(1.0, self.timer * 2), x, y, 1 if self.death[0] < 0 else -1)
        elif self.state == "windup":
            self.look.draw("attack", 0.25 * (1 - self.timer / self.windup), x, y, self.facing)
            if self.show_marks:
                ui.text_center(x, y + 66, "!", (255, 120, 80), 22)
        elif self.state == "strike":
            self.look.draw("attack", 0.45, x, y, self.facing)
        elif self.state == "recover":
            self.look.draw("attack", 0.5 + 0.5 * (1 - self.timer / ZOMBIE_RECOVER), x, y, self.facing)
        elif self.state == "poised":
            self.look.draw("attack", 0.08, x, y, self.facing)        # arms up, not yet striking
        elif self.state in ("stagger", "flinch"):
            whole = STAGGER_TIME if self.state == "stagger" else FLINCH_TIME
            self.look.draw("hurt", 1 - self.timer / whole, x, y, self.facing)
        elif self.state == "down":                                   # falls, lies, gets up
            t = DOWN_TIME - self.timer
            progress = min(1.0, t / 0.35) if self.timer > 0.4 else self.timer / 0.4
            self.look.draw("down", progress, x, y, self.facing)
        elif self.state in ("chase", "search"):
            self.look.draw("walk", self.time, x, y, self.facing, distance=self.walk)
            if self.state == "search":
                if self.show_marks:
                    ui.text_center(x, y + 66, "?", (220, 200, 120), 18)
        else:
            self.look.draw("idle", self.time, x, y, self.facing)
        if self.spotted > 0 and self.state not in ("dead", "windup") and self.show_marks:
            pop = 1 + 0.4 * max(0.0, self.spotted - SPOTTED_TIME + 0.15) / 0.15   # pops in, then settles
            ui.text_center(x, y + 68, "!", (255, 220, 90), round(22 * pop))
