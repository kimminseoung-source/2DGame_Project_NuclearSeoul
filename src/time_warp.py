"""Mutation time warp (변이 가속): while held, the world crawls and the hero speeds up.

Blows landed during the warp do not hit at once: each target keeps them (stored hits) and
they all burst when the warp ends (release, or exposure at its limit). Any unit can be a
target: it only needs a `stored_hits` list (zombie.py). Numbers in one place.
"""

WORLD_SCALE = 0.10        # the world's speed at full warp
HERO_SCALE = 1.30         # the hero's speed at full warp (moves and swings faster)
ENTER_TIME = 0.15         # seconds to slide into the warp
EXIT_TIME = 0.10          # seconds to slide back out
BURST_INTERVAL = 0.06     # seconds between stored blows popping on release


class TimeWarp:
    def __init__(self):
        self.held = False
        self.blend = 0.0          # 0 normal time ... 1 full warp

    def update(self, frame_time):
        """frame_time in real seconds."""
        if self.held:
            self.blend = min(1.0, self.blend + frame_time / ENTER_TIME)
        else:
            self.blend = max(0.0, self.blend - frame_time / EXIT_TIME)

    @property
    def active(self):
        return self.blend > 0

    @property
    def world_scale(self):
        return 1 + (WORLD_SCALE - 1) * self.blend

    @property
    def hero_scale(self):
        return 1 + (HERO_SCALE - 1) * self.blend


class Hit:
    """A blow kept for the burst: everything needed to land it later."""

    def __init__(self, damage, direction, push, heavy, critical):
        self.damage = damage
        self.direction = direction
        self.push = push
        self.heavy = heavy
        self.critical = critical
