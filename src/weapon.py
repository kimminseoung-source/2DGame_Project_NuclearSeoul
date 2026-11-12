"""Weapons as data and one real-time melee attack for every weapon and unit.

A weapon is a list of swings (its combo). Each swing says which sheet it plays, how long it
lasts, when the blow lands (contact), how much it hurts, how far it reaches and how hard it
pushes. MeleeAttack runs any swing: timing, hit test, trail. Adding a weapon (fire axe,
steel pipe ...) means adding data here, not new attack code (generic systems rule).
"""

from collections import namedtuple
from math import atan2, cos, hypot, pi, sin

import pico2d

import dodge

Swing = namedtuple("Swing", "sheet duration contact damage reach depth arc push recover_from heavy step",
                   defaults=(0,))
# sheet: animation sheet (character_look pose); duration and contact in seconds;
# damage in hit points; reach and depth in px; arc in radians around the facing direction;
# push: knockback speed in px/s; recover_from: progress where the swing's own recovery
# starts, so a follow-up swing can cut in there instead of waiting for it; heavy: a big blow
# (combo finisher) that lands one feel class harder (hit-stop, shake, number; see hit_feel);
# step: px the attacker steps forward into the blow (the art's lunge is pinned in place).

Weapon = namedtuple("Weapon", "name swings combo_window sneak_multiplier")
# combo_window: seconds after a swing's recovery starts in which a click continues the combo.

MACHETE = Weapon(
    name="마체테",
    swings=(
        # 1st and 2nd: quick, light blows; 3rd: the big chop with a real wind-up.
        Swing("swing", 0.46, 0.14, 2, 42, 20, pi / 3, 110, 0.72, False),    # quick sweep
        Swing("swing2", 0.50, 0.16, 2, 46, 22, pi / 3, 110, 0.73, False),   # rising cut
        Swing("swing3", 0.70, 0.32, 6, 50, 24, pi / 3, 340, 0.74, True, 22),  # big chop down
    ),
    combo_window=0.25,
    sneak_multiplier=3,
)

IMPACT_TIME = 0.18
TRAIL_TIME = 0.12      # seconds the white trail stays after the blow lands
TRAIL_STEPS = 10
# Fallback for looks without blade data: a right-facing arc of the blade's trail.
TRAIL = ((24, 30), (34, 24), (38, 14), (34, 4))


class MeleeAttack:
    """One swing in progress. update() returns True on the frame the blow lands."""

    def __init__(self, swing, direction, combo_index=0):
        self.swing = swing
        self.dx, self.dy = direction
        self.combo_index = combo_index
        self.elapsed = 0.0
        self.sneak = False          # started before the target noticed: a sneak attack
        # px the attacker travels just before the blow: the swing's own step, plus a counter's
        # lunge (start_lunge); lunge_from marks a counter, for its after-images.
        self.lunge = (self.dx * swing.step, 0.0)
        self.lunge_from = None

    def update(self, frame_time):
        before = self.elapsed
        self.elapsed += frame_time
        return before < self.swing.contact <= self.elapsed

    @property
    def lunge_time(self):
        return min(self.swing.contact, dodge.LUNGE_TIME)

    def start_lunge(self, attacker, distance):
        self.lunge = (self.lunge[0] + distance[0], self.lunge[1] + distance[1])
        self.lunge_from = (attacker.x, attacker.y)

    def lunge_step(self, frame_time):
        """Movement for this frame of the lunge: an even share of it over the lunge_time
        that ends at contact, so the body arrives as the blow lands.
        Call before update(), which advances elapsed."""
        if self.lunge == (0.0, 0.0):
            return 0.0, 0.0
        begin = self.swing.contact - self.lunge_time
        start = min(max(self.elapsed, begin), self.swing.contact)
        end = min(max(self.elapsed + frame_time, begin), self.swing.contact)
        share = (end - start) / self.lunge_time
        return self.lunge[0] * share, self.lunge[1] * share

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
        """A white trail right after contact that follows the blade in the frames on screen:
        the stroke into the impact frame, then the follow-through once the next frame shows
        (any weapon, any look with blade data). It fades out over TRAIL_TIME."""
        after = self.elapsed - self.swing.contact
        if not 0 <= after < TRAIL_TIME:
            return
        fade = 1 - after / TRAIL_TIME
        x, feet_y = attacker.pose_anchor()
        look, sheet = attacker.look, self.swing.sheet
        lines = look.blade_lines(sheet, x, feet_y, attacker.direction) if hasattr(look, "blade_lines") else None
        impact = look.impact_of(sheet) if lines else None
        if impact is None or not lines[impact]:
            self.draw_arc_trail(x, feet_y + 12, fade)
            return
        shown = look.frame_of(sheet, self.progress, self.contact)
        moved_on = shown > impact
        # While the impact frame shows, the whole blow (from trail_from frames before it);
        # once the sprite moves on, a cut's arc stays only as a fading after-image and a
        # thrust's streak (tied to the blade) goes.
        first = max(0, impact - look.trail_from(sheet))
        for index in range(first, impact):
            before = lines[index] or lines[impact]
            last = index == impact - 1
            draw_stroke(before, lines[index + 1] or lines[impact], fade * (0.45 if moved_on else 1),
                        MAX_BLOW_TURN, streak=last and not moved_on, facing=attacker.direction)
        if moved_on and impact + 1 < len(lines) and lines[impact + 1]:
            draw_stroke(lines[impact], lines[impact + 1], fade, MAX_FOLLOW_TURN)

    def draw_arc_trail(self, x, y, fade):
        for (x1, y1), (x2, y2) in zip(TRAIL, TRAIL[1:]):
            shade = round(150 + 100 * fade)
            pico2d.draw_line(x + self.dx * x1, y + y1, x + self.dx * x2, y + y2, shade, shade, shade)


