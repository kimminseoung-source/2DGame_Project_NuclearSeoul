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
STEPS = 96                 # mesh resolution around the eye (even spokes)
MAX_EXTRA = 160            # more spokes, through the corners of near blockers and the cone's sides
CORNER_EPS = 0.002         # radians either side of a corner its two spokes go
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
        m = len(RADII) + 2 + 4           # + the shadow's start and end, + the glow's and the cone's edges
        self.spoke = m
        # spokes: STEPS even ones + up to MAX_EXTRA through blocker corners and the cone's sides, and
        # the first again at the end (so neighbours are always a, a + 1 and the triangles are fixed)
        most = STEPS + MAX_EXTRA + 1
        self.vertices = (sdl2.SDL_Vertex * (most * m))()
        indices = []
        for a in range(most - 1):
            for k in range(m - 1):
                p, q, r, s = a * m + k, (a + 1) * m + k, a * m + k + 1, (a + 1) * m + k + 1
                indices += [p, q, r, q, s, r]
        self.indices = (sdl2.c_int * len(indices))(*indices)
        self.angles = [2 * pi * a / STEPS for a in range(STEPS)]
        for v in self.vertices:                    # the colour of the dark never changes, only its alpha
            v.color.r, v.color.g, v.color.b = 6, 8, 12

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
        # Rays through every corner of what is near, just either side of it (2026-11-18 "장애물 뒤
        # 그림자 인식이 이상"): with only the even spokes (3.75 degrees apart) the triangle between a
        # ray that passed a car and one that hit it blended the two, so the shadow's edge smeared
        # sideways over lit ground - wider the farther away. A corner ray puts a spoke exactly on the
        # edge (the visibility-polygon way of 2D lights).
        ex, ey = eye
        side = CONE_HALF * self.scale
        night = self.fog >= FOG - 1                    # outside the cone it is as dark as a shadow
        lit_ring = NEAR_GLOW + GLOW_SOFT
        extra = []
        near.sort(key=lambda bl: max(bl[0] - ex, 0, ex - bl[2]) ** 2 + max(bl[1] - ey, 0, ey - bl[3]) ** 2)
        for l, b, r, t in near:
            close = max(l - ex, 0, ex - r) ** 2 + max(b - ey, 0, ey - t) ** 2 <= lit_ring * lit_ring
            for x, y in ((l, b), (r, b), (r, t), (l, t)):
                a = atan2(y - ey, x - ex)
                # at night a corner outside the cone changes nothing on screen (dark both sides),
                # unless the blocker is inside the half-lit ring round the body
                if night and not close and abs((a - look + pi) % (2 * pi) - pi) > side + CONE_SOFT + 0.05:
                    continue
                extra += [a - CORNER_EPS, a + CORNER_EPS]
            if len(extra) >= MAX_EXTRA - 4:
                break
        extra += [look - side - CONE_SOFT, look - side, look + side, look + side + CONE_SOFT]
        angles = sorted({a % (2 * pi) for a in self.angles + extra[:MAX_EXTRA]})
        angles.append(angles[0] + 2 * pi)                  # close the ring
        # the same darkness as alpha_at, split: along one spoke the direction never changes, so the
        # cone's side term is worked out once per spoke and only the distance terms per point
        fog, reach_c = self.fog, CONE_RANGE * self.scale
        edges = (NEAR_GLOW, NEAR_GLOW + GLOW_SOFT, reach_c, reach_c + RANGE_SOFT)
        verts, flip = self.vertices, view_h - 1
        for a, angle in enumerate(angles):
            ca, sa = cos(angle), sin(angle)
            hit = ray_hit(ex, ey, ca, sa, near) if near else FAR
            off = abs((angle - look + pi) % (2 * pi) - pi)
            side_dark = _ramp((off - side) / CONE_SOFT)
            radii = sorted(RADII + (min(hit, FAR - 1), min(hit + SHADOW_SOFT, FAR)) + tuple(min(e, FAR) for e in edges))
            base = a * m
            for k, radius in enumerate(radii):
                v = verts[base + k]
                v.position.x = ox + ca * radius
                v.position.y = flip - (oy + sa * radius)
                near_dark = GLOW_DARK * _ramp((radius - NEAR_CLEAR) / NEAR_SOFT) + (1 - GLOW_DARK) * _ramp((radius - NEAR_GLOW) / GLOW_SOFT)
                dark = fog * min(near_dark, max(side_dark, _ramp((radius - reach_c) / RANGE_SOFT)))
                if radius > hit:
                    dark = max(dark, FOG * _ramp((radius - hit) / SHADOW_SOFT))
                v.color.a = round(dark)
        n = len(angles)
        sdl2.SDL_RenderGeometry(renderer, None, self.vertices, n * m, self.indices, (n - 1) * (m - 1) * 6)
