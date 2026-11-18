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
# 2026-11-16 "주변을 살짝만 더 보이게 하고 좌우 시야 범위를 좁히는 게 좋을 듯": the cone was
# 0.9 rad a side (~103 degrees) and the circle around the body 30 px; now a narrower cone and a
# slightly larger circle.
CONE_HALF = 0.7            # radians either side of the look direction (~80 degrees in all)
CONE_SOFT = 0.16           # radians over which the cone's sides fade into the dark
# 2026-11-16 "앞을 볼 수 있는 시야가 살짝 더 커야 할 듯, 맵이 커지게 된다면": 250 -> 330, so the
# cone's end reaches about the side of the screen at the default zoom.
CONE_RANGE = 400           # px the cone reaches (2026-11-18 "앞 시야가 조금 더 길어도": was 330)
RANGE_SOFT = 50
NEAR_CLEAR = 40            # px around the body that is always lit (melee range and a little more)
NEAR_SOFT = 24
# 2026-11-18 "주변(빨간 부분)은 살짝 연하게 보여도 괜찮을 것 같다": a ring around the body, out to
# NEAR_GLOW, is only partly dark - GLOW_DARK of the full darkness - so what is close is faintly seen.
NEAR_GLOW = 120
GLOW_SOFT = 30
GLOW_DARK = 0.5
STEPS = 96                 # mesh resolution around the eye
RADII = (0, 15, 30, 40, 52, 64, 80, 120, 160, 200, 250, 290, 330, 355, 380, 900)
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


def alpha_at(dx, dy, look, scale=1.0, fog=FOG):
    """Darkness 0..fog at offset (dx, dy) from the eye when looking toward angle `look`;
    `scale` < 1 narrows and shortens the cone (panic); `fog` is how dark it is outside the light
    (lower by day, daylight.py)."""
    r = hypot(dx, dy)
    near = GLOW_DARK * _ramp((r - NEAR_CLEAR) / NEAR_SOFT) + (1 - GLOW_DARK) * _ramp((r - NEAR_GLOW) / GLOW_SOFT)
    off = abs((atan2(dy, dx) - look + pi) % (2 * pi) - pi)
    cone = max(_ramp((off - CONE_HALF * scale) / CONE_SOFT), _ramp((r - CONE_RANGE * scale) / RANGE_SOFT))
    return fog * min(near, cone)


class VisionCone:
    def __init__(self, blockers=(), nearby=None):
        self.blockers = list(blockers)
        # nearby(l, b, r, t) -> the blockers that may touch that box (a spatial index); without
        # one every blocker is looked at
        self.nearby = nearby or (lambda l, b, r, t: self.blockers)
        self.scale = 1.0                 # < 1 while panicking: a narrower, shorter cone
        self.fog = FOG                   # darkness outside the light: lower by day (daylight.py);
                                         # behind walls it stays FOG
        n, m = STEPS, len(RADII) + 2 + 4     # + the shadow's start and end, + the glow's and the cone's edges
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
        dark = alpha_at(dx, dy, look, self.scale, self.fog)
        if r > 0 and self.blockers:
            hit = ray_hit(eye[0], eye[1], dx / r, dy / r,
                          self.nearby(min(eye[0], x), min(eye[1], y), max(eye[0], x), max(eye[1], y)))
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
        # only what stands within the light's reach can cast a shadow that shows (a real-map area
        # has ~150 building rectangles: every ray against all of them was needless work)
        reach = CONE_RANGE + RANGE_SOFT
        near = [(l, b, r, t) for l, b, r, t in self.nearby(eye[0] - reach, eye[1] - reach, eye[0] + reach, eye[1] + reach)
                if max(l - eye[0], 0, eye[0] - r) ** 2 + max(b - eye[1], 0, eye[1] - t) ** 2 <= reach * reach]
        for a, angle in enumerate(self.angles):
            ca, sa = cos(angle), sin(angle)
            hit = ray_hit(eye[0], eye[1], ca, sa, near) if near else FAR
            edges = (NEAR_GLOW, NEAR_GLOW + GLOW_SOFT, CONE_RANGE * self.scale, CONE_RANGE * self.scale + RANGE_SOFT)
            radii = sorted(RADII + (min(hit, FAR - 1), min(hit + SHADOW_SOFT, FAR)) + tuple(min(e, FAR) for e in edges))
            for k, radius in enumerate(radii):
                v = self.vertices[a * m + k]
                dx, dy = ca * radius, sa * radius
                v.position.x = ox + dx
                v.position.y = view_h - 1 - (oy + dy)
                v.color.r, v.color.g, v.color.b = 6, 8, 12
                dark = alpha_at(dx, dy, look, self.scale, self.fog)
                if radius > hit:
                    dark = max(dark, FOG * _ramp((radius - hit) / SHADOW_SOFT))
                v.color.a = round(dark)
        sdl2.SDL_RenderGeometry(renderer, None, self.vertices, self.count, self.indices, len(self.indices))
