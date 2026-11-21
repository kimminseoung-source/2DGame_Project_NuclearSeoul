"""Stamina (2026-11-16 "기력을 넣자"; Project Zomboid's endurance): every swing, shove and roll
costs breath, a swing that cuts only air costs more, and breath comes back once the hero stops
spending it for a moment.

An action started without enough breath still happens, but tired: a slash is slower, a shove
cannot knock anything down, and there is no roll at all - so mashing the button wears the hero
out and every blow becomes a choice. The rules are numbers here so any unit can carry a Stamina.
"""

from settings import STAMINA_ON

MAX = 100.0
COST = {"slash": 14.0, "stomp": 10.0, "shove": 12.0, "roll": 20.0}
MISS = 8.0                 # extra for a slash that hits nothing
REGEN = 30.0               # per second, standing
REGEN_MOVING = 0.6         # share of it while moving
DELAY = 0.6                # s after spending before breath comes back
TIRED_SLOW = 1.5           # a tired slash takes this many times as long
WINDED = 30.0              # below this the hero is out of breath (shown, breathing)


class Stamina:
    def __init__(self):
        self.value = MAX
        self.rest_in = 0.0          # s until it starts coming back
        self.tired_flash = 0.0      # s left of showing "out of breath" after a tired action

    def spend(self, action):
        """Pay for `action`; False (and empty) when there was not enough: the action is tired."""
        return self.pay(COST[action])

    def pay(self, cost):
        if not STAMINA_ON:                     # off (2026-11-21): nothing costs breath
            return True
        self.rest_in = DELAY
        if self.value >= cost:
            self.value -= cost
            return True
        self.value = 0.0
        self.tired_flash = 0.6
        return False

    def can(self, action):
        return not STAMINA_ON or self.value >= COST[action]

    @property
    def winded(self):
        return self.value < WINDED

    def update(self, dt, moving):
        self.tired_flash = max(0.0, self.tired_flash - dt)
        if self.rest_in > 0:
            self.rest_in -= dt
            return
        self.value = min(MAX, self.value + REGEN * (REGEN_MOVING if moving else 1.0) * dt)


# Roll charges (2026-11-21, instead of breath for the roll): a few rolls stored, one coming back at a
# time. Numbers are read live (F4 changes them). Any unit can carry Charges.
ROLL_CHARGES = 2
ROLL_RECHARGE = 1.5         # s for one roll to come back (2026-11-21 played: "1.5초 정도가 좋을 듯"; was 1.2)
POP_TIME = 0.25             # s a refilled dot shows bigger and brighter
EMPTY_FLASH = 0.5           # s the dots flash red after Space with none left


class Charges:
    def __init__(self):
        self.left = ROLL_CHARGES
        self.timer = 0.0            # s into the next one coming back
        self.pop = 0.0              # s left of the "just came back" flash
        self.empty = 0.0            # s left of the "none left" flash

    @property
    def full(self):
        return self.left >= ROLL_CHARGES

    @property
    def coming(self):
        """0..1: how far the next roll is from coming back."""
        return 0.0 if self.full else min(1.0, self.timer / ROLL_RECHARGE)

    def use(self):
        if self.left >= 1:
            self.left -= 1
            return True
        self.empty = EMPTY_FLASH
        return False

    def update(self, dt):
        self.pop = max(0.0, self.pop - dt)
        self.empty = max(0.0, self.empty - dt)
        self.left = min(self.left, ROLL_CHARGES)
        if self.full:
            self.timer = 0.0
            return
        self.timer += dt
        if self.timer >= ROLL_RECHARGE:
            self.timer = 0.0
            self.left += 1
            self.pop = POP_TIME
