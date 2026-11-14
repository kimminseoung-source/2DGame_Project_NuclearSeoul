"""Facing vision (2026-11-14, "내가 바라보는 방향만 보이면 좋겠음"): the world is dark except a cone
in the direction the hero looks and a small clear circle around the hero's own body.

Anything that stands on the ground (infected, other people) is only drawn where the light
reaches - check `visible()` before drawing it. The darkness is drawn as one mesh of triangles
around the eye whose corner alphas come from `alpha_at`, so the cone and the circle blend into
each other with soft edges and no overdraw problems.

Walls and wrecks block the light (2026-11-14, step 1 after "나쁘지 않음"): pass their ground
rectangles as `blockers`; behind them it is as dark as outside the cone, and bodies there are
hidden too. Each mesh spoke gets two extra corners where its ray leaves the first blocker it
meets (the blocker itself stays lit, as a wall seen from the front), so the shadow starts exactly there and fades in over SHADOW_SOFT px.

Works for any view that draws into a render target with pico2d's y-up coordinates. Positions
given to it are on the ground; `origin` is where the eye is on screen.
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
FAR = RADII[-1]
SHADOW_SOFT = 10           # px behind a blocker's edge over which its shadow darkens


def _ramp(value):
    return 0.0 if value <= 0 else 1.0 if value >= 1 else value


def ray_hit(x, y, ux, uy, blockers):
    """Distance along (ux, uy) from (x, y) to where the shadow starts: the far side of the
    first blocker the ray meets (the blocker itself stays lit), FAR if none."""
    best, exit_at = FAR, FAR
    for left, bottom, right, top in blockers:
        if left <= x <= right and bottom <= y <= top:
            continue                                   # standing inside one: ignore it
        near, far = 0.0, FAR
        for p, u, lo, hi in ((x, ux, left, right), (y, uy, bottom, top)):
            if abs(u) < 1e-9:
                if not lo <= p <= hi:
                    near, far = 1.0, 0.0
                continue
            t1, t2 = (lo - p) / u, (hi - p) / u
            near, far = max(near, min(t1, t2)), min(far, max(t1, t2))
        if near <= far and near < best:
            best, exit_at = near, far
    return exit_at


def alpha_at(dx, dy, look):
    """Darkness 0..FOG at offset (dx, dy) from the eye when looking toward angle `look`."""
    r = hypot(dx, dy)
    near = _ramp((r - NEAR_CLEAR) / NEAR_SOFT)
    off = abs((atan2(dy, dx) - look + pi) % (2 * pi) - pi)
    cone = max(_ramp((off - CONE_HALF) / CONE_SOFT), _ramp((r - CONE_RANGE) / RANGE_SOFT))
    return FOG * min(near, cone)


class VisionCone:
    def __init__(self, blockers=()):
        self.blockers = list(blockers)
        n, m = STEPS, len(RADII) + 2
        self.spoke = m
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

    def darkness(self, eye, look, x, y):
        dx, dy = x - eye[0], y - eye[1]
        r = hypot(dx, dy)
        dark = alpha_at(dx, dy, look)
        if r > 0 and self.blockers:
            hit = ray_hit(eye[0], eye[1], dx / r, dy / r, self.blockers)
            if r > hit:
                dark = max(dark, FOG * _ramp((r - hit) / SHADOW_SOFT))
        return dark

    def visible(self, eye, look, x, y):
        return self.darkness(eye, look, x, y) < HIDE_FROM

    def draw(self, eye, look, origin, view_w, view_h):
        """Darken the current render target (view_w x view_h, y up); eye on the ground,
        origin = the eye's spot on screen."""
        renderer = canvas.renderer
        sdl2.SDL_SetRenderDrawBlendMode(renderer, sdl2.SDL_BLENDMODE_BLEND)
        ox, oy = origin
        m = self.spoke
        for a, angle in enumerate(self.angles):
            ca, sa = cos(angle), sin(angle)
            hit = ray_hit(eye[0], eye[1], ca, sa, self.blockers) if self.blockers else FAR
            radii = sorted(RADII + (min(hit, FAR - 1), min(hit + SHADOW_SOFT, FAR)))
            for k, radius in enumerate(radii):
                v = self.vertices[a * m + k]
                dx, dy = ca * radius, sa * radius
                v.position.x = ox + dx
                v.position.y = view_h - 1 - (oy + dy)
                v.color.r, v.color.g, v.color.b = 6, 8, 12
                dark = alpha_at(dx, dy, look)
                if radius > hit:
                    dark = max(dark, FOG * _ramp((radius - hit) / SHADOW_SOFT))
                v.color.a = round(dark)
        sdl2.SDL_RenderGeometry(renderer, None, self.vertices, self.count, self.indices, len(self.indices))
