"""Mutation time warp (변이 가속): while the right button is held the world crawls and the
hero gathers power in place (charge levels 1-3); on release the hero chops once and a
flurry of cuts is let loose in front (flurry.py). Numbers in one place.
"""

WORLD_SCALE = 0.10        # the world's speed at full warp
HERO_SCALE = 1.30         # the hero's speed at full warp (moves and swings faster)
ENTER_TIME = 0.15         # seconds to slide into the warp
EXIT_TIME = 0.10          # seconds to slide back out
LEVEL_TIMES = (0.3, 0.8, 1.4)   # real seconds held to reach charge level 1, 2, 3


class TimeWarp:
    def __init__(self):
        self.held = False
        self.blend = 0.0          # 0 normal time ... 1 full warp
        self.charge = 0.0         # real seconds held

    def start(self):
        self.held = True
        self.charge = 0.0

    @property
    def reached(self):
        """Charge levels reached so far (0 before the first)."""
        return sum(self.charge >= t for t in LEVEL_TIMES)

    @property
    def level(self):
        """The flurry's level on release: at least 1, even for a quick tap."""
        return max(1, self.reached)

    def update(self, frame_time):
        """frame_time in real seconds. Returns True when a charge level was just reached."""
        before = self.reached
        if self.held:
            self.charge += frame_time
            self.blend = min(1.0, self.blend + frame_time / ENTER_TIME)
        else:
            self.blend = max(0.0, self.blend - frame_time / EXIT_TIME)
        return self.held and self.reached > before

    @property
    def active(self):
        return self.blend > 0

    @property
    def world_scale(self):
        return 1 + (WORLD_SCALE - 1) * self.blend

    @property
    def hero_scale(self):
        return 1 + (HERO_SCALE - 1) * self.blend
