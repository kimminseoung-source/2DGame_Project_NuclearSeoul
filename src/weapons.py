"""Weapons and where a blow lands (2026-11-16 "무기를 다양하게", "맞는 위치에 따라 데미지가 다르게",
"마우스 커서 방향에 따라 공격 위치가 달라지게"). Every weapon is one entry of data; the hero's attack,
the aim and the hit read only this, so a new weapon is a new entry (and a sprite for the painter).

Styles share one plain motion each (hero sheets, made in tools/blender/made_actions.py):
- "stab"   a straight thrust (knife): short, narrow, precise
- "swingh" a swing across the front (bat, pipe): wide, pushes back
- "chop"   overhead and down (machete, axe): heavy, strong on the head

Parts: the cursor over an infected picks the part it aims at (head / torso / legs, by height
on the body); anywhere else the blow goes that way at torso height.
- head:  big damage (a sure kill with a chop or a stab), hard to hit - the smallest part
- torso: normal damage, the infected flinches and its attack is broken off
- legs:  little damage, but it loses its legs and crawls from then on (stomp it)
"""

from settings import TEMPO

# Body parts by height above the feet (world units; a person is 54 tall). Generous edges:
# a blow that lands between two parts counts as the torso.
PARTS = (("legs", 0, 18), ("torso", 18, 40), ("head", 40, 60))
PART_HALF_WIDTH = 13            # world units either side of the infected's middle
PART_NAMES = {"head": "머리", "torso": "몸통", "legs": "다리"}

WEAPONS = {
    "machete": {
        "name": "마체테", "style": "chop", "pose": "chop",
        "time": 0.42 * TEMPO,       # the whole blow
        "hit": 0.2 * TEMPO,         # when it lands
        "lunge": 24.0,              # px stepped in along the aim
        "reach": 58.0, "arc": 1.0,  # px from chest to chest, radians either side of the aim
        "damage": {"head": 3, "torso": 1, "legs": 1},   # an aware infected takes 2-3
        "stamina": 14.0,
        "push": 55,                 # px/s a blow that does not kill knocks it back
    },
}
DEFAULT = "machete"

READY_SPEED = 0.5               # share of the walking speed while holding the blow ready
READY_DRAIN = 4.0               # stamina per second while holding it
READY_SKIP = 0.7                # share of the wind-up skipped when a held blow is let go
QUICK_PRESS = 0.15              # s: a press shorter than this is a plain click (a full blow)


def part_at(z, wx, wy):
    """The part of infected `z` under the world point (wx, wy), or None when it is not on it.
    Crawlers lie on the ground: the whole of them is one target (they are stomped)."""
    if abs(wx - z.x) > PART_HALF_WIDTH * (2.2 if z.prone else 1):
        return None
    up = wy - z.y
    if z.prone:
        return "torso" if -4 <= up <= 16 else None
    for part, low, high in PARTS:
        if low <= up < high:
            return part
    return None
