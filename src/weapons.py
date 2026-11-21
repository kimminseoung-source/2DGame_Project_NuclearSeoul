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

from settings import LEGS_AND_CRAWLERS, TEMPO

# Body parts by height above the feet (world units; a person is 54 tall). Generous edges:
# a blow that lands between two parts counts as the torso.
# Heights above the feet, fitted to the hunched infected sprite (2026-11-18, seen with F1: the head
# box was 40-60, above the drawn head; the picture's head is ~35-47, its shoulders ~20).
PARTS = (("legs", 0, 20), ("torso", 20, 35), ("head", 35, 48))
if not LEGS_AND_CRAWLERS:                     # no legs to aim at: the torso reaches down to the feet
    PARTS = (("torso", 0, 35), ("head", 35, 48))
PART_HALF_WIDTH = 13            # world units either side of the infected's middle
PART_NAMES = {"head": "머리", "torso": "몸통", "legs": "다리", "ground": "밟기"}
# Which styles reach a crawler on the ground (2026-11-16, crawlers and standing ones together):
# a chop comes down to the ground; a stab or a swing across passes over it.
REACHES_GROUND = {"chop"}
# A stomp is a kick down at the feet, not a swing of the weapon: it finds a crawler within this
# angle of the aim, measured on the ground (narrow weapon arcs missed a crawler at the feet).
STOMP_ARC = 0.9
# Damage (2026-11-16 "빈틈을 베었다 이런 건 빼죠, 무기마다 데미지가 다른 거지, 공격 데미지 범위가
#다른 걸로"): no blow is a sure kill any more. Each weapon has a damage range; a blow takes a number
# in it off the infected's health, times the part's share (the head only when charged - a quick
# blow always goes for the torso). A stomp has its own range.
PART_SHARE = {"head": 3, "torso": 1, "legs": 1}
STOMP_DAMAGE = (5, 8)


def roll_damage(w, part):
    """Health a blow of weapon `w` on `part` takes off ("ground" = a stomp)."""
    import random
    if part == "ground":
        return random.randint(*STOMP_DAMAGE)
    return random.randint(*w["damage"]) * PART_SHARE[part]

# Each weapon: its style's motion ("pose": a hero sheet), timing, reach, damage per part, stamina,
# push, and its sprite (assets/weapons/<sprite>.png, drawn in the hand on every frame by the game -
# 2026-11-16 "무기를 바꿔도 동작을 안 만들어도 되게끔"). Numbers are ours, to be tuned in play.
WEAPONS = {
    "machete": {
        "name": "마체테", "style": "chop", "pose": "chop", "sprite": "machete",
        "time": 0.42 * TEMPO,       # the whole blow
        "hit": 0.2 * TEMPO,         # when it lands
        "cooldown": 0.12,           # s before the next blow can start
        "lunge": 12.0,              # px stepped in along the aim
        "cells": 2,               # how wide its end is, in cells (CELL_WORLD) - the reach comes from the sprite
        "damage": (3, 4),        # health taken off a torso blow, picked in this range
        "stamina": 14.0,
        "push": 55,                 # px/s a blow that does not kill knocks it back
        "stagger": False,           # a torso blow makes it reel (open), not just flinch
        "good": "균형·기는 놈까지", "bad": "큰 강점 없음",
    },
    # The knife swings like the rest (2026-11-21 "공격 방식은 휘두르기 지금 하나만 하죠"): one body
    # motion for every melee weapon; the knife stays quick and short in its numbers. ("stab" is
    # kept for the pistol until guns get their own motion.)
    "knife": {                      # quick, short: the fastest blow
        "name": "식칼", "style": "chop", "pose": "chop", "sprite": "knife",
        "time": 0.22 * TEMPO, "hit": 0.09 * TEMPO, "cooldown": 0.04, "lunge": 10.0,
        "cells": 1,
        "damage": (2, 3),
        "stamina": 6.0, "push": 25,
        "stagger": False,
        "good": "빠름·기력 적게", "bad": "짧고 좁음",
    },
    # bat and pipe use the overhead chop like the machete and axe (2026-11-16 "야구 방망이 모션이
    # 이상함, 이런 종류의 무기를 도끼나 마체테처럼 똑같이 통일"): their own traits are in the numbers
    "bat": {                        # wide and pushing, weak: keeps them off
        "name": "야구방망이", "style": "chop", "pose": "chop", "sprite": "bat",
        "time": 0.52 * TEMPO, "hit": 0.27 * TEMPO, "cooldown": 0.2, "lunge": 10.0,
        "cells": 2,
        "damage": (2, 4),
        "stamina": 16.0, "push": 150,
        "stagger": True,
        "good": "넓게·몸통 치면 휘청", "bad": "피해 약함",
    },
    "pipe": {                       # like the bat, longer and heavier
        "name": "쇠파이프", "style": "chop", "pose": "chop", "sprite": "pipe",
        "time": 0.6 * TEMPO, "hit": 0.31 * TEMPO, "cooldown": 0.26, "lunge": 10.0,
        "cells": 3,
        "damage": (3, 5),
        "stamina": 18.0, "push": 170,
        "stagger": True,
        "good": "가장 멀리·몸통 치면 휘청", "bad": "느림·기력 많이",
    },
    "axe": {                        # slow and costly, but even the torso takes two
        "name": "소방 도끼", "style": "chop", "pose": "chop", "sprite": "axe",
        "time": 0.78 * TEMPO, "hit": 0.4 * TEMPO, "cooldown": 0.35, "lunge": 10.0,
        "cells": 2,
        "damage": (5, 7),
        "stamina": 22.0, "push": 80,
        "stagger": False,
        "good": "피해 가장 셈", "bad": "가장 느림·기력 많이",
    },
    # A gun (2026-11-17 "총기를 넣고 좀 더 전투 중심으로", first step: one pistol, 6 rounds, a big
    # noise). "shot" makes a weapon a gun: the blow is a bullet along the aim - the first infected
    # on the line up to `range` is hit (walls stop it, windows do not) - and the bang carries
    # `noise` far, so everything around comes. Rounds are counted by the game (Game.ammo); a gun
    # found on the ground comes with `rounds`. Strong but loud: to spare or to shoot.
    "pistol": {
        "name": "권총", "style": "stab", "pose": "stab", "sprite": "pistol",
        "time": 0.3 * TEMPO, "hit": 0.05 * TEMPO, "cooldown": 0.22, "lunge": -5.0,   # a step back: recoil
        "cells": 1,
        "damage": (12, 15),         # ends a plain infected (health 8-12) in one; armour will not
        "stamina": 0.0, "push": 140,
        "stagger": True,
        "shot": {"range": 420.0, "noise": 400, "width": 12.0, "rounds": 6},
        "good": "멀리서 한 방", "bad": "소리가 모두를 부름·탄 적음",
    },
}
# Reach follows the drawn weapon (2026-11-16 "보이는 칼의 길이에 비해 공격 범위가 너무 길다"): the
# blade's tip at the hit = how far the hand is out in that style's hit frame (measured on the hero
# sheets' hand lines, blade.json) + the weapon's own length (its sprite, in world units: dot px x
# 54/32). The shown arc is the tip; a body whose middle is up to BODY_MARGIN past it is still hit
# (half its width). A new weapon's reach comes from its sprite alone.
HAND_REACH = {"stab": 14.0, "chop": 8.0, "swingh": 12.0}
BODY_CONTACT = 20               # px: an infected this close is against the hero's body: any blow hits it (2026-11-16 판정)
BODY_MARGIN = 10.0
SPRITE_TO_WORLD = 54 / 32


