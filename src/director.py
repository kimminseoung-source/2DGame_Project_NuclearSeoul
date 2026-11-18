"""The AI director (2026-11-18, after Left 4 Dead's: "넣어 보세요"): it decides when infected come in,
so a play has a rhythm - tension builds, peaks, then lets go - instead of one every 6-9 s.

- intensity (0..1): how hard things are for the hero right now. It rises when he is hit and while
  infected that have spotted him are close, and when one of the station's people falls; it drains
  slowly when nothing is on him.
- Out in the area: BUILD (arrivals at the normal pace) until intensity reaches PEAK_AT -> PEAK (a
  few more, quickly, for a moment) -> RELAX (nobody new comes until intensity has dropped and a
  while has passed) -> BUILD again. A loud noise that reaches an entrance still calls one in, even
  while relaxing: the hero chose to make it.
- At the station (the defense) the rhythm follows the clock to the train: build, a lull to breathe,
  a harder push, then the final horde when the train is heard (DEFENSE_PHASES).
- Adaptive: while the hero is badly hurt the arrivals come slower (L4D sends fewer when players
  struggle).

All the numbers are in OUTSIDE and DEFENSE_PHASES; play.py only asks `update()` whether to bring
one in now. F7 shows intensity, the state and the next arrival.
"""

import random

# state: (seconds between arrivals or None = nobody new, at most this many up at once)
OUTSIDE = {"build": ((6.0, 9.0), 6), "peak": ((2.5, 3.5), 8), "relax": (None, 6)}
PEAK_AT = 0.7               # intensity that turns a build-up into a peak (three blows)
PEAK_HOLD = 5.0             # s a peak lasts
RELAX_MIN = 12.0            # s a relax lasts at least...
RELAX_UNTIL = 0.3           # ...and until intensity is this low

# the defense, by seconds left to the train: (from, state, every, most alive, message on entering)
DEFENSE_PHASES = (
    (60, "build", (3.5, 5.0), 6, None),
    (40, "relax", None, 6, "잠잠해졌다 · 숨을 돌릴 때"),
    (32, "build", (2.2, 3.2), 8, "다시 몰려온다"),
    (15, "peak", (0.9, 1.3), 12, "기차 소리가 들린다! 마지막 15초"),
)

HIT_RISE = 0.25             # intensity a blow on the hero adds
FALL_RISE = 0.2             # ...one of the people falling
CLOSE_RISE = 0.06           # per second for each close infected that has spotted him
CLOSE = 170                 # px
DRAIN = 0.05                # per second when nothing is on him
HURT_SLOW = 1.5             # arrivals this much slower while the hero is under HURT_HP
HURT_HP = 35.0


class Director:
    def __init__(self):
        self.intensity = 0.0
        self.state = "build"
        self.time_in_state = 0.0
        self.spawn_in = random.uniform(*OUTSIDE["build"][0])
        self.most = OUTSIDE["build"][1]
        self.history = []            # (intensity, state) every 0.25 s for the F7 graph
        self._sample = 0.0

    # ------------------------------------------------------------------ inputs
    def hero_hit(self):
        self.intensity = min(1.0, self.intensity + HIT_RISE)

    def person_fell(self):
        self.intensity = min(1.0, self.intensity + FALL_RISE)

    def noise_calls(self, soon):
        """A loud noise reached an entrance: the next one comes within `soon` s."""
        self.spawn_in = min(self.spawn_in, soon)

    # ------------------------------------------------------------------ the rhythm
    def set_state(self, state, every, most):
        if state != self.state:
            self.state, self.time_in_state = state, 0.0
            if every is not None:
                self.spawn_in = min(self.spawn_in, random.uniform(*every))
        self.most = most

    def update(self, dt, game):
        """Advance; True when one infected should come in now."""
        hero = game.hero
        close = sum(1 for z in game.zombies if z.alive and z.state in ("chase", "poised", "windup", "strike")
                    and (z.x - hero.x) ** 2 + (z.y - hero.y) ** 2 <= CLOSE ** 2)
        if close:
            self.intensity = min(1.0, self.intensity + CLOSE_RISE * close * dt)
        else:
            self.intensity = max(0.0, self.intensity - DRAIN * dt)
        self.time_in_state += dt
        self._sample += dt
        if self._sample >= 0.25:
            self._sample = 0.0
            self.history = (self.history + [(self.intensity, self.state)])[-240:]   # the last minute

        if game.defense is not None:
            every, message = self.defense_phase(game.defense)
            if message:
                game.message = message
        else:
            every = self.outside_phase()
        self.spawn_in -= dt
        if self.spawn_in > 0:
            return False
        if every is None and not game.pulled_entrances():
            return False                               # relaxing: only a noise the hero made calls one
        pace = HURT_SLOW if hero.hp < HURT_HP else 1.0
        self.spawn_in = random.uniform(*(every or OUTSIDE["build"][0])) * pace
        return sum(z.alive for z in game.zombies) < self.most

    def outside_phase(self):
        if self.state == "build" and self.intensity >= PEAK_AT:
            self.set_state("peak", *OUTSIDE["peak"])
        elif self.state == "peak" and self.time_in_state >= PEAK_HOLD:
            self.set_state("relax", *OUTSIDE["relax"])
        elif self.state == "relax" and self.time_in_state >= RELAX_MIN and self.intensity <= RELAX_UNTIL:
            self.set_state("build", *OUTSIDE["build"])
        return OUTSIDE[self.state][0]

    def defense_phase(self, left):
        """The phase for `left` seconds to the train; (every, message if just entered)."""
        phase = next(p for p in reversed(DEFENSE_PHASES) if left <= p[0]) if left <= DEFENSE_PHASES[0][0] \
            else DEFENSE_PHASES[0]
        _, state, every, most, message = phase
        entered = (state, every) != (self.state, getattr(self, "_every", None))
        self._every = every
        self.set_state(state, every, most)
        if entered:
            self.time_in_state = 0.0
        return every, message if entered else None
