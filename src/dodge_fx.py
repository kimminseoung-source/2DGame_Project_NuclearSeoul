"""The dodge's look (2026-11-21, "굳이 구르는 동작이 없어도 되지 않을까요? 살짝 샤샥하면서"):
no roll pictures. The body glides on one stride picture toward where it dodges, and one of these
looks sells the speed:

  ghost       fading copies of the body left along the way (afterimages)
  ghost_dust  afterimages + a puff of dust where it set off
  streak      speed lines behind the body + the dust
  roll        a real roll (Mixamo Stand To Roll, Roll/ pictures; only east for now, 2026-11-21
              "구르기 동작 한쪽 방향으로만 해서 비교") + the dust; other directions glide

Any character with a look (DirLook / SheetLook) can use Trail; plan:
docs/plans/2026-11-21_구르기_회피.md.
"""

import random
from math import cos, pi, sin

import ground_marks as marks

STYLES = ("ghost", "ghost_dust", "streak", "roll")
STYLE_NAMES = {"ghost": "잔상", "ghost_dust": "잔상 + 먼지", "streak": "속도선 + 먼지", "roll": "구르기 그림 (동쪽만) + 먼지"}
style = "ghost_dust"            # F4 "회피 연출"

GHOST_EVERY = 0.035             # s between afterimages
GHOST_LIFE = 0.16               # s an afterimage takes to fade
GHOST_ALPHA = 0.45              # the newest afterimage's opacity
GHOST_TINT = (150, 185, 235)    # afterimages are cooler than the body
STREAK_LINES = ((-7, 0.9), (0, 1.0), (7, 0.8), (14, 0.55))   # (sideways offset, length share) of the speed lines
STREAK_LEN = 34                 # world units of the longest speed line
STREAK_COLOUR = (215, 222, 230)
DUST_COLOUR = (178, 164, 136)


ROLL_EDGES = (0.15, 0.35, 0.8)  # the roll's crouch | dive | tucked | rising, when the look gives no timing
PUFF_EVERY = 0.045              # s between dust puffs while it rolls along the ground


def roll_edges(look):
    """Where the roll's dive, tucked and rising pictures start (0..1), from the look's timing holds."""
    shares = getattr(look, "keys", {}).get("timing", {}).get("roll")
    if not shares or len(shares) != 4:
        return ROLL_EDGES
    total, edges, acc = sum(shares), [], 0.0
    for s in shares[:3]:
        acc += s / total
        edges.append(acc)
    return tuple(edges)


class Trail:
    """Afterimages / speed lines / rolling dust of one character's dodge."""

    def __init__(self):
        self.ghosts = []                # [x, y, angle, age, progress]
        self.clock = GHOST_EVERY
        self.speed = 0.0                # 0..1: how strongly the speed lines show (fades after the dodge)
        self.angle = 0.0
        self.puffs = []                 # Dust under a rolling body
        self.puff_clock = 0.0
        self.landed = False

    def update(self, dt, x, y, angle, active, progress=0.0, look=None):
        for g in self.ghosts:
            g[3] += dt
        self.ghosts = [g for g in self.ghosts if g[3] < GHOST_LIFE]
        self.puffs = [d for d in self.puffs if d.update(dt)]
        if not active:
            self.clock = GHOST_EVERY            # the next dodge leaves one at once
            self.speed = max(0.0, self.speed - dt / GHOST_LIFE)
            self.landed = False
            return
        self.angle = angle
        self.speed = 1.0
        if style == "roll" and rolls(look, angle):
            self.roll_effects(dt, x, y, angle, progress, look)
            return
        self.clock += dt
        if self.clock >= GHOST_EVERY:
            self.clock = 0.0
            self.ghosts.append([x, y, angle, 0.0, progress])

    def roll_effects(self, dt, x, y, angle, progress, look):
        """2026-11-21 구르기 다듬기: a faint afterimage while it dives, dust along the ground while it is
        tucked, and a puff to both sides as it comes up."""
        dive, tuck, rise = roll_edges(look)
        self.clock += dt
        if dive <= progress < tuck and self.clock >= GHOST_EVERY:
            self.clock = 0.0
            self.ghosts.append([x, y, angle, 0.0, progress])
        self.puff_clock += dt
        if tuck <= progress < rise and self.puff_clock >= PUFF_EVERY:
            self.puff_clock = 0.0
            self.puffs.append(Dust(x, y, angle, kind="puff"))
        if progress >= rise and not self.landed:
            self.landed = True
            self.puffs.append(Dust(x, y, angle, kind="land"))

    def draw(self, look, pose, time, x, y, cam_x, cam_y, facing):
        """Under the body: afterimages or speed lines. (x, y) is where the body is now (world)."""
        for d in self.puffs:
            d.draw(cam_x, cam_y)
        if style == "streak":
            if self.speed <= 0:
                return
            ux, uy = cos(self.angle), sin(self.angle)
            for side, share in STREAK_LINES:
                ox = x - cam_x - uy * side - ux * 6
                oy = y - cam_y + ux * side + 16
                length = STREAK_LEN * share * self.speed
                marks.line(ox, oy, ox - ux * length, oy - uy * length, STREAK_COLOUR, gap=2)
            return
        for gx, gy, ang, age, prog in self.ghosts:
            rolled = style == "roll" and rolls(look, ang)
            look.draw("roll" if rolled else pose, prog if rolled else time, gx - cam_x, gy - cam_y, facing,
                      alpha=GHOST_ALPHA * (1 - age / GHOST_LIFE) * (0.7 if rolled else 1.0), tint=GHOST_TINT,
                      angle=ang)


def rolls(look, angle):
    """Draw the dodge as a roll: that style is on and the look has roll pictures this way."""
    return style == "roll" and bool(getattr(look, "has_dir", lambda p, a: False)("roll", angle))


class Dust:
    """Dust kicked up by a dodge. kind: "kick" (setting off, thrown back against the way it went),
    "puff" (small, under a rolling body), "land" (coming up out of a roll, to both sides)."""

    KINDS = {   # spread around the direction (radians), reach range, bits, life (s)
        "kick": (0.9, (10, 22), 12, 0.3),
        "puff": (1.4, (3, 9), 4, 0.22),
        "land": (0.5, (8, 18), 10, 0.3),
    }

    def __init__(self, x, y, angle, kind="kick"):
        spread, (near, far), count, self.life = self.KINDS[kind]
        self.x, self.y = x, y
        self.age = 0.0
        if kind == "land":
            aims = [angle + pi / 2, angle - pi / 2]
        else:
            aims = [angle + pi]
        self.bits = [(random.choice(aims) + random.uniform(-spread, spread), random.uniform(near, far),
                      random.uniform(0, 5)) for _ in range(count)]

    @staticmethod
    def wanted():
        return style in ("ghost_dust", "streak", "roll")

    def update(self, dt):
        self.age += dt
        return self.age < self.life

    def draw(self, cam_x, cam_y):
        p = self.age / self.life
        for k, (a, reach, rise) in enumerate(self.bits):
            if k / len(self.bits) < p:                  # bits drop out as it settles
                continue
            r = reach * (0.3 + 0.7 * p)
            px, py = self.x - cam_x + cos(a) * r, self.y - cam_y + sin(a) * r * 0.5 + rise * p
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):     # 2 x 2 canvas pixels: readable at this zoom
                marks.dot(px + ox * marks.PIXEL, py + oy * marks.PIXEL, DUST_COLOUR)
