"""Screen objects for a running fight.

Combat (combat.py) holds the rules. Each class here is one element on screen with
update()/draw(), registered in a game_world layer by create_views() — the same
pattern as the course's Boy/Grass/Ball objects.
"""

import math

import pico2d

import game_clock
import game_world
import hit_feel
import ui
from combat import (
    BADGE_TIME, END_TURN_CENTER, END_TURN_RADIUS, ENEMY_COLOR, FOOT_RX, FOOT_RY,
    HUD_BOTTOM, HUD_TOP, LOG_LINE, LOG_LINES, LOG_WIDTH, PARTY_COLOR, POPUP_TIME, PORTRAIT_CENTER,
    HIT_GAUGE_TIME, PORTRAIT_RADIUS, REACH_M, SLOT_COLUMNS, SLOT_GAP, SLOT_SIZE, SLOTS_LEFT, TEXT_COLOR, fmt_m,
    hit_chance,
)
from nav import NODE_X, NODE_Y, PX_PER_M_X, PX_PER_M_Y, metres, path_length
from tile_map import WIDTH

WEAPON_RECT = (112, 30, 160, 78)   # the equipped-weapon slot beside the portrait


def team_color(fighter):
    return PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR


def draw_portrait(fighter, left, bottom, width, height, color):
    pico2d.draw_rectangle(left, bottom, left + width, bottom + height, 24, 32, 40, filled=True)
    pico2d.draw_rectangle(left, bottom, left + width, bottom + height, *color)
    clip = getattr(fighter.unit, "portrait_clip", None)
    if clip is None:
        return
    image, sx, sy, sw, sh = clip()
    scale = min((width - 4) / sw, (height - 4) / sh)
    image.clip_draw(sx, sy, sw, sh, left + width / 2, bottom + height / 2, sw * scale, sh * scale)
    if not fighter.alive:
        pico2d.draw_rectangle(left, bottom, left + width, bottom + height, 0, 0, 0, 150, filled=True)


def roll_outcome(result):
    """Verdict text and colour for a hit roll."""
    if result["critical"]:
        return "치명타!", ui.CRITICAL
    if result["fumble"]:
        return "대실패", ui.DIM
    return ("명중!", ui.DANGER) if result["hit"] else ("빗나감", ui.MISS)


class CombatView:
    def __init__(self, combat):
        self.combat = combat

    def sx(self, x):
        """World x to screen x (the fight keeps the camera fixed)."""
        return x - self.combat.camera_x

    def update(self):
        pass


# Board layer (under the units) ---------------------------------------------------

