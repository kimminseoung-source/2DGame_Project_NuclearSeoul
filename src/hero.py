"""The hero: WASD movement (Ctrl sneaks), the aimed slash with a short lunge, the roll, being
grabbed, being slowed by blows (Zomboid: each hit slows you, up to half speed), stamina
(stamina.py: every swing, shove and roll costs breath) and the quiet takedown of an unaware
infected (its own motion: take hold, a short stab)."""

from math import atan2, cos, hypot, sin

import sdl2

import stamina as breath
from area import HERO_START, move_body
from settings import (CHEST, CHOP_HIT, CHOP_LUNGE, CHOP_TIME, HERO_HP, HURT_REACT, ROLL_COOLDOWN,
                      ROLL_SPEED, ROLL_TIME, RUN_SPEED, SLASH_COOLDOWN, SLASH_HIT, SLASH_LUNGE, SLASH_TIME,
                      TEMPO)


PICKUP_TIME = 0.35 * TEMPO  # s of the pick-up motion (2026-11-15 "간단하게")
SNEAK_SPEED = 0.45          # Ctrl held: share of the normal speed
HIT_SLOW = 0.25             # each blow taken slows the hero this much more...
MAX_SLOW = 0.5              # ...up to half speed (Zomboid's attack slow cap)
SLOW_RECOVER = 0.2          # per second back to full speed
SHOVE_TIME = 0.25 * TEMPO   # s of the shove (right click)
SHOVE_COOLDOWN = 0.6
LUNGE_SPEED = 60 * (1 - 0.82)   # the lunge fades by 0.82 a frame: start speed = distance x this
# The takedown (2026-11-16 "기습을 성공하는 건 애니메이션을 따로, 조용히 죽이는 걸로"): the hero takes
# hold of an infected that has not seen him and stabs it, feet planted, no sound to speak of.
TAKEDOWN_TIME = 0.8 * TEMPO
TAKEDOWN_STAB = 0.55        # share of the takedown when the blade goes in
TAKEDOWN_REACH = 40         # px: close enough to take hold


