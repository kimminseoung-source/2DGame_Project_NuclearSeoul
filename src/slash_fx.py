"""Slash effects: the big white crescent along the aim and the burst where a blow lands."""

from math import cos, pi, sin

import pico2d

from settings import SLASH_ARC


class Crescent:
    """The big white slash crescent along the aim."""

    LIFE = 0.16

    def __init__(self, x, y, angle):
        self.x, self.y, self.angle = x, y, angle
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        return self.age < self.LIFE

    def draw(self, cam_x, cam_y):
        fade = 1 - self.age / self.LIFE
        cx, cy = self.x - cam_x, self.y - cam_y
        for ring, (radius, alpha) in enumerate(((52, 255), (48, 230), (44, 190), (40, 130), (36, 70))):
            pts = []
            for k in range(13):
                t = -SLASH_ARC + 2 * SLASH_ARC * k / 12
                width = sin(pi * k / 12)                       # thick in the middle, thin at the tips
                r = radius + 6 * width * (1 if ring == 0 else 0.6)
                pts.append((cx + cos(self.angle + t) * r, cy + sin(self.angle + t) * r))
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                pico2d.draw_line(x1, y1, x2, y2, 255, 255, 255, round(alpha * fade))


class Spark:
    """A short burst where a blow lands."""

    def __init__(self, x, y, big=False):
        self.x, self.y = x, y
        self.age = 0.0
        self.big = big

    def update(self, dt):
        self.age += dt
        return self.age < 0.18

    def draw(self, cam_x, cam_y):
        p = self.age / 0.18
        scale = 1.6 if self.big else 1.0
        for dx, dy in ((-25, 8), (-15, 21), (4, 25), (22, 15), (26, -4), (12, -13), (-10, -14)):
            a, b = (0.2 + p * 0.7) * scale, (0.2 + p * 0.7 + (1 - p) * 0.5) * scale
            pico2d.draw_line(self.x - cam_x + dx * a, self.y - cam_y + dy * a, self.x - cam_x + dx * b,
                             self.y - cam_y + dy * b, 255, 120, 110)
        if p < 0.35:
            pico2d.draw_circle(self.x - cam_x, self.y - cam_y, round(5 * scale), 255, 230, 220, filled=True)
