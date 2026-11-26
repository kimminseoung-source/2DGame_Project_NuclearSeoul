"""Slash effects: the big white crescent along the aim and the burst where a blow lands, and
the realistic set (F3, 2026-11-15 "리얼리티 느낌"): a faint quick blade streak, blood spraying from
a wound and the stains it leaves on the ground."""

import random
from math import cos, pi, sin

import pico2d

from settings import DOT, ROOT, SLASH_ARC

# Drawn effect pictures (2026-11-19 "임팩트 효과로 좀 가려야"): the blow's trail and the burst where
# it lands, so two key-pose pictures read as one swing (docs/planning/MOTION_FEW_SPRITES_2026-11-19.md).
# Credits: assets/effects/CREDITS.md. Each: sheet, frame w, h, frames, frames per second, scale.
FX = {
    "slash": ("pixel_art_sword_slash_sprites.png", 64, 47, 7, 40, 0.75),     # tbbk, CC0 (from its 3rd frame)
    "hit": ("oga_hit_animations_3/shards02.png", 64, 64, 10, 40, 0.6),       # Viktor Hahn, CC-BY 4.0
    "hit_big": ("oga_hit_animations_3/splash04.png", 64, 64, 10, 36, 0.75),  # Viktor Hahn, CC-BY 4.0
}
FX_FIRST = {"hit": 5, "slash": 2}   # shards02: its second row (a sharp cross); slash: skip the two tiny first frames
_sheets = {}


class SpriteFx:
    """One play of a drawn effect sheet (FX) at a point, turned to `angle` (radians, y up).
    The slash sheet's crescent bulges toward +x as drawn, so `angle` turns it to bulge along the
    blow (checked in the game: turned by angle - pi it bulged back at the hero)."""

    on = True                        # F4 "타격 효과 그림"

    def __init__(self, name, x, y, angle=0.0):
        sheet, self.fw, self.fh, self.count, self.fps, self.scale = FX[name]
        if sheet not in _sheets:
            _sheets[sheet] = pico2d.load_image(str(ROOT / "assets" / "effects" / sheet))
        self.image = _sheets[sheet]
        self.first = FX_FIRST.get(name, 0)
        self.x, self.y = x, y
        self.angle = angle
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        return self.age < self.count / self.fps

    def draw(self, cam_x, cam_y):
        n = self.first + min(self.count - 1, int(self.age * self.fps))
        cols = self.image.w // self.fw
        col, row = n % cols, n // cols
        w, h = self.fw * self.scale / DOT, self.fh * self.scale / DOT     # its pixels are canvas pixels
        self.image.clip_composite_draw(col * self.fw, self.image.h - (row + 1) * self.fh, self.fw, self.fh,
                                       self.angle, "", self.x - cam_x, self.y - cam_y, w, h)


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


class Streak:
    """Realistic slash: a quick bright arc where the blade passed - on the same arc the game shows
    as the weapon's reach (2026-11-16: the trail and the shown range were two different arcs)."""

    LIFE = 0.16

    def __init__(self, x, y, angle, radius=44, arc=SLASH_ARC):
        self.x, self.y, self.angle = x, y, angle
        self.radius, self.arc = radius, arc
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        return self.age < self.LIFE

    def draw(self, cam_x, cam_y):
        fade = 1 - self.age / self.LIFE
        cx, cy = self.x - cam_x, self.y - cam_y
        n = max(2, int(self.radius * self.arc / 6))       # the same dots as the shown arc (play.draw_aim)
        for k in range(-n, n + 1):
            t = self.angle + k * self.arc / n
            x, y = cx + cos(t) * self.radius, cy + sin(t) * self.radius
            pico2d.draw_rectangle(x - 1, y - 1, x + 1, y + 1, 236, 238, 240, round(255 * fade), filled=True)


# Blood colours (ART_BIBLE "피 색"): people bleed red, the infected a murky dark green
# (cold blue-grey world + green = danger).  (falling drop, stain on the ground)
BLOOD_RED = ((110, 12, 14), (70, 10, 12))
BLOOD_INFECTED = ((52, 68, 34), (32, 44, 24))


class Blood:
    """Dark drops thrown from a wound along the blow; where they land they leave stains
    (handed back by `landed()` so the play loop can keep them on the ground).
    `infected=True` gives the infected's murky green; people stay red."""

    def __init__(self, x, y, angle, amount=14, infected=False):
        self.colors = BLOOD_INFECTED if infected else BLOOD_RED
        rng = random.Random()
        self.drops = []
        for _ in range(amount):
            a = angle + rng.uniform(-0.7, 0.7)
            speed = rng.uniform(40, 150)
            self.drops.append([x, y, cos(a) * speed, sin(a) * speed, rng.uniform(14, 26), rng.randint(1, 2)])
        self.age = 0.0
        self.stains = []

    def update(self, dt):
        self.age += dt
        for d in self.drops:
            if d[4] > 0:
                d[0] += d[2] * dt
                d[1] += d[3] * dt
                d[4] -= 90 * dt                      # height above the ground falls
                d[2] *= 0.9
                d[3] *= 0.9
                if d[4] <= 0:
                    self.stains.append((d[0], d[1], d[5], self.colors[1]))
        return any(d[4] > 0 for d in self.drops)

    def landed(self):
        stains, self.stains = self.stains, []
        return stains

    def draw(self, cam_x, cam_y):
        for x, y, vx, vy, h, size in self.drops:
            if h > 0:
                pico2d.draw_rectangle(x - cam_x, y + h - cam_y, x - cam_x + size, y + h - cam_y + size,
                                      *self.colors[0], filled=True)


def draw_stains(stains, cam_x, cam_y):
    """Blood on the ground (stays for the whole area). A stain is (x, y, size[, colour]); red if no colour."""
    for st in stains:
        x, y, size = st[0], st[1], st[2]
        r, g, b = st[3] if len(st) > 3 else BLOOD_RED[1]
        pico2d.draw_rectangle(x - cam_x, y - cam_y, x - cam_x + size + 1, y - cam_y + size, r, g, b, 220,
                              filled=True)


class Tracer:
    """A bullet's line and the flash at the muzzle, gone in a blink."""

    def __init__(self, x0, y0, x1, y1):
        self.a, self.b = (x0, y0), (x1, y1)
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        return self.age < 0.09

    def draw(self, cam_x, cam_y):
        (x0, y0), (x1, y1) = self.a, self.b
        fade = 1 - self.age / 0.09
        pico2d.draw_line(x0 - cam_x, y0 - cam_y, x1 - cam_x, y1 - cam_y, 255, round(200 + 40 * fade), round(140 * fade))
        if self.age < 0.05:                              # the muzzle flash
            pico2d.draw_circle(x0 - cam_x, y0 - cam_y, 5, 255, 236, 170, filled=True)
            pico2d.draw_circle(x0 - cam_x, y0 - cam_y, 2, 255, 255, 240, filled=True)


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
