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

Swing = namedtuple("Swing", "sheet duration contact damage reach depth arc push recover_from heavy step trail",
                   defaults=(0, "blade"))
# sheet: animation sheet (character_look pose); duration and contact in seconds;
# damage in hit points; reach and depth in px; arc in radians around the facing direction;
# push: knockback speed in px/s; recover_from: progress where the swing's own recovery
# starts, so a follow-up swing can cut in there instead of waiting for it; heavy: a big blow
# (combo finisher) that lands one feel class harder (hit-stop, shake, number; see hit_feel);
# step: px the attacker steps forward into the blow (the art's lunge is pinned in place);
# trail: "blade" follows the blade in the sheets, "crescent" draws a big half moon around
# the attacker in the attack's direction (the aimed slash).

Weapon = namedtuple("Weapon", "name swings combo_window sneak_multiplier finisher", defaults=(None,))
# combo_window: seconds after a swing's recovery starts in which a click continues the combo;
# finisher: the blow the time-warp release swings (it looses the flurry, flurry.py);
# None means the combo's last swing.

MACHETE = Weapon(
    name="마체테",
    swings=(
        # PRD v4.0: one slash toward the mouse - a short lunge, a big crescent, and an
        # infected falls to one blow. Click again once it recovers to slash again.
        Swing("swing", 0.32, 0.07, 10, 52, 40, pi / 2.2, 260, 0.55, False, 38, "crescent"),
    ),
    combo_window=0.25,
    sneak_multiplier=3,
    # The time-warp release's blow (until stage 2 makes the warp a plain slow-down).
    finisher=Swing("swing3", 0.68, 0.28, 6, 50, 24, pi / 3, 340, 0.74, True),
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
        length = hypot(*direction) or 1
        self.dx, self.dy = direction[0] / length, direction[1] / length   # unit vector
        self.combo_index = combo_index
        self.elapsed = 0.0
        self.sneak = False          # started before the target noticed: a sneak attack
        # px the attacker travels just before the blow: the swing's own step, plus a counter's
        # lunge (start_lunge); lunge_from marks a counter, for its after-images.
        self.lunge = (self.dx * swing.step, self.dy * swing.step)
        self.lunge_from = None
        self.flurry = False          # the time-warp finisher: its blow looses a flurry (flurry.py)

    def update(self, frame_time):
        before = self.elapsed
        self.elapsed += frame_time
        return before < self.swing.contact <= self.elapsed

    STOP_SHARE = 0.5          # a lunge stops this share of the reach in front of an enemy

    def trim_lunge(self, attacker, targets):
        """Shorten the swing's own step so it stops just in front of the first enemy in its
        path instead of running through it (any attacker, any targets)."""
        length = hypot(*self.lunge)
        if not length:
            return
        for target in targets:
            along = (target.x - attacker.x) * self.dx + (target.y - attacker.y) * self.dy
            across = abs((target.x - attacker.x) * self.dy - (target.y - attacker.y) * self.dx)
            if along > 0 and across <= self.swing.depth:
                length = min(length, max(0.0, along - self.swing.reach * self.STOP_SHARE))
        self.lunge = (self.dx * length, self.dy * length)

    @property
    def lunge_time(self):
        return min(self.swing.contact, dodge.LUNGE_TIME)

    def start_lunge(self, attacker, distance):
        """A counter's lunge: it replaces the swing's own step (it already stops in reach)."""
        self.lunge = distance
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
        x, feet_y = attacker.pose_anchor()
        if self.swing.trail == "crescent":
            # The half moon sweeps in just before contact, so it is whole when the blow
            # lands (and stays whole through the hit-stop).
            after = self.elapsed - self.swing.contact + CRESCENT_GROW
            if 0 <= after < TRAIL_TIME + CRESCENT_GROW:
                fade = min(1.0, 1 - (after - CRESCENT_GROW) / TRAIL_TIME)
                draw_crescent(x, feet_y + 24, atan2(self.dy, self.dx), after, fade)
            return
        after = self.elapsed - self.swing.contact
        if not 0 <= after < TRAIL_TIME:
            return
        fade = 1 - after / TRAIL_TIME
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


CRESCENT_SPAN = 2.6           # radians the half moon covers, centred on the aim
CRESCENT_GROW = 0.035         # seconds for the cut to sweep across
CRESCENT_RADIUS = 46          # px, outer edge
CRESCENT_THICK = 18           # px, thickness in the middle (the tips taper to nothing)
CRESCENT_STEPS = 150         # dense enough that the band has no gaps


def draw_crescent(x, y, angle, after, fade):
    """A big, clean half moon swept in the aim's direction: a solid band, thick in the
    middle and sharp at both tips, white along the outer edge and cooler inside; it
    sweeps from one tip to the other in the first CRESCENT_GROW seconds."""
    grow = min(1.0, after / CRESCENT_GROW)
    shown = max(1, round(CRESCENT_STEPS * grow))
    edge = None
    for index in range(shown + 1):
        t = index / CRESCENT_STEPS
        taper = 1 - abs(2 * t - 1) ** 1.6          # 0 at the tips, 1 in the middle
        theta = angle + CRESCENT_SPAN * (0.5 - t)
        c, s = cos(theta), sin(theta) * 0.85
        outer = CRESCENT_RADIUS
        core = outer - CRESCENT_THICK * 0.4 * taper
        inner = outer - CRESCENT_THICK * taper
        pico2d.draw_line(x + c * inner, y + s * inner, x + c * core, y + s * core,
                         150, 225, 210, round(150 * fade))
        pico2d.draw_line(x + c * core, y + s * core, x + c * outer, y + s * outer,
                         255, 255, 255, round(245 * fade))
        point = (x + c * (outer + 1), y + s * (outer + 1))
        if edge is not None:
            pico2d.draw_line(*edge, *point, 255, 255, 255, round(255 * fade))
        edge = point


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
