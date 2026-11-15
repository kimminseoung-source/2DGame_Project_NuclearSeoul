"""The hero's condition (Zomboid-style "moodles", 2026-11-15 "1번 ㄱ"):

- tension: rises while infected that have spotted the hero are close, falls when they are gone;
  at panic the blade is slower to come back after a slash and the hero's view narrows
- injuries from blows: a scratch, a laceration (bleeds) or a bite (bleeds, and will matter for
  exposure later). Each blow takes health by its kind (percent); a bleeding wound keeps draining
  health every second until a bandage stops it.
- `moodles()` lists what the HUD shows as status icons (also slowed and sneaking).
"""

import random

TENSION_RISE = 0.22          # per second for each close infected that has spotted the hero
TENSION_FALL = 0.12          # per second when none are close
TENSION_NEAR = 170           # px
TENSE, PANIC = 0.33, 0.66    # tension levels
PANIC_RECOVER = 1.5          # slash cooldown multiplier while panicking
INJURIES = (("scratch", "긁힘", 0.6, 12, 0.0), ("laceration", "찢어짐", 0.3, 22, 1.2), ("bite", "물림", 0.1, 35, 2.0))
# (kind, name, chance, health % the blow takes, health % lost per second while it bleeds)
BANDAGE_HEAL = 15.0          # health % a bandage gives back


class Condition:
    def __init__(self):
        self.tension = 0.0
        self.injuries = []           # dicts: kind, name, bleed (health % per second, 0 = not bleeding)

    # ------------------------------------------------------------------ tension
    def update(self, dt, hero, zombies):
        """Returns the health % lost to bleeding this frame."""
        close = sum(1 for z in zombies if z.alive and z.state in ("chase", "poised", "windup", "strike")
                    and (z.x - hero.x) ** 2 + (z.y - hero.y) ** 2 <= TENSION_NEAR ** 2)
        if close:
            self.tension = min(1.0, self.tension + TENSION_RISE * close * dt)
        else:
            self.tension = max(0.0, self.tension - TENSION_FALL * dt)
        return sum(w["bleed"] for w in self.injuries) * dt

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
        """A blow lands: returns (wound name, health % it takes)."""
        roll, total = random.random(), 0.0
        for kind, name, chance, damage, bleed in INJURIES:
            total += chance
            if roll <= total:
                self.injuries.append({"kind": kind, "name": name, "bleed": bleed})
                return name, damage
        return INJURIES[0][1], INJURIES[0][3]

    @property
    def bleeding(self):
        return any(w["bleed"] > 0 for w in self.injuries)

    def treat(self):
        """A bandage on the worst wound: stops its bleeding (a bite first, then a laceration)."""
        order = {"bite": 0, "laceration": 1, "scratch": 2}
        for wound in sorted(self.injuries, key=lambda w: (w["bleed"] <= 0, order[w["kind"]])):
            if wound["bleed"] > 0 or wound["kind"] == "scratch":
                wound["bleed"] = 0.0
                if wound["kind"] == "scratch":
                    self.injuries.remove(wound)              # a scratch, once dressed, is gone
                else:
                    wound["dressed"] = True
                return wound["name"]
        return None

    # ------------------------------------------------------------------ HUD
    def moodles(self, hero):
        """(label, colour, level 1-3) for each status icon to show."""
        out = []
        if self.tension >= PANIC:
            out.append(("공황", (200, 70, 60), 3))
        elif self.tension >= TENSE:
            out.append(("긴장", (210, 160, 70), 2))
        if self.bleeding:
            out.append(("출혈", (190, 40, 40), 3))
        for kind, label in (("bite", "물림"), ("laceration", "찢김"), ("scratch", "긁힘")):
            n = sum(1 for w in self.injuries if w["kind"] == kind)
            if n:
                out.append((label if n == 1 else f"{label}{n}", (170, 110, 100), 1))
        if hero.slowed > 0.05:
            out.append(("느림", (130, 150, 190), 1))
        if hero.sneaking:
            out.append(("은신", (110, 150, 120), 1))
        return out
