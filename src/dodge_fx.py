"""The dodge's look (2026-11-21, "굳이 구르는 동작이 없어도 되지 않을까요? 살짝 샤샥하면서"):
no roll pictures. The body glides on one stride picture toward where it dodges, and one of these
looks sells the speed:

  ghost       fading copies of the body left along the way (afterimages)
  ghost_dust  afterimages + a puff of dust where it set off
  streak      speed lines behind the body + the dust

Any character with a look (DirLook / SheetLook) can use Trail; plan:
docs/plans/2026-11-21_구르기_회피.md.
"""

import random
from math import cos, pi, sin

import ground_marks as marks

STYLES = ("ghost", "ghost_dust", "streak")
STYLE_NAMES = {"ghost": "잔상", "ghost_dust": "잔상 + 먼지", "streak": "속도선 + 먼지"}
style = "ghost_dust"            # F4 "회피 연출"

GHOST_EVERY = 0.035             # s between afterimages
GHOST_LIFE = 0.16               # s an afterimage takes to fade
GHOST_ALPHA = 0.45              # the newest afterimage's opacity
GHOST_TINT = (150, 185, 235)    # afterimages are cooler than the body
STREAK_LINES = ((-7, 0.9), (0, 1.0), (7, 0.8), (14, 0.55))   # (sideways offset, length share) of the speed lines
STREAK_LEN = 34                 # world units of the longest speed line
STREAK_COLOUR = (215, 222, 230)
DUST_COLOUR = (178, 164, 136)


class Trail:
    """Afterimages / speed lines of one character's dodge."""

    def __init__(self):
        self.ghosts = []                # [x, y, angle, age]
        self.clock = GHOST_EVERY
        self.speed = 0.0                # 0..1: how strongly the speed lines show (fades after the dodge)
        self.angle = 0.0

    def update(self, dt, x, y, angle, active):
        for g in self.ghosts:
            g[3] += dt
        self.ghosts = [g for g in self.ghosts if g[3] < GHOST_LIFE]
        if active:
            self.angle = angle
            self.speed = 1.0
            self.clock += dt
            if self.clock >= GHOST_EVERY:
                self.clock = 0.0
                self.ghosts.append([x, y, angle, 0.0])
        else:
            self.clock = GHOST_EVERY            # the next dodge leaves one at once
            self.speed = max(0.0, self.speed - dt / GHOST_LIFE)

    def draw(self, look, pose, time, x, y, cam_x, cam_y, facing):
        """Under the body: afterimages or speed lines. (x, y) is where the body is now (world)."""
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
        for gx, gy, ang, age in self.ghosts:
            look.draw(pose, time, gx - cam_x, gy - cam_y, facing, alpha=GHOST_ALPHA * (1 - age / GHOST_LIFE),
                      tint=GHOST_TINT, angle=ang)


class Dust:
    """A small puff where a dodge set off, kicked back against the way it went."""

    LIFE = 0.3

    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.age = 0.0
        back = angle + pi
        self.bits = [(back + random.uniform(-0.9, 0.9), random.uniform(10, 22), random.uniform(0, 5))
                     for _ in range(12)]

    @staticmethod
    def wanted():
        return style in ("ghost_dust", "streak")

    def update(self, dt):
        self.age += dt
        return self.age < self.LIFE

    def draw(self, cam_x, cam_y):
        p = self.age / self.LIFE
        for k, (a, reach, rise) in enumerate(self.bits):
            if k / len(self.bits) < p:                  # bits drop out as it settles
                continue
            r = reach * (0.3 + 0.7 * p)
            px, py = self.x - cam_x + cos(a) * r, self.y - cam_y + sin(a) * r * 0.5 + rise * p
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):     # 2 x 2 canvas pixels: readable at this zoom
                marks.dot(px + ox * marks.PIXEL, py + oy * marks.PIXEL, DUST_COLOUR)
