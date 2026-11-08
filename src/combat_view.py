"""Game-world objects that put a running fight on screen.

The Combat class holds the rules; these objects give it update()/draw() on the
right layers: the board under the units, the overlay above them, the top strip
and the hotbar.
"""

import game_clock


class CombatBoard:
    """Board layer: runs the fight each frame and draws movement area, rings and paths."""

    def __init__(self, combat):
        self.combat = combat

    def update(self):
        self.combat.update(game_clock.step())

    def draw(self):
        self.combat.draw()


class CombatOverlay:
    def __init__(self, combat):
        self.combat = combat

    def update(self):
        pass

    def draw(self):
        self.combat.draw_overlay()


class CombatHud:
    def __init__(self, combat):
        self.combat = combat

    def update(self):
        pass

    def draw(self):
        self.combat.draw_hud()


class CombatBottom:
    def __init__(self, combat):
        self.combat = combat

    def update(self):
        pass

    def draw(self):
        self.combat.draw_bottom()