def _sprite_length(sprite):
    """Width of assets/weapons/<sprite>.png in px, read from the PNG header (no image library)."""
    import struct
    from settings import ROOT
    with open(ROOT / "assets" / "weapons" / f"{sprite}.png", "rb") as f:
        return struct.unpack(">I", f.read(24)[16:20])[0]


# The range in cells (2026-11-16 "범위를 칸으로 정해서, 식칼은 칸 1개 마체테는 2개"): one cell = 8
# dot px (CELL_WORLD world units). The blow's width at its reach is `cells` cells, and the end of
# the range is a dotted row exactly that wide: the arc is the angle the row covers at the reach.
CELL_WORLD = 8 * SPRITE_TO_WORLD


for _w in WEAPONS.values():
    _w["reach"] = HAND_REACH[_w["style"]] + _sprite_length(_w["sprite"]) * SPRITE_TO_WORLD
    _w["arc"] = _w["cells"] * CELL_WORLD / 2 / (_w["reach"] + _w["lunge"])   # half-angle of the row


# Arcs are narrow (2026-11-16 "공격 범위가 너무 넓어, 세로로 말고 가로로"): a blow covers a long,
# thin strip toward the aim, its end a short arc; the bat is still the widest, the knife the narrowest.
DEFAULT = "machete"
# Carried weapons are bag items "w:<key>" that take cells on the bag's sheet (2026-11-16 "무기를
# 인벤토리나 어디를 통해서 바꿀 수 있게"); the weapon in hand takes none. They lie flat, wide and low.
SHAPE = {"knife": (2, 1), "machete": (4, 1), "bat": (3, 2), "pipe": (3, 2), "axe": (4, 2), "pistol": (2, 1)}
STYLE_TEXT = {"chop": "내려치기 · 바닥에 기는 놈에게도 닿는다", "stab": "찌르기 · 빠르고 짧다",
              "swingh": "가로 휘두르기 · 넓고 밀어낸다"}


def attack_range(w):
    """How far a blow reaches, from where the hero stands when it starts: its reach plus the step
    in. The dotted path, the aim and the hit all use this one number (2026-11-16 "보이는 점선
    범위가 공격 범위랑 동일하게"). A gun reaches as far as its bullet flies."""
    if "shot" in w:
        return w["shot"]["range"]
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

# The charge (2026-11-16 "차징이 이러면 이득이 있나"): a quick click always goes for the torso
# (a crawler is stomped); holding until the range arc is full (CHARGE_TIME) lets the cursor pick
# the head or the legs, and the blow is let go at once. Holding costs a slow step and stamina.
CHARGE_TIME = 0.35 * TEMPO      # s to fill the charge
READY_SPEED = 0.5               # share of the walking speed while holding the blow ready
READY_DRAIN = 4.0               # stamina per second while holding it
READY_SKIP = 0.7                # share of the wind-up skipped when a held blow is let go
QUICK_SKIP = 0.5                # share of the wind-up skipped by a plain click (2026-11-20 "클릭 공격의
                                # 준비 동작 시간을 줄여야"); less than READY_SKIP, so aiming still pays
QUICK_PRESS = 0.15              # s: a press shorter than this is a plain click (a full blow)


# Aiming along the path (not on the body): the height where the path passes the infected's
# middle picks the part, with wider head and leg bands - a raised cursor reads as "the head".
PATH_PARTS = (("legs", -99, 18), ("torso", 18, 33), ("head", 33, 99))
if not LEGS_AND_CRAWLERS:
    PATH_PARTS = (("torso", -99, 33), ("head", 33, 99))


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
