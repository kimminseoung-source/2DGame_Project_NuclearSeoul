"""The flurry (연속 베기) the time-warp charge lets loose: a storm of cuts in front of the hero.

On release the hero chops once; at the blow a burst of slash lines is drawn across the
area in front (one after another, very fast), the scene holds for a beat, then the lines
pop one by one and every enemy inside the area takes each of them; the last line hits
hardest. The play loop asks pop() for the lines that pop this frame and lands them, so
any enemy and any weapon use the same storm (generic systems rule).
"""

import random
from math import cos, sin

import pico2d

import camera

# Charge level -> (cuts, reach in px in front, half depth in px, px behind the hero).
LEVELS = {
    1: (4, 64, 20, 0),
    2: (7, 96, 26, 0),
    3: (12, 128, 34, 32),
}
CUT_DAMAGE = 1            # each line
LAST_DAMAGE = 3           # the last line
DRAW_EVERY = 0.025        # real seconds between lines appearing
HOLD = 0.14               # real seconds the finished storm hangs before popping
POP_EVERY = 0.045         # real seconds between pops


class Flurry:
    def __init__(self, x, y, direction, level, power, targets=()):
        self.x, self.y, self.direction = x, y, direction
        self.level = level
        self.power = power
        cuts, self.reach, self.depth, self.behind = LEVELS[level]
        rng = random.Random(int(x * 7 + y * 13 + level))
        self.lines = []
        # Most cuts go through the enemies caught in the area, the rest fill the space around.
        inside = [t for t in targets if self.contains(t)]
        for index in range(cuts):
            if inside and (index == cuts - 1 or rng.random() < 0.7):   # the last cut always lands
                target = inside[index % len(inside)]
                cx = target.x + rng.uniform(-12, 12)
                cy = target.y + rng.uniform(4, 34)
            else:
                cx = x + direction * rng.uniform(-self.behind + 10, self.reach - 8)
                cy = y + rng.uniform(-self.depth, self.depth) * 0.6 + 18
            angle = rng.choice((0.5, -0.5, 0.9, -0.9, 0.15, -0.15)) + rng.uniform(-0.15, 0.15)
            length = rng.uniform(34, 58) * (1.4 if index == cuts - 1 else 1)
            self.lines.append((cx, cy, angle, length))
        self.clock = 0.0
        self.popped = 0           # lines already popped
        self.done = False

    def update(self):
        pass                      # the play loop drives pop() so it can land each cut

    def contains(self, target):
        dx = (target.x - self.x) * self.direction
        return -self.behind - 6 <= dx <= self.reach + 6 and abs(target.y - self.y) <= self.depth + 6

    def damage(self, index):
        last = index == len(self.lines) - 1
        return max(1, round((LAST_DAMAGE if last else CUT_DAMAGE) * self.power))

    @property
    def shown(self):
        return min(len(self.lines), int(self.clock / DRAW_EVERY) + 1)

    def pop(self, frame_time):
        """Advance by real frame_time; returns indices of the lines that pop now."""
        self.clock += frame_time
        start = len(self.lines) * DRAW_EVERY + HOLD
        due = 0 if self.clock < start else min(len(self.lines), int((self.clock - start) / POP_EVERY) + 1)
        popped = list(range(self.popped, due))
        self.popped = due
        if self.popped == len(self.lines):
            self.done = True
        return popped

    def line_center(self, index):
        cx, cy, _, _ = self.lines[index]
        return cx, cy

    def draw(self):
        drawing = self.clock < len(self.lines) * DRAW_EVERY
        for index in range(self.popped, self.shown):
            cx, cy, angle, length = self.lines[index]
            newest = drawing and index == self.shown - 1
            grow = min(1.0, (self.clock - index * DRAW_EVERY) / DRAW_EVERY) if newest else 1.0
            half = length * grow / 2
            dx, dy = cos(angle) * half * self.direction, sin(angle) * half
            x, y = cx - camera.x, cy
            # A thin bright cut with a green glow that tapers off towards both ends.
            for share, offset, (r, g, b, a) in ((0.7, -1, (110, 255, 160, 150)), (0.7, 1, (110, 255, 160, 150)),
                                                (1.0, 0, (255, 255, 255, 255))):
                pico2d.draw_line(x - dx * share, y - dy * share + offset, x + dx * share,
                                 y + dy * share + offset, r, g, b, a)