class CombatBoard(CombatView):
    """Runs the fight each frame and draws the movement area, foot rings and paths."""

    def __init__(self, combat):
        super().__init__(combat)
        self.area_cache = None

    def update(self):
        self.combat.update(game_clock.step())

    def foot_ring(self, fighter, color, scale=1.0, dashed=False):
        x, y = fighter.pos
        ui.ellipse(self.sx(x), y - 10, FOOT_RX * scale, FOOT_RY * scale, color, dashed=dashed)

    def draw(self):
        c = self.combat
        player_turn = c.is_player_turn()
        if player_turn and c.mode == "move":
            self.draw_reach_area()
        if player_turn and c.mode == "attack":
            x, y = c.current.pos
            # Melee reach as a dashed ellipse in floor perspective.
            ui.ellipse(self.sx(x), y - 10, REACH_M * PX_PER_M_X, REACH_M * PX_PER_M_Y, ui.DANGER, 40, dashed=True)
        for fighter in c.fighters:
            if not fighter.alive:
                continue
            active = fighter is c.current and c.outcome is None
            self.foot_ring(fighter, ui.ACCENT if active else team_color(fighter))
            if active:
                self.foot_ring(fighter, ui.ACCENT, 1.2)
        if not player_turn:
            return
        if c.mode == "attack":
            for enemy in c.living_foes(c.current):
                if c.in_reach(c.current.pos, enemy.pos):
                    self.foot_ring(enemy, ui.DANGER, 1.35)
                elif c.plan_approach(c.current, enemy):
                    self.foot_ring(enemy, ui.ACCENT, 1.35, dashed=True)
        hovered = c.hovered_target()
        if hovered is not None:
            self.foot_ring(hovered, ui.DANGER, 1.2)
        if c.mode == "move":
            self.draw_move_path()
        elif hovered is not None and c.current.action and not c.in_reach(c.current.pos, hovered.pos):
            points = c.plan_approach(c.current, hovered)
            if points:
                self.draw_polyline(points, ui.ACCENT)
                end_x, end_y = points[-1]
                ui.ellipse(self.sx(end_x), end_y - 10, FOOT_RX, FOOT_RY, ui.ACCENT, dashed=True)

    def draw_polyline(self, points, color, thick=False):
        screen = [(self.sx(x), y) for x, y in points]
        for (x1, y1), (x2, y2) in zip(screen, screen[1:]):
            pico2d.draw_line(x1, y1, x2, y2, *color)
            if thick:
                pico2d.draw_line(x1, y1 + 1, x2, y2 + 1, *color)

    def draw_move_path(self):
        c = self.combat
        points = c.plan_move(c.current, c.hover)
        if not points:
            return
        color = ui.DANGER if c.path_provokes(c.current, points) else ui.ACCENT
        self.draw_polyline(points, color, thick=True)
        end_x, end_y = points[-1]
        ui.ellipse(self.sx(end_x), end_y - 10, FOOT_RX, FOOT_RY, color)

    def draw_reach_area(self):
        """BG3-like movement area: a soft fill with a brighter rim."""
        costs = self.combat.search(self.combat.current)
        if self.area_cache is None or self.area_cache[0] is not costs:
            self.area_cache = (costs, self.area_shapes(set(costs)))
        runs, rim = self.area_cache[1]
        for left, right, y in runs:
            pico2d.draw_rectangle(self.sx(left), y - NODE_Y / 2, self.sx(right), y + NODE_Y / 2 - 1,
                                  *ui.MOVE, 34, filled=True)
        for x, y in rim:
            pico2d.draw_rectangle(self.sx(x) - 1, y - 1, self.sx(x) + 1, y + 1, *ui.MOVE, filled=True)

    def area_shapes(self, nodes):
        """Merge reachable nodes into row runs for the fill and collect rim points."""
        nav = self.combat.nav
        runs, rim = [], []
        for row in sorted({r for _, r in nodes}):
            columns = sorted(c for c, r in nodes if r == row)
            start = previous = columns[0]
            for column in columns[1:] + [None]:
                if column is not None and column == previous + 1:
                    previous = column
                    continue
                left, y = nav.position((start, row))
                right, _ = nav.position((previous, row))
                runs.append((left - NODE_X / 2, right + NODE_X / 2 - 1, y))
                if column is not None:
                    start = previous = column
        for c, r in nodes:
            if any((c + dc, r + dr) not in nodes for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                rim.append(nav.position((c, r)))
        return runs, rim


# Overlay layer (above the units) ------------------------------------------------

class HealthBars(CombatView):
    def draw(self):
        for fighter in self.combat.fighters:
            if fighter.alive:
                ui.bar(self.sx(fighter.unit.x) - 18, fighter.unit.y + 52, 36, 4,
                       fighter.hp / fighter.max_hp, team_color(fighter))


class PartyColumn(CombatView):
    """Party portraits down the left edge with health, as in BG3."""

    def draw(self):
        c = self.combat
        top = HUD_BOTTOM - 14
        for fighter in c.fighters:
            if fighter.team != "party":
                continue
            active = fighter is c.current and c.outcome is None
            border = ui.ACCENT if active else (PARTY_COLOR if fighter.alive else ui.DIM)
            left, bottom = 8, top - 66
            pico2d.draw_rectangle(left - 2, bottom - 2, left + 54, top + 2, *ui.PANEL, 220, filled=True)
            draw_portrait(fighter, left, bottom, 52, 66, border)
            ui.panel(left + 4, bottom + 2, left + 48, bottom + 18, border, ui.PANEL, 230)
            ui.text_center(left + 26, bottom + 10, f"{fighter.hp}/{fighter.max_hp}", ui.TEXT, 12)
            top = bottom - 10


class TargetHeader(CombatView):
    """BG3-style target readout under the turn order: name, big health bar, status."""

    def draw(self):
        c = self.combat
        target = c.hovered_target() if c.is_player_turn() else None
        if target is None and c.attack is not None:
            target = c.attack["target"]
        if target is None:
            return
        color = team_color(target)
        center, top = WIDTH / 2, HUD_BOTTOM - 10
        ui.panel(center - 140, top - 74, center + 140, top + 6, (120, 98, 60), ui.PANEL, 200)
        ui.text_center(center, top - 8, target.name, color, 18)
        ui.text_center(center, top - 26, f"방어 {target.armor_class}", ui.MUTED, 13)
        width = 260
        left = center - width / 2
        ui.panel(left - 2, top - 48, left + width + 2, top - 34, (120, 98, 60), ui.PANEL, 230)
        ui.bar(left, top - 46, width, 10, target.hp / target.max_hp, color, (40, 26, 28))
        ui.text_center(center, top - 41, f"{target.hp}/{target.max_hp}", ui.TEXT, 12)
        statuses = []
        if target.surprised:
            statuses.append(("기습당함", ui.DANGER))
        if target.team == "enemy" and target.alive:
            statuses.append(("적대적", ENEMY_COLOR))
        if not target.alive:
            statuses.append(("쓰러짐", ui.DIM))
        x = center - sum(ui.text_width(s, 13) + 26 for s, _ in statuses) / 2
        for label, chip_color in statuses:
            pico2d.draw_circle(x + 6, top - 62, 5, *chip_color, filled=True)
            ui.text(x + 15, top - 62, label, ui.MUTED, 13)
            x += ui.text_width(label, 13) + 26


class PointerInfo(CombatView):
    """What the mouse is over: hit chance next to an enemy, or the distance of a move."""

    def draw(self):
        c = self.combat
        if not c.is_player_turn():
            return
        target = c.hovered_target()
        if target is not None:
            self.draw_hit_chip(c.current, target)
        elif c.mode == "move":
            self.draw_move_label()

    def draw_hit_chip(self, attacker, target):
        c = self.combat
        x = self.sx(target.unit.x) + 24
        y = target.unit.y + 30
        chance = round(hit_chance(attacker.attack_bonus, target.armor_class) * 100)
        low, high = attacker.damage_range()
        approach = None
        if not attacker.action:
            note, note_color = "자원이 충분하지 않음: 행동", ui.DANGER
        elif c.in_reach(attacker.pos, target.pos):
            note, note_color = "클릭하면 공격", ui.MUTED
        else:
            approach = c.plan_approach(attacker, target)
            if approach:
                note, note_color = f"{fmt_m(path_length(approach))} 이동 후 공격", ui.ACCENT
            else:
                note, note_color = f"닿지 않음 · 거리 {fmt_m(metres(attacker.pos, target.pos))}", ui.DANGER
        usable = bool(attacker.action) and (c.in_reach(attacker.pos, target.pos) or approach)
        big = f"{chance}%"
        detail = f"피해 {low}~{high} · 방어 {target.armor_class}"
        width = max(32 + ui.text_width(big, 24) + 6 + ui.text_width("명중 확률", 13),
                    ui.text_width(detail, 13), ui.text_width(note, 13)) + 20
        height = 70
        x = min(x, WIDTH - width - 4)
        ui.panel(x, y, x + width, y + height, ui.ACCENT if usable else ui.DIM, ui.PANEL, 235)
        for offset in (-1, 0, 1):
            pico2d.draw_line(x + 10 + offset, y + height - 30, x + 24 + offset, y + height - 12, 196, 160, 110)
        ui.text(x + 32, y + height - 20, big, ui.ACCENT if usable else ui.DIM, 24)
        ui.text(x + 32 + ui.text_width(big, 24) + 6, y + height - 24, "명중 확률", ui.MUTED, 13)
        ui.text(x + 10, y + 26, detail, ui.TEXT, 13)
        ui.text(x + 10, y + 10, note, note_color, 13)

    def draw_move_label(self):
        c = self.combat
        points = c.plan_move(c.current, c.hover)
        if not points:
            return
        x, y = points[-1]
        x = self.sx(x)
        danger = c.path_provokes(c.current, points)
        label = fmt_m(path_length(points)) + (" · 기회 공격 위험" if danger else "")
        color = ui.DANGER if danger else ui.ACCENT
        width = ui.text_width(label, 14) + 14
        ui.panel(x - width / 2, y + 22, x + width / 2, y + 42, color)
        ui.text_center(x, y + 32, label, color, 14)


class Popups(CombatView):
    """Short floating texts such as '기회 공격!'."""

    def draw(self):
        for text, x, y, time_left, color in self.combat.popups:
            rise = (POPUP_TIME - time_left) * 22
            ui.text_center(self.sx(x), y + rise, text, color)


class InitiativeBadges(CombatView):
    """'선공 6 / 주사위 4 + 민첩 2' over each fighter when the fight starts."""

    def draw(self):
        for badge in self.combat.badges:
            unit = badge["unit"]
            x, y = self.sx(unit.x), unit.y + 82
            width = max(ui.text_width(badge["title"], 16), ui.text_width(badge["detail"], 13)) + 18
            left = max(4, min(WIDTH - 4 - width, x - width / 2))
            ui.panel(left, y - 19, left + width, y + 19, badge["color"])
            ui.text(left + 9, y + 8, badge["title"], badge["color"], 16)
            ui.text(left + 9, y - 9, badge["detail"], ui.MUTED, 13)


def needed_face(attacker, target):
    """Lowest d20 face that hits (a 1 always misses, a 20 always hits)."""
    return max(2, min(20, target.armor_class - attacker.attack_bonus))


def ease_out(u, power):
    return 1 - (1 - u) ** power


class SpinMotion:
    """Where the hit wheel's needle points at a given moment of its spin.

    Positions count d20 slices clockwise from 12 o'clock (slice k shows face k % 20 + 1).
    The needle whirls round a few times, slows until it ticks over slice by slice, and
    stops on the rolled face. Results close to the hit line get extra drama: a near
    miss swings on until it is just over the line into green, hangs there and falls
    back; a near hit hangs on the last red slice, then tips over the line.
    """

    TURNS = 5            # full turns before the result slice
    EASE = 4             # higher = faster start and a longer crawl at the end
    TEASE_SHARE = 0.75   # share of the spin spent before the hang
    HANG = 0.35          # share of the remaining time spent hanging still
    PEEK = 0.45          # how far (in slices) over the line the needle hangs

    def __init__(self, face, need, duration):
        self.final = face - 1 + 20 * self.TURNS
        self.duration = duration
        self.lean = 0.0                         # where it hangs, relative to the result
        if face != 1 and need - 2 <= face < need:
            self.lean = (need - 1 - face) + self.PEEK            # just past the line
        elif face != 20 and need <= face <= need + 1:
            self.lean = -(face - need) - (1 - self.PEEK)       # just short of the line

    def position(self, elapsed):
        u = max(0.0, min(1.0, elapsed / self.duration)) if self.duration > 0 else 1.0
        if not self.lean:
            return self.final * ease_out(u, self.EASE)
        if u < self.TEASE_SHARE:
            return (self.final + self.lean) * ease_out(u / self.TEASE_SHARE, self.EASE)
        rest = (u - self.TEASE_SHARE) / (1 - self.TEASE_SHARE)
        settle = 0.0 if rest < self.HANG else ease_out((rest - self.HANG) / (1 - self.HANG), 2)
        return self.final + self.lean * (1 - settle)


class HitWheel(CombatView):
    """Hit roll as a spinning wheel over the attacker's head.

    The wheel has the twenty d20 faces as slices: green slices hit, red ones miss, so
    the share of green is the hit chance. A needle whirls round and stops on the
    rolled face; the slice under the needle lights up and its face shows in the hub.
    """

    RADIUS = 34
    SLICE = 360 / 20
    OFFSET_Y = 64 + 34 + 4   # wheel centre above the attacker's feet
    PULSE_FROM = 0.6         # share of the spin after which the rim starts to pulse
    FLASH_TIME = 0.15
    HIT_COLOR = (60, 130, 80)
    MISS_COLOR = (130, 56, 48)
    FUMBLE_COLOR = (90, 30, 30)
    HIT_TEXT = (120, 220, 140)

    def draw(self):
        c = self.combat
        attack = c.attack
        if attack is not None and attack.get("phase") == "dice" and not attack["landed"]:
            motion = attack.get("spin")
            if motion is None:
                need = needed_face(attack["attacker"], attack["target"])
                motion = attack["spin"] = SpinMotion(attack["result"]["roll"], need, attack["roll_time"])
            spin = attack["dice_time"] / attack["roll_time"] if attack["roll_time"] else 1.0
            self.draw_wheel(attack["attacker"], attack["target"], motion.position(attack["dice_time"]), None, spin)
        for record in c.hit_rolls:
            flash = record["time"] > HIT_GAUGE_TIME - self.FLASH_TIME
            self.draw_wheel(record["attacker"], record["target"], record["result"]["roll"] - 1.0,
                            record["result"], 1.0, flash)

    def face_color(self, face, need):
        if face == 20:
            return ui.CRITICAL
        if face == 1:
            return self.FUMBLE_COLOR
        return self.HIT_COLOR if face >= need else self.MISS_COLOR

    def verdict(self, result):
        if result["critical"]:
            return "치명타!", ui.CRITICAL
        if result["fumble"]:
            return "대실패", ui.DIM
        return ("명중!", self.HIT_TEXT) if result["hit"] else ("빗나감", ui.MISS)

    def draw_wheel(self, attacker, target, position, result, spin, flash=False):
        need = needed_face(attacker, target)
        radius = self.RADIUS
        cx = max(radius + 14, min(WIDTH - radius - 14, self.sx(attacker.unit.x)))
        cy = attacker.unit.y + self.OFFSET_Y
        if result is None:
            title, rim = f"명중 {round(hit_chance(attacker.attack_bonus, target.armor_class) * 100)}%", ui.TEXT
            if spin > self.PULSE_FROM:
                # The rim throbs faster as the needle slows down.
                beat = abs(math.sin((spin - self.PULSE_FROM) * 28))
                rim = tuple(int(v * (0.55 + 0.45 * beat)) for v in ui.ACCENT)
        else:
            title, rim = self.verdict(result)

        pico2d.draw_circle(cx, cy, radius + 5, *ui.PANEL, filled=True)
        current = int(math.floor(position + 0.5)) % 20 + 1     # face under the needle
        for face in range(1, 21):
            start = (face - 1) * self.SLICE
            color = self.face_color(face, need)
            if face == current:
                # The slice under the needle lights up, so each tick over reads as a step.
                color = tuple(min(255, v + 70) for v in color)
            ui.wedge(cx, cy, radius, start, start + self.SLICE, color)
        for face in range(1, 21):
            pico2d.draw_line(cx, cy, *ui.dial_point(cx, cy, radius, (face - 1) * self.SLICE), *ui.PANEL)
        # The hit line: where green begins.
        edge = (need - 1) * self.SLICE
        for offset in (-0.8, 0, 0.8):
            pico2d.draw_line(cx, cy, *ui.dial_point(cx, cy, radius + 4, edge + offset), *ui.ACCENT)
        ui.ring(cx, cy, radius + 5, rim, 3)
        # The target's armour sits at the end of the red, where the roll must reach.
        DamageRoll.outlined(*ui.dial_point(cx, cy, radius + 15, edge - self.SLICE / 2),
                            str(target.armor_class), ui.TEXT, 13)
        if flash and result["hit"]:
            ui.ring(cx, cy, radius + 9, rim, 2)

        # Needle from the hub to the rim: white with a dark outline so it reads on any slice.
        angle = (position + 0.5) * self.SLICE
        tip = ui.dial_point(cx, cy, radius - 3, angle)
        outline = (14, 18, 22)
        for side, color in ((-2.5, outline), (2.5, outline), (-1.2, ui.TEXT), (0, ui.TEXT), (1.2, ui.TEXT)):
            base = ui.dial_point(cx, cy, side, angle + 90)
            pico2d.draw_line(*base, *tip, *color)
        hub = self.face_color(current, need)
        pico2d.draw_circle(cx, cy, 12, *hub, filled=True)
        ui.ring(cx, cy, 12, ui.TEXT, 2)
        ui.text_center(cx, cy, str(current), (20, 20, 20) if current == 20 else ui.TEXT, 14)
        size = 18 if result is not None else 15
        DamageRoll.outlined(cx, cy + radius + 18, title, rim, size)


class DamageRoll(CombatView):
    """The attack's outcome rising over the target: "명중" with the damage, or "빗나감".

    The possible range (e.g. 3~8) is shown beforehand in the hover readout; the
    dice behind the number stay in the combat log, so the screen only says
    whether it landed and how much it hurt.
    """

    RISE_PER_SECOND = 18
    POP_TIME = 0.16          # the number appears oversized and settles within this time
    HIT_TEXT = HitWheel.HIT_TEXT

    def draw(self):
        for record in self.combat.damage_rolls:
            self.draw_number(record)

    def draw_number(self, record):
        target = record["target"]
        elapsed = BADGE_TIME - record["time"]
        x = self.sx(target.unit.x)
        y = target.unit.y + 74 + elapsed * self.RISE_PER_SECOND
        if not record["hit"]:
            self.outlined(x, y + 6, "대실패" if record["fumble"] else "빗나감", ui.MISS, 18)
            return
        # Size, colour and pop come from the hit's weight, shared by every attack.
        feel = hit_feel.feel(record["weight"])
        grow = feel.pop * (1 - min(1.0, elapsed / self.POP_TIME)) ** 2
        size = round(feel.number_size * (1 + grow))
        color = ui.CRITICAL if record["critical"] else feel.number_color
        label = ("치명타!", ui.CRITICAL) if record["critical"] else ("명중", self.HIT_TEXT)
        self.outlined(x, y + feel.number_size + 2, *label, 16)
        self.outlined(x, y - (size - feel.number_size) / 2, f"-{record['damage']}", color, size)

    @staticmethod
    def outlined(x, y, text, color, size):
        # A dark outline keeps the number readable over the bright sky.
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
            ui.text_center(x + dx, y + dy, text, (14, 18, 22), size)
        ui.text_center(x, y, text, color, size)


class ResourceRow(CombatView):
    """Named resource icons above the hotbar (drawn in the world, under the floor)."""

    def draw(self):
        c = self.combat
        if c.current.team != "party" or c.outcome is not None:
            return
        fighter = c.selected or c.current
        x, y = 238, 13
        ui.panel(x - 12, y - 11, x + 404, y + 11, ui.BORDER, ui.PANEL, 210)
        ui.action_icon(x, y, 6, bool(fighter.action))
        ui.text(x + 10, y, "행동", ui.TEXT if fighter.action else ui.DIM, 12)
        ui.bonus_icon(x + 52, y, 7, bool(fighter.bonus_action))
        ui.text(x + 62, y, "보조", ui.TEXT if fighter.bonus_action else ui.DIM, 12)
        ui.reaction_icon(x + 104, y, 7, bool(fighter.reaction))
        ui.text(x + 114, y, "반응", ui.TEXT if fighter.reaction else ui.DIM, 12)
        total = max(0.1, fighter.move_m)
        cost = 0.0
        if c.is_player_turn() and c.mode == "move":
            points = c.plan_move(fighter, c.hover)
            cost = path_length(points) if points else 0.0
        left_after = max(0.0, fighter.moves_left - cost)
        bar_x = x + 156
        ui.bar(bar_x, y - 3, 60, 6, left_after / total, ui.MOVE)
        if cost:
            # The part this move would spend, shown in gold like BG3's preview.
            start = bar_x + 60 * left_after / total
            pico2d.draw_rectangle(start, y - 3, start + 60 * cost / total, y + 3, *ui.ACCENT, filled=True)
            ui.text(bar_x + 66, y, f"{fmt_m(cost)} 사용 · 남음 {fmt_m(left_after)}", ui.ACCENT, 12)
        else:
            ui.text(bar_x + 66, y, f"이동 {fighter.moves_left:.1f}/{fmt_m(fighter.move_m)}", ui.MUTED, 12)


class SlotTooltip(CombatView):
    """Tooltip above a hovered hotbar slot, drawn in world coordinates."""

    def draw(self):
        c = self.combat
        if not c.is_player_turn() or c.hover_bottom is None:
            return
        mx, my = c.hover_bottom
        fighter = c.selected
        w_left, w_bottom, w_right, w_top = WEAPON_RECT
        if w_left <= mx <= w_right and w_bottom <= my <= w_top:
            # The weapon itself: what one swing does.
            self.draw_box(self.attack_lines(fighter), w_left, w_right)
            return
        hit = c.slot_at(mx, my)
        if hit is None or hit[0] is None:
            return
        (kind, label, cost, enabled), (left, _, right, _) = hit
        if kind == "move":
            lines = [(f"이동 · 남은 거리 {fmt_m(fighter.moves_left)}", ui.TEXT),
                     ("원하는 곳을 클릭해 걸어갑니다", ui.MUTED)]
        else:
            lines = self.attack_lines(fighter) + [("적을 클릭하면 사거리까지 걸어가서 칩니다", ui.MUTED)]
        if not enabled:
            reason = "남은 이동 거리가 없음" if kind == "move" else (
                "자원이 충분하지 않음: 행동" if not fighter.action else "공격할 적이 없음")
            lines.append((reason, ui.DANGER))
        self.draw_box(lines, left, right)

    @staticmethod
    def attack_lines(fighter):
        low, high = fighter.damage_range()
        return [("방망이 근접 공격 · 행동 1", ui.TEXT), (f"피해 {low}~{high}", ui.DANGER)]

    @staticmethod
    def draw_box(lines, left, right):
        width = max(ui.text_width(text, 13) for text, _ in lines) + 18
        height = 18 * len(lines) + 10
        x = max(4, min(WIDTH - width - 4, (left + right) / 2 - width / 2))
        bottom = 30
        ui.panel(x, bottom, x + width, bottom + height, ui.BORDER_LIGHT, ui.PANEL, 240)
        for index, (text, color) in enumerate(lines):
            ui.text(x + 9, bottom + height - 14 - 18 * index, text, color, 13)


class CombatLog(CombatView):
    """Collapsible combat log in the top-right corner (click the header or press L)."""

    def draw(self):
        c = self.combat
        left, bottom, right, top = c.log_header_rect()
        mouse = c.hover
        hovered = mouse is not None and left <= mouse[0] <= right and bottom <= mouse[1] <= top
        ui.panel(left, bottom, right, top, ui.ACCENT if hovered else (120, 98, 60), ui.PANEL_RAISED, 235)
        tx, ty = left + 12, (bottom + top) / 2
        if c.log_open:
            pico2d.draw_line(tx - 5, ty + 3, tx + 5, ty + 3, *ui.ACCENT)
            pico2d.draw_line(tx - 5, ty + 3, tx, ty - 4, *ui.ACCENT)
            pico2d.draw_line(tx + 5, ty + 3, tx, ty - 4, *ui.ACCENT)
        else:
            pico2d.draw_line(tx - 3, ty + 5, tx - 3, ty - 5, *ui.ACCENT)
            pico2d.draw_line(tx - 3, ty + 5, tx + 4, ty, *ui.ACCENT)
            pico2d.draw_line(tx - 3, ty - 5, tx + 4, ty, *ui.ACCENT)
        ui.text(left + 24, ty, "전투 기록", ui.TEXT, 14)
        ui.text(right - 64, ty, "L 접기" if c.log_open else "L 펼치기", ui.DIM, 12)
        if not c.log_open:
            return
        lines = list(c.history)[-LOG_LINES:]
        height = LOG_LINE * len(lines) + 8
        ui.panel(left, bottom - height, right, bottom, (64, 80, 92), ui.PANEL, 215)
        for index, (line, color) in enumerate(lines):
            ui.text(left + 8, bottom - 12 - LOG_LINE * index, self.fit(line, LOG_WIDTH - 14, 12), color, 12)

    @staticmethod
    def fit(line, width, size):
        if ui.text_width(line, size) <= width:
            return line
        while line and ui.text_width(line + "…", size) > width:
            line = line[:-1]
        return line + "…"


class StartBanner(CombatView):
    def draw(self):
        c = self.combat
        if not c.banner_time:
            return
        label = "기습! 전투 시작" if c.surprise else "발각! 전투 시작"
        width = ui.text_width(label, 20) + 48
        ui.panel(WIDTH / 2 - width / 2, 300, WIDTH / 2 + width / 2, 340, ui.ACCENT)
        ui.text_center(WIDTH / 2, 320, label, ui.ACCENT, 20)


# Top strip ------------------------------------------------------------------------

class TurnOrderBar(CombatView):
    """Turn order portraits in the top strip, current fighter outlined in gold."""

    def draw(self):
        c = self.combat
        ui.panel(0, HUD_BOTTOM, WIDTH - 1, HUD_TOP - 1, ui.BORDER, ui.PANEL, 255)
        pico2d.draw_line(0, HUD_BOTTOM + 1, WIDTH, HUD_BOTTOM + 1, 120, 98, 60)
        ui.text(14, HUD_BOTTOM + 40, f"{c.round}라운드", ui.ACCENT, 16)
        ui.text(14, HUD_BOTTOM + 18, "선공 1d4 + 민첩", ui.DIM, 12)
        size, gap = 46, 6
        count = len(c.order)
        left = WIDTH / 2 - (count * size + (count - 1) * gap) / 2
        for index, fighter in enumerate(c.order):
            x = left + index * (size + gap)
            current = index == c.turn_index and c.outcome is None
            border = ui.ACCENT if current else (team_color(fighter) if fighter.alive else ui.DIM)
            bottom = HUD_BOTTOM + 8
            draw_portrait(fighter, x, bottom, size, 50, border)
            if current:
                pico2d.draw_rectangle(x - 2, bottom - 2, x + size + 2, bottom + 52, *ui.ACCENT)
            ui.bar(x + 3, bottom + 3, size - 6, 4, fighter.hp / fighter.max_hp, team_color(fighter))
            ui.text(x + size - 12, bottom + 42, str(fighter.initiative), ui.MUTED, 11)
            if fighter.surprised:
                ui.text_center(x + size / 2, bottom + 25, "기습", ui.DANGER, 12)
        if c.log:
            ui.text(left + count * (size + gap) + 20, HUD_BOTTOM + 32, c.log, ui.MUTED, 13)


# Bottom hotbar ----------------------------------------------------------------------

class Hotbar(CombatView):
    """BG3-style hotbar: round portrait, weapon, action slots and the round end-turn button."""

    def draw(self):
        c = self.combat
        ui.panel(0, 0, WIDTH - 1, ui.BOTTOM_HEIGHT - 1, ui.BORDER, ui.PANEL, 255)
        pico2d.draw_line(0, ui.BOTTOM_HEIGHT - 2, WIDTH, ui.BOTTOM_HEIGHT - 2, 120, 98, 60)
        self.draw_round_portrait(c.current)
        self.draw_weapon_slot()
        player_turn = c.is_player_turn()
        mouse = c.hover_bottom
        for entry, (left, bottom, right, top) in c.bottom_slots():
            hovered = mouse is not None and left <= mouse[0] <= right and bottom <= mouse[1] <= top
            self.draw_slot(entry, left, bottom, right, top, hovered and player_turn)
        self.draw_end_turn(player_turn)

    def draw_round_portrait(self, fighter):
        x, y = PORTRAIT_CENTER
        color = team_color(fighter)
        pico2d.draw_circle(x, y, PORTRAIT_RADIUS, 24, 32, 40, filled=True)
        clip = getattr(fighter.unit, "portrait_clip", None)
        if clip is not None:
            image, sx, sy, sw, sh = clip()
            scale = PORTRAIT_RADIUS * 1.35 / max(sw, sh)
            image.clip_draw(sx, sy, sw, sh, x, y + 6, sw * scale, sh * scale)
        # Lost health fills the circle from below in red, as in BG3.
        lost = 1 - fighter.hp / fighter.max_hp
        if lost:
            height = 2 * PORTRAIT_RADIUS * lost
            pico2d.draw_rectangle(x - PORTRAIT_RADIUS + 8, y - PORTRAIT_RADIUS + 4,
                                  x + PORTRAIT_RADIUS - 8, y - PORTRAIT_RADIUS + 4 + height,
                                  170, 40, 40, 110, filled=True)
        ui.ring(x, y, PORTRAIT_RADIUS, color, 3)
        ui.ring(x, y, PORTRAIT_RADIUS + 3, (120, 98, 60), 1)
        label = f"{fighter.hp}/{fighter.max_hp}"
        width = ui.text_width(label, 14) + 12
        ui.panel(x - width / 2, y - PORTRAIT_RADIUS - 2, x + width / 2, y - PORTRAIT_RADIUS + 16, color)
        ui.text_center(x, y - PORTRAIT_RADIUS + 7, label, ui.TEXT, 14)

    @staticmethod
    def draw_weapon_slot():
        left, bottom, right, top = WEAPON_RECT
        ui.panel(left, bottom, right, top, ui.BORDER_LIGHT, ui.PANEL_RAISED, 255)
        for offset in (-1, 0, 1):
            pico2d.draw_line(left + 12 + offset, bottom + 10, right - 12 + offset, top - 10, 196, 160, 110)
        pico2d.draw_line(left + 10, bottom + 8, left + 16, bottom + 14, 90, 70, 50)
        ui.text_center((left + right) / 2, bottom - 10, "방망이", ui.MUTED, 12)

    def draw_slot(self, entry, left, bottom, right, top, hovered):
        if entry is None:
            ui.panel(left, bottom, right, top, (44, 54, 62), (20, 27, 34), 255)
            return
        kind, label, cost, enabled = entry
        if kind == self.combat.mode:
            border, fill = ui.ACCENT, (60, 76, 86)
        elif enabled:
            border, fill = (ui.ACCENT if hovered else ui.BORDER_LIGHT), ui.PANEL_RAISED
        else:
            border, fill = ui.DIM, ui.PANEL
        ui.panel(left, bottom, right, top, border, fill, 255)
        color = (230, 210, 170) if enabled else ui.DIM
        cx, cy = (left + right) / 2, (bottom + top) / 2 + 4
        if kind == "move":
            pico2d.draw_line(cx - 11, cy - 6, cx + 9, cy + 6, *color)
            pico2d.draw_line(cx + 9, cy + 6, cx + 1, cy + 7, *color)
            pico2d.draw_line(cx + 9, cy + 6, cx + 6, cy - 2, *color)
        else:
            for offset in (-1, 0, 1):
                pico2d.draw_line(cx - 10 + offset, cy - 10, cx + 9 + offset, cy + 9, *color)
            pico2d.draw_line(cx - 4, cy + 6, cx + 6, cy - 4, *color)
        number = {"move": "1", "attack": "2"}[kind]
        ui.text(left + 3, top - 7, number, ui.MUTED if enabled else ui.DIM, 11)
        ui.text_center(cx, bottom + 7, label, ui.TEXT if enabled else ui.DIM, 11)
        if kind == "attack":
            ui.action_icon(right - 7, top - 7, 4, enabled)

    def draw_end_turn(self, enabled):
        x, y = END_TURN_CENTER
        mouse = self.combat.hover_bottom
        hovered = mouse is not None and (mouse[0] - x) ** 2 + (mouse[1] - y) ** 2 <= END_TURN_RADIUS ** 2
        pico2d.draw_circle(x, y, END_TURN_RADIUS, 22, 44, 58, filled=True)
        ring_color = ui.ACCENT if hovered and enabled else ((96, 170, 190) if enabled else ui.DIM)
        ui.ring(x, y, END_TURN_RADIUS, ring_color, 4)
        ui.ring(x, y, END_TURN_RADIUS + 3, (120, 98, 60), 1)
        ui.text_center(x, y + 6, "턴 종료", ui.TEXT if enabled else ui.DIM)
        ui.text_center(x, y - 14, "Space", ui.MUTED if enabled else ui.DIM, 12)


def create_views(combat):
    """Every screen object of a fight with the layer it belongs to."""
    overlay = [HealthBars, PartyColumn, TargetHeader, PointerInfo, Popups, InitiativeBadges,
               HitWheel, DamageRoll, ResourceRow, SlotTooltip, CombatLog, StartBanner]
    views = [(CombatBoard(combat), game_world.BOARD)]
    views += [(view(combat), game_world.OVERLAY) for view in overlay]
    views += [(TurnOrderBar(combat), game_world.HUD), (Hotbar(combat), game_world.BOTTOM)]
    return views
