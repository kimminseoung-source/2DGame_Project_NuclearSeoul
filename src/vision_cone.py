"""Facing vision (2026-11-14, "내가 바라보는 방향만 보이면 좋겠음"): the world is dark except a cone
in the direction the hero looks and a small clear circle around the hero's own body.

Anything that stands on the ground (infected, other people) is only drawn where the light
reaches - check `visible()` before drawing it. The darkness is drawn as one mesh of triangles
around the eye whose corner alphas come from `alpha_at`, so the cone and the circle blend into
each other with soft edges and no overdraw problems.

Works for any view that draws into a render target with pico2d's y-up coordinates.
"""

from math import atan2, cos, hypot, pi, sin

import sdl2
from pico2d import pico2d as canvas

FOG = 228                  # darkness outside the light (255 = pitch black)
HIDE_FROM = 150            # bodies are hidden where the darkness is at least this strong
CONE_HALF = 0.9            # radians either side of the look direction (~100 degrees in all)
CONE_SOFT = 0.16           # radians over which the cone's sides fade into the dark
CONE_RANGE = 250           # px the cone reaches
RANGE_SOFT = 50
NEAR_CLEAR = 30            # px around the body that is always lit (melee range)
NEAR_SOFT = 22
STEPS = 96                 # mesh resolution around the eye
RADII = (0, 15, 30, 41, 52, 80, 120, 160, 200, 250, 275, 300, 900)


def _ramp(value):
    return 0.0 if value <= 0 else 1.0 if value >= 1 else value


def alpha_at(dx, dy, look):
    """Darkness 0..FOG at offset (dx, dy) from the eye when looking toward angle `look`."""
    r = hypot(dx, dy)
    near = _ramp((r - NEAR_CLEAR) / NEAR_SOFT)
    off = abs((atan2(dy, dx) - look + pi) % (2 * pi) - pi)
    cone = max(_ramp((off - CONE_HALF) / CONE_SOFT), _ramp((r - CONE_RANGE) / RANGE_SOFT))
    return FOG * min(near, cone)


class VisionCone:
    def __init__(self):
        n, m = STEPS, len(RADII)
        self.count = n * m
        self.vertices = (sdl2.SDL_Vertex * self.count)()
        indices = []
        for a in range(n):
            b = (a + 1) % n
            for k in range(m - 1):
                p, q, r, s = a * m + k, b * m + k, a * m + k + 1, b * m + k + 1
                indices += [p, q, r, q, s, r]
        self.indices = (sdl2.c_int * len(indices))(*indices)
        self.angles = [2 * pi * a / n for a in range(n)]

    def visible(self, eye, look, x, y):
        return alpha_at(x - eye[0], y - eye[1], look) < HIDE_FROM

    def draw(self, eye, look, view_w, view_h):
        """Darken the current render target (view_w x view_h, y up) around the eye."""
        renderer = canvas.renderer
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        ex, ey = eye
        m = len(RADII)
        for a, angle in enumerate(self.angles):
            ca, sa = cos(angle), sin(angle)
            for k, radius in enumerate(RADII):
                v = self.vertices[a * m + k]
                dx, dy = ca * radius, sa * radius
                v.position.x = ex + dx
                v.position.y = view_h - 1 - (ey + dy)
                v.color.r, v.color.g, v.color.b = 6, 8, 12
                v.color.a = round(alpha_at(dx, dy, look))
        sdl2.SDL_RenderGeometry(renderer, None, self.vertices, self.count, self.indices, len(self.indices))
