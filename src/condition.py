"""The hero's condition (Zomboid-style "moodles", 2026-11-15 "1번 ㄱ"):

- tension: rises while infected that have spotted the hero are close, falls when they are gone;
  at panic the blade is slower to come back after a slash and the hero's view narrows
- one kind of wound, bleeding (2026-11-18 "출혈만 하나로 정리하죠", was scratch/laceration/bite):
  every blow takes BLOW_DAMAGE % health and BLEED_CHANCE of blows start bleeding, which drains
  BLEED_RATE % a second until a bandage stops it. More bleeding blows do not stack.
- `moodles()` lists what the HUD shows as status icons: bleeding, slowed, sneaking.
  Tension and panic are not shown (2026-11-16 "왜 표시하는지 모르겠음"); they are felt instead.
"""

import random

TENSION_RISE = 0.22          # per second for each close infected that has spotted the hero
TENSION_FALL = 0.12          # per second when none are close
TENSION_NEAR = 170           # px
PANIC = 0.66                 # tension level where panic starts
PANIC_RECOVER = 1.5          # slash cooldown multiplier while panicking
BLOW_DAMAGE = 17            # health % every blow takes (the old three kinds averaged ~17)
BLEED_CHANCE = 0.4          # chance a blow starts bleeding (the old laceration + bite: 30% + 10%)
BLEED_RATE = 1.5            # health % lost per second while bleeding
BANDAGE_HEAL = 15.0          # health % a bandage gives back


class Condition:
    def __init__(self):
        self.tension = 0.0
        self.bleeding = False
        self.blows = 0               # blows taken: marks on the bag's body outline
        self.dressed = False         # a bandage is on (the body column says so)

    # ------------------------------------------------------------------ tension
    def update(self, dt, hero, zombies):
        """Returns the health % lost to bleeding this frame."""
        close = sum(1 for z in zombies if z.alive and z.state in ("chase", "poised", "windup", "strike")
                    and (z.x - hero.x) ** 2 + (z.y - hero.y) ** 2 <= TENSION_NEAR ** 2)
        if close:
            self.tension = min(1.0, self.tension + TENSION_RISE * close * dt)
        else:
            self.tension = max(0.0, self.tension - TENSION_FALL * dt)
        return BLEED_RATE * dt if self.bleeding else 0.0

    @property
    def panic(self):
        return self.tension >= PANIC

    def view_scale(self):
        """Panic narrows what the hero takes in (Zomboid: panic cuts vision): 1.0 calm, 0.7 at worst."""
        if self.tension <= PANIC:
            return 1.0
        return 1.0 - 0.3 * (self.tension - PANIC) / (1 - PANIC)

    # ------------------------------------------------------------------ wounds
    def wound(self):
        """A blow lands: returns (bleeds, health % it takes)."""
        self.blows += 1
        if random.random() < BLEED_CHANCE:
            self.bleeding, self.dressed = True, False
        return self.bleeding, BLOW_DAMAGE

    def treat(self):
        """A bandage: stops the bleeding. True if there was bleeding to stop."""
        if not self.bleeding:
            return False
        self.bleeding, self.dressed = False, True
        return True

    # ------------------------------------------------------------------ HUD
    def moodles(self, hero):
        """(label, colour, level 1-3) for each status icon to show."""
        out = []                     # tension/panic is felt (narrow view, slow blade), not shown
        if self.bleeding:
            out.append(("출혈", (190, 40, 40), 3))
        if hero.slowed > 0.05:
            out.append(("느림", (130, 150, 190), 1))
        if hero.sneaking:
            out.append(("은신", (110, 150, 120), 1))
        return out
