"""What high exposure does to the hero's eyes: the street around stays clear (melee is not
blinded), everything beyond darkens and, later, swims in a green haze; in the last stage
the edges pulse red as the body breaks down.

The clear circle shrinks with the stage, so enemies coming from afar are seen late - the
pressure is on what is coming, not on the fight in front (2026-11-13 decision "가운데 맑게").
One white mask image (tools/sprites/make_vision_mask.py) is scaled, tinted and faded.
"""

from math import sin

import pico2d
import sdl2

import camera
import game_clock
import ui

MASK_CLEAR = 48                # the mask image's clear radius in px (make_vision_mask.py)
STREET_HEIGHT = 480            # the street region (the top HUD strip is not darkened)

# Per exposure stage: (clear radius px, darkness 0..1, green haze 0..1). 32 px = 1 m.
STAGE_LOOK = (
    (None, 0.0, 0.0),
    (128, 0.55, 0.0),          # 30 %+: 4 m clear, the rest darkens
    (96, 0.65, 0.20),          # 60 %+: 3 m, green haze swimming
    (80, 0.72, 0.26),          # 90 %+: 2.5 m, red pulse (health draining)
)
EASE = 1.5                     # how fast the look follows the stage (per second)


class ExposureVision:
    def __init__(self, exposure, hero, mask_image):
        self.exposure = exposure
        self.hero = hero
        self.mask = mask_image
        self.radius = 160.0
        self.dark = 0.0
        self.haze = 0.0
        self.red = 0.0
        self.age = 0.0

    def update(self):
        dt = game_clock.real_frame_time
        self.age += dt
        radius, dark, haze = STAGE_LOOK[self.exposure.stage]
        follow = min(1.0, dt * EASE * 4)
        self.dark += (dark - self.dark) * follow
        self.haze += (haze - self.haze) * follow
        if radius is not None:
            self.radius += (radius - self.radius) * follow
        last = self.exposure.stage == len(STAGE_LOOK) - 1
        self.red = max(0.0, self.red - dt * 2) if not last else 0.35 + 0.35 * sin(self.age * 5)

    def draw(self):
        if self.dark < 0.01 and self.red < 0.01:
            return
        x, y = self.hero.x - camera.x, self.hero.y + 20
        wobble = 1 + 0.04 * self.haze * sin(self.age * 2.3)       # the haze breathes
        self.layer(x, y, self.radius * wobble, (0, 0, 0), self.dark)
        if self.haze > 0.01:
            self.layer(x, y, self.radius * 1.15 * wobble, (60, 200, 90), self.haze * (0.75 + 0.25 * sin(self.age * 3)))
        if self.red > 0.01:
            self.layer(x, y, self.radius * 1.3, (210, 30, 30), self.red * 0.6)

    def layer(self, x, y, radius, color, alpha):
        """The mask scaled so its clear core has this radius, plus solid fill beyond it."""
        size = self.mask.w * radius / MASK_CLEAR
        a = round(255 * max(0.0, min(1.0, alpha)))
        sdl2.SDL_SetTextureColorMod(self.mask.texture, *color)
        self.mask.opacify(alpha)
        self.mask.draw(x, y, size, size)
        self.mask.opacify(1.0)
        sdl2.SDL_SetTextureColorMod(self.mask.texture, 255, 255, 255)
        left, right = x - size / 2, x + size / 2
        bottom, top = y - size / 2, y + size / 2
        width = ui.SCREEN_WIDTH
        for x1, y1, x2, y2 in ((0, 0, width, bottom), (0, top, width, STREET_HEIGHT),
                               (0, bottom, left, top), (right, bottom, width, top)):
            if x2 > x1 and y2 > y1:
                pico2d.draw_rectangle(x1, max(0, y1), x2, min(STREET_HEIGHT, y2), *color, a, filled=True)
