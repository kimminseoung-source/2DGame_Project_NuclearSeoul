"""The hero: WASD movement (Ctrl sneaks), the aimed slash with a short lunge, the roll, being
grabbed, being slowed by blows (Zomboid: each hit slows you, up to half speed), stamina
(stamina.py: every swing, shove and roll costs breath) and the stomp on a crawling infected."""

from math import atan2, cos, hypot, sin

import sdl2

import dodge_fx
import stamina as breath
from settings import DOT_LOOK, STAMINA_ON
import weapons
from area import HERO_START, move_body
from settings import (CHEST, HERO_HP, HURT_REACT, ROLL_COOLDOWN, ROLL_SPEED, ROLL_TIME, RUN_SPEED,
                      SLASH_COOLDOWN, STOMP_HIT, STOMP_LUNGE, STOMP_TIME,
                      TEMPO)


PICKUP_TIME = 0.35 * TEMPO  # s of the pick-up motion (2026-11-15 "간단하게")
SNEAK_SPEED = 0.45          # Ctrl held: share of the normal speed
HIT_SLOW = 0.25             # each blow taken slows the hero this much more...
MAX_SLOW = 0.5              # ...up to half speed (Zomboid's attack slow cap)
SLOW_RECOVER = 0.2          # per second back to full speed
SHOVE_TIME = 0.25 * TEMPO   # s of the shove (right click)
SHOVE_COOLDOWN = 0.6
LUNGE_SPEED = 60 * (1 - 0.82)   # the lunge fades by 0.82 a frame: start speed = distance x this
# Cancelling the follow-through (2026-11-19 "공격 동작 때 잠깐 멈추는 틈이 더 짧으면, 각 동작마다 더
# 부드러운 조작"): once the blow has landed, walking, rolling or the next blow end it early.
CANCEL_MOVE = 0.06          # s after the hit that walking or a roll ends the blow
# The roll's speed from start to end, as shares of ROLL_SPEED (2026-11-21 "출발은 확 튀고 끝은 미끄러지듯"):
# it falls evenly from the first to the second; their mean is 1, so the roll still covers the same ground.
# (1.0, 1.0) is the old even roll. F4 "구르기 속도".
ROLL_EASE = (1.6, 0.4)
CANCEL_BLOW = 0.5           # share of the follow-through after which the next blow may start
CANCEL_REST = 0.5           # share of the weapon's rest (cooldown) kept after walking out of a blow



