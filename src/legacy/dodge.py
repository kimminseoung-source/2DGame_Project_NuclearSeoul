"""Perfect dodge and counter, shared by every enemy attack and every weapon.

Dashing at the last moment before a blow lands is a perfect dodge: the scene slows for a
moment and the next blow the hero lands within COUNTER_TIME is a counter (more damage, the
hardest hit feel). A counter started in that time lunges at the dodged enemy (up to
COUNTER_LUNGE), because the dash itself carried the hero out of reach. Any enemy reports
only where its blow would land (reach and depth); the rule here decides, so a new enemy or weapon gets the same dodge and counter for free.
"""

from math import hypot

PERFECT_WINDOW = 0.2       # s: the dash started at most this long before the blow landed
NEAR_MISS = 60             # px beyond the blow's reach that still counts (a dash covers ~48 px)
SLOW_TIME = 0.35           # real seconds the scene runs slowed after a perfect dodge
SLOW_SCALE = 0.3           # game speed during the slow motion
COUNTER_TIME = 1.2         # s after the dodge in which a landed blow is a counter
COUNTER_MULTIPLIER = 2
COUNTER_LUNGE = 64         # px (2 m): how far a counter may carry the hero to its target
LUNGE_TIME = 0.12          # s: the lunge is over by then (or by the blow's contact, if sooner)
LUNGE_STOP = 0.6           # stop at this share of the weapon's reach in front of the target


def is_perfect(target, dx, dy, reach, depth):
    """Did target dash out of a blow that would have hit it (dx, dy from the attacker)?"""
    if getattr(target, "dash_age", PERFECT_WINDOW + 1) > PERFECT_WINDOW:
        return False
    return abs(dx) <= reach + NEAR_MISS and abs(dy) <= depth + NEAR_MISS


def lunge(attacker, target, reach):
    """(dx, dy) that carries attacker in front of target, within its reach, at most
    COUNTER_LUNGE long; (0, 0) if it is already close enough."""
    facing = 1 if target.x >= attacker.x else -1
    dx = target.x - facing * reach * LUNGE_STOP - attacker.x
    if dx * facing < 0:
        dx = 0.0
    dy = target.y - attacker.y
    length = hypot(dx, dy)
    if length > COUNTER_LUNGE:
        dx, dy = dx * COUNTER_LUNGE / length, dy * COUNTER_LUNGE / length
    return dx, dy
