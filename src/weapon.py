"""Weapons as data and one real-time melee attack for every weapon and unit.

A weapon is a list of swings (its combo). Each swing says which sheet it plays, how long it
lasts, when the blow lands (contact), how much it hurts, how far it reaches and how hard it
pushes. MeleeAttack runs any swing: timing, hit test, trail. Adding a weapon (fire axe,
steel pipe ...) means adding data here, not new attack code (generic systems rule).
"""

from collections import namedtuple
from math import cos, hypot, pi

import pico2d

Swing = namedtuple("Swing", "sheet duration contact damage reach depth arc push recover_from")
# sheet: animation sheet (character_look pose); duration and contact in seconds;
# damage in hit points; reach and depth in px; arc in radians around the facing direction;
# push: knockback speed in px/s; recover_from: progress where the swing's own recovery
# starts, so a follow-up swing can cut in there instead of waiting for it.

Weapon = namedtuple("Weapon", "name swings combo_window sneak_multiplier")
# combo_window: seconds after a swing's recovery starts in which a click continues the combo.

MACHETE = Weapon(
    name="마체테",
    swings=(
        Swing("swing", 0.50, 0.24, 3, 42, 20, pi / 3, 150, 0.62),     # rising cut
        Swing("swing2", 0.48, 0.20, 3, 44, 20, pi / 3, 150, 0.62),    # backhand sweep
        Swing("swing3", 0.62, 0.22, 5, 48, 22, pi / 3, 260, 0.75),    # lunging finisher
    ),
    combo_window=0.25,
    sneak_multiplier=3,
)

IMPACT_TIME = 0.18
TRAIL = ((24, 30), (34, 24), (38, 14), (34, 4))   # right-facing arc of the blade's trail


class MeleeAttack:
    """One swing in progress. update() returns True on the frame the blow lands."""

    def __init__(self, swing, direction, combo_index=0):
        self.swing = swing
        self.dx, self.dy = direction
        self.combo_index = combo_index
        self.elapsed = 0.0
        self.sneak = False          # started before the target noticed: a sneak attack

    def update(self, frame_time):
        before = self.elapsed
        self.elapsed += frame_time
        return before < self.swing.contact <= self.elapsed

    @property
    def contact(self):
        return self.swing.contact / self.swing.duration

    @property
    def progress(self):
        return min(1.0, self.elapsed / self.swing.duration)

    @property
    def done(self):
        return self.elapsed >= self.swing.duration

    @property
    def recovering(self):
        return self.progress >= self.swing.recover_from

    def hits(self, attacker, target):
        """Is target (x, y) inside this swing's reach and arc, with nothing solid between?"""
        dx, dy = target[0] - attacker.x, target[1] - attacker.y
        distance = hypot(dx, dy)
        if distance > self.swing.reach or abs(dy) > self.swing.depth:
            return False
        if distance and (dx * self.dx + dy * self.dy) / hypot(self.dx, self.dy) < distance * cos(self.swing.arc):
            return False
        steps = max(1, int(distance / 4) + 1)
        return all(
            attacker.tile_map.can_stand(attacker.x + dx * step / steps, attacker.y + dy * step / steps, 0)
            for step in range(1, steps + 1)
        )

    def draw_trail(self, attacker, camera_x):
        """A short light arc right after contact."""
        after = self.elapsed - self.swing.contact
        if not 0 <= after < 0.1:
            return
        fade = 1 - after / 0.1
        x, y = attacker.x - camera_x, attacker.y
        for (x1, y1), (x2, y2) in zip(TRAIL, TRAIL[1:]):
            shade = round(150 + 100 * fade)
            pico2d.draw_line(x + self.dx * x1, y + y1, x + self.dx * x2, y + y2, shade, shade, shade)


def draw_impact(x, y, time_left):
    """The star burst where a blow lands."""
    progress = 1 - time_left / IMPACT_TIME
    inner = 0.18 + progress * 0.65
    outer = inner + (1 - progress) * 0.52
    for dx, dy in ((-25, 8), (-15, 21), (4, 25), (22, 15), (26, -4), (12, -13)):
        pico2d.draw_line(x + dx * inner, y + dy * inner, x + dx * outer, y + dy * outer, 255, 214, 127)
    if progress < 0.3:
        pico2d.draw_circle(x, y, 4, 255, 237, 191, filled=True)