class Hero:
    def __init__(self, look):
        self.look = look
        self.x, self.y = HERO_START
        self.facing = 1
        self.hp = HERO_HP
        self.hurt = 0.0              # s left of being safe from another blow (not shown)
        self.reeling = 0.0           # s left of reeling from a blow (hurt sheet, no control)
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
        self.shove = 0.0             # s left of a shove
        self.shove_angle = 0.0
        self.shove_cooldown = 0.0
        self.shove_weak = False      # a tired shove cannot knock anything down
        self.stamina = breath.Stamina()
        self.takedown = 0.0          # s left of the quiet takedown
        self.victim = None           # the infected being taken down

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
        self.reeling = HURT_REACT
        self.slash = None                       # a blow breaks off the hero's own swing
        self.shove = 0.0

    def start_slash(self, ax, ay, chop=False):
        """A slash toward (ax, ay); `chop` makes it the overhead chop at something on the ground."""
        if not self.free:
            return
        angle = atan2(ay - (self.y + CHEST), ax - self.x)
        self.facing = 1 if cos(angle) >= 0 else -1
        whole, hit, lunge = (CHOP_TIME, CHOP_HIT, CHOP_LUNGE) if chop else (SLASH_TIME, SLASH_HIT, SLASH_LUNGE)
        if not self.stamina.spend("chop" if chop else "slash"):       # out of breath: a slow swing
            whole, hit = whole * breath.TIRED_SLOW, hit * breath.TIRED_SLOW
        self.slash = {"time": 0.0, "angle": angle, "hit": False, "chop": chop,
                      "whole": whole, "hit_at": hit, "pose": "swing3" if chop else "swing"}
        speed = lunge * LUNGE_SPEED                     # covers about `lunge` px whatever the tempo
        self.lunge = (cos(angle) * speed, sin(angle) * speed)

    @property
    def free(self):
        """Not busy with another action: a new slash, shove or takedown may start."""
        return not (self.slash or self.roll > 0 or self.slash_cooldown > 0 or self.dead or self.grabbed > 0
                    or self.reeling > 0 or self.shove > 0 or self.pickup > 0 or self.takedown > 0)

    def start_takedown(self, victim):
        """Take hold of an unaware infected from close by and stab it (no stamina, no noise)."""
        if not self.free:
            return False
        self.takedown, self.victim = TAKEDOWN_TIME, victim
        self.facing = 1 if victim.x >= self.x else -1
        return True

    def start_shove(self, ax, ay):
        """Right click: push whatever is in front away (Zomboid's shove)."""
        if not self.free or self.shove_cooldown > 0:
            return False
        self.shove_weak = not self.stamina.spend("shove")
        self.shove_angle = atan2(ay - (self.y + CHEST), ax - self.x)
        self.facing = 1 if cos(self.shove_angle) >= 0 else -1
        self.shove = SHOVE_TIME
        return True

    def start_roll(self, mx, my):
        """False when it could not roll: busy, or no breath left for it."""
        if self.roll > 0 or self.roll_cooldown > 0 or self.dead or self.takedown > 0:
            return False
        if not self.stamina.can("roll"):
            self.stamina.tired_flash = 0.6
            return False
        self.stamina.spend("roll")
        length = hypot(mx, my)
        self.roll_dir = (mx / length, my / length) if length else (float(self.facing), 0.0)
        self.roll = ROLL_TIME
        self.slash = None
        self.grabbed = 0.0           # rolling tears free
        return True

    def update(self, dt, keys, aim_x):
        self.time += dt
        self.hurt = max(0.0, self.hurt - dt)
        self.reeling = max(0.0, self.reeling - dt)
        self.slash_cooldown = max(0.0, self.slash_cooldown - dt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        self.slowed = max(0.0, self.slowed - SLOW_RECOVER * dt)
        self.shove_cooldown = max(0.0, self.shove_cooldown - dt)
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LCTRL] or keys[sdl2.SDL_SCANCODE_RCTRL])
        self.stamina.update(dt, self.moving)
        if self.dead:
            self.dead += dt
            return
        mx = keys[sdl2.SDL_SCANCODE_D] - keys[sdl2.SDL_SCANCODE_A]
        my = keys[sdl2.SDL_SCANCODE_W] - keys[sdl2.SDL_SCANCODE_S]
        self.moving = False
        if self.grabbed > 0:
            self.grabbed -= dt
            return
        if self.reeling > 0:                   # knocked back a step by the blow
            return
        if self.takedown > 0:                  # holding it, stabbing: feet planted
            self.takedown = max(0.0, self.takedown - dt)
            if self.takedown <= 0:
                self.victim = None
            return
        if self.pickup > 0:                    # crouched for a moment, picking something up
            self.pickup -= dt
            return
        if self.shove > 0:                     # both hands out, pushing
            self.shove -= dt
            if self.shove <= 0:
                self.shove_cooldown = SHOVE_COOLDOWN
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
            if self.slash["time"] >= self.slash["whole"]:
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
        elif self.takedown > 0:
            self.look.draw("takedown", 1 - self.takedown / TAKEDOWN_TIME, x, y, self.facing)
        elif self.reeling > 0:                 # reels from the blow (was: blinking)
            self.look.draw("hurt", 1 - self.reeling / HURT_REACT, x, y, self.facing)
        elif self.pickup > 0:
            self.look.draw("pickup", 1 - self.pickup / PICKUP_TIME, x, y, self.facing)
        elif self.shove > 0:                   # both hands out (2026-11-16: push sheet, UAL1 Push_Loop)
            self.look.draw("push", 1 - self.shove / SHOVE_TIME, x, y, self.facing)
        elif self.roll > 0:
            face = 1 if self.roll_dir[0] >= 0 else -1
            self.look.draw("run", (1 - self.roll / ROLL_TIME) * 0.5, x, y - 2, face,
                           distance=self.run_distance + (1 - self.roll / ROLL_TIME) * 3)
        elif self.slash:
            s = self.slash
            self.look.draw(s["pose"], s["time"] / s["whole"], x, y, self.facing, contact=s["hit_at"] / s["whole"])
        elif self.moving:
            pose = "sneak" if self.sneaking else "run"
            self.look.draw(pose, self.time, x, y, self.facing, distance=self.run_distance)
        else:
            self.look.draw("sneak_idle" if self.sneaking else "idle", self.time, x, y, self.facing)
