"""Radiation exposure (피폭 수치): the price of the hero's mutation, shared rules.

People who pass the limit die and turn into the infected (PRD 12). The hero is exposed
but not yet turned: pushing the body (the time warp, time_warp.py) raises exposure, which
makes the flurry (flurry.py) hit harder but blurs the eyes, then drains health; at the limit the
body gives out. Rules live here once so any unit with an Exposure (a companion, a
hostile survivor) works the same way (generic systems rule).
"""

MAX = 100.0
WARP_RISE = 15.0          # per second while the time warp is held
DECAY = 2.0               # per second once it has rested
DECAY_DELAY = 1.5         # seconds after the last rise before it starts falling
LIMIT_DAMAGE = 4          # health lost when the gauge hits the limit
LIMIT_RESET = 70.0        # the gauge drops back here after the limit
DRAIN_EVERY = 2.0         # seconds per point of health lost in the last stage

# Stages: (from value, name, power multiplier for the flurry's cuts).
STAGES = (
    (0.0, "안정", 1.0),
    (30.0, "시야 좁아짐", 1.3),
    (60.0, "시야 흐려짐", 1.6),
    (90.0, "몸이 무너짐", 2.0),
)


def stage_of(value):
    return max(index for index, (start, _, _) in enumerate(STAGES) if value >= start)


class Exposure:
    """One body's exposure. update() returns events: "limit" when it hits MAX,
    "drain" for each point of health the last stage takes."""

    def __init__(self):
        self.value = 0.0
        self.rest = 0.0          # seconds since the last rise
        self.drain = 0.0

    @property
    def ratio(self):
        return self.value / MAX

    @property
    def stage(self):
        return stage_of(self.value)

    @property
    def power(self):
        return STAGES[self.stage][2]

    @property
    def stage_name(self):
        return STAGES[self.stage][1]

    def raise_by(self, amount):
        self.value = min(MAX, self.value + amount)
        self.rest = 0.0

    def update(self, frame_time, rising):
        """frame_time in real seconds; rising: the warp is held this frame."""
        events = []
        if rising:
            self.raise_by(WARP_RISE * frame_time)
        else:
            self.rest += frame_time
            if self.rest >= DECAY_DELAY:
                self.value = max(0.0, self.value - DECAY * frame_time)
        if self.value >= MAX:
            self.value = LIMIT_RESET
            self.rest = 0.0
            events.append("limit")
        if self.stage == len(STAGES) - 1:
            self.drain += frame_time
            while self.drain >= DRAIN_EVERY:
                self.drain -= DRAIN_EVERY
                events.append("drain")
        else:
            self.drain = 0.0
        return events
