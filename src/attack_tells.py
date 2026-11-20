"""Where an infected's claw will land, shown faintly on the ground while it winds up (2026-11-20,
docs/plans/2026-11-20_피폭체_공격_예고.md: "상대 몬스터가 공격할 때 히트 판정이 살짝 보이게").

The wedge is the claw's real reach and arc (the same as the F1 view and the hit test): reach + 8
out from its feet, ZOMBIE_ARC either side of where it lunged. A stipple of dark red fills it from
the inside as the wind-up runs out; in the counter window (a shove then staggers it) it turns a
little brighter. If the hero is outside the wedge everything is sparser, so the one that can hit
stands out. Drawn on the ground, under the bodies.
"""

from math import atan2, cos, hypot, pi

import ground_marks as gm
from infected import COUNTER_WINDOW
from settings import ZOMBIE_ARC, DOT

EDGE = (120, 36, 34)           # the wedge's outline while it winds up
FILL = (86, 26, 26)            # the filling stipple
EDGE_NOW = (196, 64, 52)       # in the counter window: "shove now"
FILL_NOW = (132, 40, 36)
RING = 3                       # canvas px between the filling arcs


def wedge_of(z):
    """(x, y, radius, heading, half angle) of the claw, as the hit test uses it."""
    return z.x, z.y, z.reach + 8, z.heading, ZOMBIE_ARC


def can_hit(z, hx, hy):
    x, y, r, ang, half = wedge_of(z)
    if hypot(hx - x, hy - y) > r:
        return False
    return abs((atan2(hy - y, hx - x) - ang + pi) % (2 * pi) - pi) <= half


def draw(game, cx, cy):
    if not getattr(game.dev, "tells", True):
        return
    hero = game.hero
    for z in game.zombies:
        if not z.alive or z.state != "windup":
            continue
        x, y, r, ang, half = wedge_of(z)
        x, y = x - cx, y - cy
        now = z.timer <= COUNTER_WINDOW
        sparse = 1 if can_hit(z, hero.x, hero.y) else 2      # the one that cannot reach is fainter
        edge, fill = (EDGE_NOW, FILL_NOW) if now else (EDGE, FILL)
        gm.wedge(x, y, r, ang, half, edge, gap=2 * sparse)
        grown = r * min(1.0, 1 - z.timer / max(1e-6, z.windup))
        step = RING / DOT * sparse
        k = step
        while k < grown:
            gm.arc(x, y, k, ang - half, ang + half, fill, gap=3 * sparse)
            k += step