# Radians a blade may turn between two frames and still read as a cut. A blow's arc goes the
# way round that passes in front of the body (a cut always crosses the front); it may turn
# up to MAX_BLOW_TURN (a rising cut from behind turns ~185 degrees). A wide turn whose middle
# is not in front (the blade flips over the head, as in a thrust) gets a straight streak.
MAX_BLOW_TURN = 3.5
WIDE_TURN = 2.7
MIN_FRONT = 0.3              # cos of the arc's middle angle along the facing for a wide cut
MAX_FOLLOW_TURN = 1.9
RINGS = ((1.0, 255), (0.93, 235), (0.86, 205), (0.75, 150), (0.62, 90))   # radius, alpha


def draw_stroke(before, at, fade, max_turn, streak=False, facing=0):
    """Trail of a blade moving from `before` to `at` ((grip, tip) screen pairs): a crescent
    when it turns at most max_turn, otherwise a straight streak behind the tip if streak is
    set, or nothing. With facing (+1 / -1, for the blow itself) the arc takes the way round
    that passes in front of the body, and a wide turn that is not in front is a thrust."""
    (g0, t0), (g1, t1) = before, at
    a0 = atan2(t0[1] - g0[1], t0[0] - g0[0])
    a1 = atan2(t1[1] - g1[1], t1[0] - g1[0])
    turn = (a1 - a0 + pi) % (2 * pi) - pi          # the short way round
    front = 1.0
    if facing:
        other = turn - 2 * pi if turn > 0 else turn + 2 * pi
        turn = max((turn, other), key=lambda t: cos(a0 + t / 2) * facing)
        front = cos(a0 + turn / 2) * facing
    if abs(turn) <= max_turn and (abs(turn) <= WIDE_TURN or front >= MIN_FRONT):
        draw_sweep(before, at, a0, turn, fade)
    elif streak:
        draw_streak(at, fade)


def draw_sweep(before, at, a0, turn, fade):
    """A crescent swept by the blade turning about its moving grip; fade eats it from the tail."""
    (g0, t0), (g1, t1) = before, at
    l0, l1 = hypot(t0[0] - g0[0], t0[1] - g0[1]), hypot(t1[0] - g1[0], t1[1] - g1[1])
    start = round((1 - fade) * TRAIL_STEPS)
    previous = None
    for step in range(start, TRAIL_STEPS + 1):
        t = step / TRAIL_STEPS
        gx, gy = g0[0] + (g1[0] - g0[0]) * t, g0[1] + (g1[1] - g0[1]) * t
        angle, length = a0 + turn * t, l0 + (l1 - l0) * t
        points = [(gx + cos(angle) * length * r, gy + sin(angle) * length * r) for r, _ in RINGS]
        if previous:
            tail = (step - start) / max(1, TRAIL_STEPS - start)    # the newest part is brightest
            for (p, q), (_, alpha) in zip(zip(previous, points), RINGS):
                pico2d.draw_line(*p, *q, 255, 255, 255, round(alpha * fade * (0.35 + 0.65 * tail)))
        previous = points


def draw_streak(at, fade):
    """Speed lines running back from the tip along the blade, for a thrust."""
    (gx, gy), (tx, ty) = at
    length = hypot(tx - gx, ty - gy) or 1
    ux, uy = (tx - gx) / length, (ty - gy) / length
    reach = length * (0.6 + 1.0 * fade)
    for side, alpha in ((0, 255), (-1.5, 170), (1.5, 170), (-3, 90), (3, 90)):
        sx, sy = tx - uy * side, ty + ux * side
        back = reach * (1 - abs(side) * 0.15)
        pico2d.draw_line(sx, sy, sx - ux * back, sy - uy * back, 255, 255, 255, round(alpha * fade))


def draw_impact(x, y, time_left, scale=1.0):
    """The star burst where a blow lands; scale grows with the blow's weight (hit_feel)."""
    progress = 1 - time_left / IMPACT_TIME
    inner = (0.18 + progress * 0.65) * scale
    outer = inner + (1 - progress) * 0.52 * scale
    for dx, dy in ((-25, 8), (-15, 21), (4, 25), (22, 15), (26, -4), (12, -13)):
        for width in range(max(1, round(scale))):          # heavier blows draw thicker rays
            pico2d.draw_line(x + dx * inner + width, y + dy * inner, x + dx * outer + width,
                             y + dy * outer, 255, 214, 127)
    if progress < 0.3:
        pico2d.draw_circle(x, y, round(4 * scale), 255, 237, 191, filled=True)
    if scale > 1.2 and progress < 0.7:                      # a shock ring on heavy blows
        pico2d.draw_circle(x, y, round(10 + 26 * progress * scale), 255, 230, 180,
                           round(200 * (1 - progress / 0.7)))
