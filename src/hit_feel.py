"""How hard a blow feels, shared by every attack.

Any attack (the bat now; other weapons, skills and enemy blows later) reports only
the damage it dealt and its target. The weight comes from the share of the target's
maximum health that one hit took, so a bigger hit always feels bigger, whatever
made it. Weapons and skills never carry their own hit-stop, shake or number size:
tune the feel here, once, for all of them.
"""

from collections import namedtuple

import ui


LIGHT, MEDIUM, HEAVY, CRUSHING = range(4)
# Share of the target's maximum health from which a hit counts as medium / heavy.
MEDIUM_SHARE = 0.5
HEAVY_SHARE = 0.75

Feel = namedtuple("Feel", "hitstop shake shake_time number_size number_color pop")
# hitstop: seconds the scene freezes; shake: pixels and seconds of screen shake;
# number: size and colour of the damage number; pop: how far it overshoots on appearing.
FEELS = {
    LIGHT: Feel(0.04, 0, 0.0, 22, (255, 186, 140), 0.25),
    MEDIUM: Feel(0.075, 2, 0.15, 27, ui.DANGER, 0.4),
    HEAVY: Feel(0.11, 4, 0.22, 32, (240, 84, 62), 0.55),
    CRUSHING: Feel(0.16, 7, 0.3, 35, (240, 84, 62), 0.7),
}


def weight(damage, target_max_hp, critical=False, finishing=False):
    """Weight class of one hit: critical and finishing blows always land the hardest."""
    if critical or finishing:
        return CRUSHING
    share = damage / max(1, target_max_hp)
    if share >= HEAVY_SHARE:
        return HEAVY
    return MEDIUM if share >= MEDIUM_SHARE else LIGHT


def feel(hit_weight):
    return FEELS[hit_weight]
