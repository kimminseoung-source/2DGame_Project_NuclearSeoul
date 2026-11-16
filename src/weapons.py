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
PART_NAMES = {"head": "머리", "torso": "몸통", "legs": "다리", "ground": "밟기"}
# Which styles reach a crawler on the ground (2026-11-16, crawlers and standing ones together):
# a chop comes down to the ground; a stab or a swing across passes over it.
REACHES_GROUND = {"chop"}
HEAD_QUICK = 1                  # damage taken off a head blow that was not aimed (held ready)

# Each weapon: its style's motion ("pose": a hero sheet), timing, reach, damage per part, stamina,
# push, and its sprite (assets/weapons/<sprite>.png, drawn in the hand on every frame by the game -
# 2026-11-16 "무기를 바꿔도 동작을 안 만들어도 되게끔"). Numbers are ours, to be tuned in play.
WEAPONS = {
    "machete": {
        "name": "마체테", "style": "chop", "pose": "chop", "sprite": "machete",
        "time": 0.42 * TEMPO,       # the whole blow
        "hit": 0.2 * TEMPO,         # when it lands
        "cooldown": 0.12,           # s before the next blow can start
        "lunge": 24.0,              # px stepped in along the aim
        "reach": 58.0, "arc": 1.0,  # px from chest to chest, radians either side of the aim
        "damage": {"head": 3, "torso": 1, "legs": 1},   # an aware infected takes 2-3
        "stamina": 14.0,
        "push": 55,                 # px/s a blow that does not kill knocks it back
    },
    "knife": {                      # quick, short, precise: a stab to the head ends it
        "name": "식칼", "style": "stab", "pose": "stab", "sprite": "knife",
        "time": 0.22 * TEMPO, "hit": 0.09 * TEMPO, "cooldown": 0.04, "lunge": 18.0,
        "reach": 44.0, "arc": 0.45,
        "damage": {"head": 3, "torso": 1, "legs": 1},
        "stamina": 8.0, "push": 25,
    },
    "bat": {                        # wide and pushing, weak: keeps them off
        "name": "야구방망이", "style": "swingh", "pose": "swingh", "sprite": "bat",
        "time": 0.52 * TEMPO, "hit": 0.27 * TEMPO, "cooldown": 0.2, "lunge": 16.0,
        "reach": 62.0, "arc": 1.35,
        "damage": {"head": 2, "torso": 1, "legs": 1},
        "stamina": 16.0, "push": 150,
    },
    "pipe": {                       # like the bat, longer and heavier
        "name": "쇠파이프", "style": "swingh", "pose": "swingh", "sprite": "pipe",
        "time": 0.6 * TEMPO, "hit": 0.31 * TEMPO, "cooldown": 0.26, "lunge": 16.0,
        "reach": 66.0, "arc": 1.3,
        "damage": {"head": 2, "torso": 1, "legs": 2},
        "stamina": 18.0, "push": 170,
    },
    "axe": {                        # slow and costly, but even the torso takes two
        "name": "소방 도끼", "style": "chop", "pose": "chop", "sprite": "axe",
        "time": 0.78 * TEMPO, "hit": 0.4 * TEMPO, "cooldown": 0.35, "lunge": 20.0,
        "reach": 60.0, "arc": 0.9,
        "damage": {"head": 3, "torso": 2, "legs": 2},
        "stamina": 22.0, "push": 80,
    },
}
DEFAULT = "machete"
# Carried weapons are bag items "w:<key>" with a weight, so they take cells on the bag's sheet
# (2026-11-16 "무기를 인벤토리나 어디를 통해서 바꿀 수 있게"); the weapon in hand weighs nothing.
WEIGHT = {"machete": 0.4, "knife": 0.2, "bat": 0.6, "pipe": 0.6, "axe": 0.8}
STYLE_TEXT = {"chop": "내려치기 · 바닥에 기는 놈에게도 닿는다", "stab": "찌르기 · 빠르고 짧다",
              "swingh": "가로 휘두르기 · 넓고 밀어낸다"}


def attack_range(w):
    """How far a blow reaches, from where the hero stands when it starts: its reach plus the step
    in. The dotted path, the aim and the hit all use this one number (2026-11-16 "보이는 점선
    범위가 공격 범위랑 동일하게")."""
    return w["reach"] + w["lunge"]


def speed_word(w):
    t = w["time"] + w["cooldown"]
    return "빠름" if t < 0.45 else "보통" if t < 0.8 else "느림"


def item(key):
    return f"w:{key}"


def key_of(kind):
    """The weapon key of a bag item, or None when it is not a weapon."""
    return kind[2:] if kind.startswith("w:") else None


def key_of_weapon(weapon):
    return next(k for k, v in WEAPONS.items() if v is weapon)

READY_SPEED = 0.5               # share of the walking speed while holding the blow ready
READY_DRAIN = 4.0               # stamina per second while holding it
READY_SKIP = 0.7                # share of the wind-up skipped when a held blow is let go
QUICK_PRESS = 0.15              # s: a press shorter than this is a plain click (a full blow)


# Aiming along the path (not on the body): the height where the path passes the infected's
# middle picks the part, with wider head and leg bands - a raised cursor reads as "the head".
PATH_PARTS = (("legs", -99, 16), ("torso", 16, 33), ("head", 33, 99))


def path_part(z, up):
    """The part the path of a blow reaches, passing the infected `up` units above its feet."""
    if z.prone:
        return "ground" if up < 16 else None                     # a crawler: aim low to stomp it
    return next(part for part, low, high in PATH_PARTS if low <= up < high)


_images = {}


def image(sprite):
    """The weapon's sprite (assets/weapons/<sprite>.png, tools/sprites/weapons.py), loaded once."""
    if sprite not in _images:
        import pico2d
        from settings import ROOT
        _images[sprite] = pico2d.load_image(str(ROOT / "assets" / "weapons" / f"{sprite}.png"))
    return _images[sprite]


def part_at(z, wx, wy):
    """The part of infected `z` under the world point (wx, wy), or None when it is not on it.
    Crawlers lie on the ground: the whole of them is one target (they are stomped)."""
    if abs(wx - z.x) > PART_HALF_WIDTH * (2.2 if z.prone else 1):
        return None
    up = wy - z.y
    if z.prone:
        return "ground" if -4 <= up <= 16 else None
    for part, low, high in PARTS:
        if low <= up < high:
            return part
    return None