def roll_share(p0, p1):
    """Share of the whole roll's ground covered between progress p0 and p1 (0..1), with the speed
    falling evenly from ROLL_EASE[0] to ROLL_EASE[1] times ROLL_SPEED."""
    a, b = ROLL_EASE
    return a * (p1 - p0) + (b - a) * (p1 * p1 - p0 * p0) / 2

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
        self.roll_buffer = None      # Space pressed while rolling: the next roll's direction (2026-11-21)
        self.rolled_now = False      # a roll began this frame (the game puts its dust and sound)
        self.trail = dodge_fx.Trail()   # the dodge's afterimages / speed lines (2026-11-21)
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
        self.rolls = breath.Charges()       # rolls stored (2026-11-21, stamina off)
        self.weapon = weapons.WEAPONS[weapons.DEFAULT]
        self.ready = None            # s the blow has been held ready (left button held), or None

    @property
    def invulnerable(self):
        return self.roll > 0 or self.hurt > 0

    def take_blow(self):
        self.slowed = min(MAX_SLOW, self.slowed + HIT_SLOW)
        self.reeling = HURT_REACT
        self.slash = None                       # a blow breaks off the hero's own swing
        self.shove = 0.0

    def held(self):
        """The weapon drawn in the hand (the dot look's sheets are empty-handed), or None."""
        return weapons.image(self.weapon["sprite"]) if DOT_LOOK else None

    @property
    def charge(self):
        """0..1: how full the charge is while the button is held."""
        return 0.0 if self.ready is None else min(1.0, self.ready / weapons.CHARGE_TIME)

    def start_ready(self):
        """Left button pressed: raise the weapon and hold it (slow walk, a little stamina)."""
        if self.free:
            self.ready = 0.0

    def start_slash(self, ax, ay, stomp=False, aim=None):
        """A blow of the weapon toward (ax, ay) (weapons.py); `stomp` makes it a stamp of the foot
        on a crawler instead. `aim` = (infected, part) it is aimed at, if any. A blow let go from
        the ready stance skips most of its wind-up (READY_SKIP), a plain click some (QUICK_SKIP)."""
        held = self.charge >= 1.0                     # a full charge: the aimed part counts
        self.ready = None
        if self.can_cancel(CANCEL_BLOW):              # chain: the next blow cuts the follow-through
            self.end_slash(rest=0.0)
        if not self.free:
            return
        angle = atan2(ay - (self.y + CHEST), ax - self.x)
        self.facing = 1 if cos(angle) >= 0 else -1
        w = self.weapon
        if stomp:
            whole, hit, lunge, cost = STOMP_TIME, STOMP_HIT, STOMP_LUNGE, breath.COST["stomp"]
        else:
            whole, hit, lunge, cost = w["time"], w["hit"], w["lunge"], w["stamina"]
        if not self.stamina.pay(cost):                                 # out of breath: a slow one
            whole, hit = whole * breath.TIRED_SLOW, hit * breath.TIRED_SLOW
        if stomp:
            start = 0.0
        else:                                         # raised already: most of the wind-up is done;
            start = hit * (weapons.READY_SKIP if held else weapons.QUICK_SKIP)   # a click: some of it
        self.slash = {"time": start, "angle": angle, "hit": False, "stomp": stomp, "aim": aim,
                      "whole": whole, "hit_at": hit, "pose": "stomp" if stomp else w["pose"],
                      "reach": w["reach"], "arc": w["arc"], "weapon": w, "held": held,
                      "from": (self.x, self.y + CHEST)}            # the range is measured from here
        speed = lunge * LUNGE_SPEED                     # covers about `lunge` px whatever the tempo
        self.lunge = (cos(angle) * speed, sin(angle) * speed)

    def can_cancel(self, share=0.0):
        """The blow has landed and its follow-through may be cut short (after CANCEL_MOVE s, or
        `share` of the follow-through if that is later)."""
        s = self.slash
        if not s or not s["hit"]:
            return False
        return s["time"] >= s["hit_at"] + max(CANCEL_MOVE, share * (s["whole"] - s["hit_at"]))

    def end_slash(self, rest=CANCEL_REST):
        """Cut the blow short; `rest` of the weapon's cooldown still follows."""
        if self.slash:
            self.slash_cooldown = self.slash["weapon"].get("cooldown", SLASH_COOLDOWN) * rest
            self.slash = None
            self.lunge = (0.0, 0.0)

    @property
    def free(self):
        """Not busy with another action: a new slash or shove may start."""
        return not (self.slash or self.roll > 0 or self.slash_cooldown > 0 or self.dead or self.grabbed > 0
                    or self.reeling > 0 or self.shove > 0 or self.pickup > 0)

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
        """False when it could not roll: busy, or no roll left (breath, when stamina is on)."""
        if self.dead:
            return False
        if self.roll > 0 or self.roll_cooldown > 0:   # still rolling: it goes on as soon as this one ends
            self.roll_buffer = (mx, my)
            return False
        if STAMINA_ON:
            if not self.stamina.can("roll"):
                self.stamina.tired_flash = 0.6
                return False
            self.stamina.spend("roll")
        elif not self.rolls.use():               # none stored: the dots flash red
            return False
        length = hypot(mx, my)
        self.roll_dir = (mx / length, my / length) if length else (float(self.facing), 0.0)
        self.roll = ROLL_TIME
        self.slash = None
        self.grabbed = 0.0           # rolling tears free
        self.roll_buffer = None
        self.rolled_now = True
        return True

    # Experiment (2026-11-18 "근접 전투가 답답하다"): the hero's own actions - swing, its rest,
    # shove, pick-up, raising the weapon - run this many times faster. 1.3 undoes settings.TEMPO
    # for the hero only; walking and the infected stay as they are. Set by the F4 panel.
    action_speed = 1.0
    walk_while_shooting = False      # opt-in gun animation trial; normal/melee behaviour unchanged
    distance_step_audio = True       # default distance clock; refined trial supplies contact events
    hand = None                     # screen point of the weapon hand last drawn (8-direction art)
    angle = None                    # where the hero looks (world radians), set by play for 8-direction art

    def update(self, dt, keys, aim_x):
        adt = dt * self.action_speed               # the hero's action clock
        self.time += dt
        self.hurt = max(0.0, self.hurt - dt)
        self.reeling = max(0.0, self.reeling - dt)
        self.slash_cooldown = max(0.0, self.slash_cooldown - adt)
        self.roll_cooldown = max(0.0, self.roll_cooldown - dt)
        self.trail.update(dt, self.x, self.y, self.roll_angle(), self.roll > 0,   # fades even when busy
                          1 - self.roll / ROLL_TIME, self.look)
        self.slowed = max(0.0, self.slowed - SLOW_RECOVER * dt)
        self.shove_cooldown = max(0.0, self.shove_cooldown - adt)
        self.sneaking = bool(keys[sdl2.SDL_SCANCODE_LCTRL] or keys[sdl2.SDL_SCANCODE_RCTRL])
        if self.ready is not None:
            if not self.free:                          # hit, grabbed, rolling: the stance is lost
                self.ready = None
            else:
                self.ready += adt
                if STAMINA_ON:
                    self.stamina.value = max(0.0, self.stamina.value - weapons.READY_DRAIN * dt)
                    self.stamina.rest_in = breath.DELAY
        self.stamina.update(dt, self.moving)
        self.rolls.update(dt)
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
        if self.pickup > 0:                    # crouched for a moment, picking something up
            self.pickup -= adt
            return
        if self.shove > 0:                     # both hands out, pushing
            self.shove -= adt
            if self.shove <= 0:
                self.shove_cooldown = SHOVE_COOLDOWN
            return
        if self.roll > 0:
            before = 1 - self.roll / ROLL_TIME
            self.roll -= dt
            after = min(1.0, 1 - max(0.0, self.roll) / ROLL_TIME)
            go = ROLL_SPEED * ROLL_TIME * roll_share(before, after)
            move_body(self, self.roll_dir[0] * go, self.roll_dir[1] * go)
            if self.roll <= 0:
                self.roll_cooldown = ROLL_COOLDOWN
        if self.roll <= 0 and self.roll_cooldown <= 0 and self.roll_buffer is not None:
            pressed, self.roll_buffer = self.roll_buffer, None
            self.start_roll(*pressed)           # the roll pressed during the last one (none left: red dots, no late roll)
        elif self.slash and not ((mx or my) and self.can_cancel()):
            self.slash["time"] += adt
            if self.walk_while_shooting and self.slash["weapon"].get("shot") and (mx or my):
                self._walk_step(dt, mx, my, raised=True)
            else:
                move_body(self, self.lunge[0] * dt, self.lunge[1] * dt)
            self.lunge = (self.lunge[0] * 0.82, self.lunge[1] * 0.82)
            if self.slash["time"] >= self.slash["whole"]:
                self.slash_cooldown = self.slash["weapon"].get("cooldown", SLASH_COOLDOWN)   # the weapon's rest
                self.slash = None
        elif mx or my:
            self.end_slash()                           # walking out of a landed blow (no-op otherwise)
            self._walk_step(dt, mx, my, raised=self.ready is not None)
        elif aim_x is not None:
            self.facing = 1 if aim_x >= self.x else -1

    def _walk_step(self, dt, mx, my, raised=False):
        length = hypot(mx, my)
        speed = RUN_SPEED * (SNEAK_SPEED if self.sneaking else 1.0) * (1 - self.slowed)
        if raised:
            speed *= weapons.READY_SPEED
        move_body(self, mx / length * speed * dt, my / length * speed * dt)
        self.run_distance += speed * dt / 32
        self.moving = True
        if mx:
            self.facing = mx

    DODGE_STRIDE = 2               # which walking picture the body glides on while dodging (legs apart)

    def roll_angle(self):
        return atan2(self.roll_dir[1], self.roll_dir[0])

    def _draw(self, *args, **kw):
        """Draws with the look and keeps where the weapon hand is (F1; None for side sheets)."""
        self.hand = self.look.draw(*args, **kw)

    def draw(self, cx, cy):
        x, y = self.x - cx, self.y - cy
        stride = getattr(self.look, "FRAME_TIME", 0.1) * self.DODGE_STRIDE
        face = 1 if self.roll_dir[0] >= 0 else -1
        self.trail.draw(self.look, "run", stride, self.x, self.y, cx, cy, face)   # under the body
        if self.dead:
            self._draw("down", min(1.0, self.dead * 1.5), x, y, self.facing, angle=self.angle)
        elif self.reeling > 0:                 # reels from the blow (was: blinking)
            self._draw("hurt", 1 - self.reeling / HURT_REACT, x, y, self.facing, held=self.held(), angle=self.angle)
        elif self.pickup > 0:
            self._draw("pickup", 1 - self.pickup / PICKUP_TIME, x, y, self.facing, held=self.held(), angle=self.angle)
        elif self.shove > 0:                   # both hands out (2026-11-16: push sheet, UAL1 Push_Loop)
            self._draw("push", 1 - self.shove / SHOVE_TIME, x, y, self.facing, held=self.held(), angle=self.angle)
        elif self.roll > 0 and dodge_fx.rolls(self.look, self.roll_angle()):   # F4: the real roll to compare
            self._draw(dodge_fx.roll_pose(), 1 - self.roll / ROLL_TIME, x, y, face, held=self.held(),
                       angle=self.roll_angle())
        elif self.roll > 0:                    # the dodge: no roll pictures, it glides on one stride (2026-11-21)
            self._draw("run", stride, x, y, face, distance=self.run_distance, held=self.held(),
                       angle=self.roll_angle())
        elif self.slash:
            s = self.slash
            self._draw(s["pose"], s["time"] / s["whole"], x, y, self.facing, contact=s["hit_at"] / s["whole"],
                           held=self.held(), angle=s["angle"])
        elif self.ready is not None and self.ready >= weapons.QUICK_PRESS:   # holding the blow raised
            w = self.weapon
            walking = f"ready_{w['style']}"
            if self.moving and self.look.has(walking):     # stepping with it raised: the legs walk
                self._draw(walking, self.time, x, y, self.facing, distance=self.run_distance, held=self.held(),
                           angle=self.angle)
            elif self.look.has(f"ready_stand_{w['style']}"):    # an aiming picture for this kind of weapon
                self._draw(f"ready_stand_{w['style']}", self.time, x, y, self.facing, held=self.held(),
                           angle=self.angle)
            else:
                self._draw(w["pose"], w["hit"] * 0.95 / w["time"], x, y, self.facing, contact=w["hit"] / w["time"],
                               held=self.held(), angle=self.angle)
        elif self.moving:
            pose = "sneak" if self.sneaking else "run"
            self._draw(pose, self.time, x, y, self.facing, distance=self.run_distance, held=self.held(),
                           angle=self.angle)
        else:
            self._draw("sneak_idle" if self.sneaking else "idle", self.time, x, y, self.facing, held=self.held(),
                           angle=self.angle)
