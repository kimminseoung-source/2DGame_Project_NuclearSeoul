"""Turn-based combat on the street floor with free, metre-based movement (BG3 style)."""

import random
from collections import deque

import pico2d

import ui
from bat import BAT_DURATION, BatSwing
from nav import NODE_X, NODE_Y, PX_PER_M_X, PX_PER_M_Y, NavField, metres, path_length, point_along, truncate
from nav import bodies_clash as nav_clash
from tile_map import HEIGHT, WIDTH
from zombie import STRIKE_TIME, WINDUP_TIME


BANNER_TIME = 1.4
MOVE_SPEED_M = 4.5          # metres per second while walking
ENEMY_PAUSE = 0.45
SKIP_PAUSE = 0.9
POPUP_TIME = 1.3
VICTORY_PAUSE = 1.2
INITIATIVE_DIE = 4
BADGE_TIME = 1.5
# The badge rolls, lands on the result, holds briefly, and only then the swing starts.
DICE_ROLL_TIME = 0.45
DICE_HOLD_TIME = 0.4
BADGE_FLICKER = 0.06
REACH_M = 1.5               # melee reach, as in BG3
REACH_SLACK_M = 0.05
MIN_MOVE_M = 0.25
CLICK_SNAP_M = 0.6          # a click must land this close to the reachable area
# Top strip (inside the world canvas) and the hotbar strip under the world.
HUD_BOTTOM = HEIGHT
HUD_TOP = HEIGHT + 64
BAR_HEIGHT = ui.BOTTOM_HEIGHT
PORTRAIT_CENTER = (58, 52)
PORTRAIT_RADIUS = 44
SLOT_SIZE = 40
SLOT_GAP = 4
SLOT_COLUMNS = 8
SLOT_ROWS = 2
SLOTS_LEFT = 176
SLOTS_BOTTOM = 8
END_TURN_CENTER = (708, 52)
END_TURN_RADIUS = 40
FOOT_RX, FOOT_RY = 15, 6
LOG_WIDTH = 230
LOG_LINES = 8
LOG_LINE = 16
LOG_HEADER = 22
LOG_RIGHT = WIDTH - 8
LOG_TOP = HEIGHT - 8

PARTY_COLOR = ui.PARTY
ENEMY_COLOR = ui.ENEMY
TEXT_COLOR = ui.TEXT


def hit_chance(attack_bonus, armor_class, advantage=0):
    """Chance that d20 + bonus meets the armour class; 1 always misses, 20 always hits.

    advantage > 0 rolls two dice and keeps the higher, < 0 keeps the lower (BG3 rules).
    """
    single = (sum(1 for roll in range(2, 20) if roll + attack_bonus >= armor_class) + 1) / 20
    if advantage > 0:
        return 1 - (1 - single) ** 2
    if advantage < 0:
        return single ** 2
    return single


def badge_label(result):
    if result["critical"]:
        return "치명타!"
    if result["fumble"]:
        return "대실패"
    return "명중" if result["hit"] else "빗나감"


def badge_color(result):
    if result["critical"]:
        return ui.CRITICAL
    if result["fumble"]:
        return ui.DIM
    return ui.DANGER if result["hit"] else ui.MISS


def fmt_m(value):
    return f"{value:.1f}m"


class Fighter:
    """Turn data and combat stats for one unit on the street."""

    def __init__(self, unit, name, team, *, dexterity, move_m, max_hp,
                 armor_class, attack_bonus, damage_dice, damage_bonus, hp=None):
        self.unit = unit
        self.name = name
        self.team = team
        self.dexterity = dexterity
        self.move_m = move_m
        self.max_hp = max_hp
        self.hp = max_hp if hp is None else hp
        self.armor_class = armor_class
        self.attack_bonus = attack_bonus
        self.damage_dice = damage_dice  # (count, sides)
        self.damage_bonus = damage_bonus
        self.initiative = 0
        self.initiative_roll = 0
        self.surprised = False
        self.moves_left = 0.0
        self.action = 0
        self.bonus_action = 0
        # One reaction per round, refreshed at the start of the fighter's turn.
        self.reaction = 1

    @property
    def pos(self):
        return self.unit.x, self.unit.y

    @property
    def alive(self):
        return self.hp > 0

    def damage_range(self):
        count, sides = self.damage_dice
        return count + self.damage_bonus, count * sides + self.damage_bonus


class Combat:
    """Initiative order, free movement on a hidden lattice, and the current turn."""

    def __init__(self, camera_x, tile_map, fighters, surprise, rng=None):
        self.camera_x = camera_x
        self.nav = NavField(tile_map, camera_x, camera_x + WIDTH)
        self.surprise = surprise
        self.rng = rng or random.Random()
        self.banner_time = BANNER_TIME
        self.fighters = fighters
        placed = []
        for fighter in fighters:
            # Keep everyone on open floor and out of each other's bodies.
            if not self.nav.open_at(fighter.pos, placed):
                node = self.nav.nearest_open(fighter.pos, placed)
                fighter.unit.x, fighter.unit.y = self.nav.position(node)
            placed.append(fighter.pos)
            fighter.surprised = surprise and fighter.team == "enemy"
        self.roll_initiative()
        self.round = 1
        self.turn_index = 0
        self.hover = None           # mouse position in screen coordinates (world viewport)
        self.hover_screen = None
        self.hover_bottom = None
        self.moving = None
        self.attack = None
        self.wait_time = 0.0
        self.log = ""
        self.popups = []
        self.effects = []
        self.outcome = None
        self.selected = None
        self.mode = None
        self.dice_visual = random.Random()
        self._search_cache = None
        self._plan_cache = None
        self._area_cache = None
        self._approach_cache = None
        self.history = deque(maxlen=40)
        self.log_open = True
        # Small result badges over each fighter, starting with the initiative roll.
        self.badges = [
            {"unit": f.unit, "time": BADGE_TIME + 0.6, "face": None, "color": (181, 197, 209),
             "title": f"선공 {f.initiative}",
             "detail": f"주사위 {f.initiative_roll} + 민첩 {f.dexterity}"}
            for f in self.fighters
        ]
        order = ", ".join(f"{f.name} {f.initiative}" for f in self.order)
        self.record("기습! 전투 시작" if surprise else "발각! 전투 시작", ui.ACCENT)
        self.record(f"선공(1d4+민첩): {order}", ui.MUTED)
        self.start_turn()

    def record(self, text, color=TEXT_COLOR):
        self.history.append((text, color))

    # Turn order -----------------------------------------------------------

    def roll(self, sides=20):
        return self.rng.randint(1, sides)

    def roll_initiative(self):
        # Like BG3: 1d4 + dexterity, so dexterity matters more than luck.
        for fighter in self.fighters:
            fighter.initiative_roll = self.roll(INITIATIVE_DIE)
            fighter.initiative = fighter.initiative_roll + fighter.dexterity
        # Higher total first; dexterity breaks ties, then the party acts first.
        self.order = sorted(
            self.fighters,
            key=lambda f: (f.initiative, f.dexterity, f.team == "party"),
            reverse=True,
        )

    @property
    def current(self):
        return self.order[self.turn_index]

    def busy(self):
        return self.moving is not None or self.attack is not None or bool(self.wait_time)

    def is_player_turn(self):
        return self.outcome is None and self.current.team == "party" and not self.busy()

    def living(self, team):
        return [f for f in self.fighters if f.team == team and f.alive]

    def start_turn(self):
        fighter = self.current
        fighter.moves_left = float(fighter.move_m)
        fighter.action = 1
        fighter.bonus_action = 1
        fighter.reaction = 1
        # Like BG3, the active party member is selected automatically.
        self.selected = fighter if fighter.team == "party" else None
        self.mode = None
        self.record(f"{self.round}라운드 · {fighter.name}의 턴", ui.DIM)
        if fighter.surprised:
            self.record(f"{fighter.name}: 기습당해 행동 불가", ui.MISS)
            self.log = f"{fighter.name}: 기습당해 이번 라운드에 행동하지 못합니다."
            self.wait_time = SKIP_PAUSE
            return
        if fighter.team == "enemy":
            self.log = f"{fighter.name}의 턴"
            self.enemy_approach(fighter)
        else:
            self.log = f"{fighter.name}의 턴 · 아래 핫바에서 행동을 고르세요"

    def end_turn(self):
        if self.moving is not None or self.attack is not None or self.outcome is not None:
            return
        self.current.surprised = False
        while True:
            self.turn_index += 1
            if self.turn_index == len(self.order):
                self.turn_index = 0
                self.round += 1
            if self.current.alive:
                break
        self.wait_time = 0.0
        self.start_turn()

    # Positions and reach --------------------------------------------------

    def blockers(self, mover):
        return [f.pos for f in self.fighters if f is not mover and f.alive]

    def in_reach(self, a, b):
        return metres(a, b) <= REACH_M + REACH_SLACK_M

    def attack_targets(self, fighter):
        enemy_team = "enemy" if fighter.team == "party" else "party"
        return [f for f in self.living(enemy_team) if self.in_reach(f.pos, fighter.pos)]

    def to_world(self, screen_x, y):
        return screen_x + self.camera_x, y

    def fighter_under(self, screen_point):
        """The living fighter whose sprite is under a screen point."""
        if screen_point is None:
            return None
        x, y = self.to_world(*screen_point)
        hits = [f for f in self.fighters
                if f.alive and abs(f.unit.x - x) <= 16 and f.unit.y - 14 <= y <= f.unit.y + 46]
        if not hits:
            return None
        foes = [f for f in hits if f.team != self.current.team]
        pool = foes or hits
        return min(pool, key=lambda f: (abs(f.unit.x - x), abs(f.unit.y + 16 - y)))

    # Movement -------------------------------------------------------------

    def search(self, fighter):
        """Reachable lattice for the fighter's remaining movement, cached per state."""
        key = (id(fighter), fighter.pos, round(fighter.moves_left, 3), tuple(self.blockers(fighter)))
        if self._search_cache is None or self._search_cache[0] != key:
            costs = self.nav.search(fighter.pos, self.blockers(fighter), fighter.moves_left)
            self._search_cache = (key, costs)
        return self._search_cache[1]

    def plan_move(self, fighter, screen_point):
        """Straightened path to the reachable spot nearest the mouse, or None (cached)."""
        if screen_point is None:
            return None
        key = (id(fighter), fighter.pos, round(fighter.moves_left, 3), tuple(self.blockers(fighter)), screen_point)
        if self._plan_cache is not None and self._plan_cache[0] == key:
            return self._plan_cache[1]
        points = self._plan_move(fighter, screen_point)
        self._plan_cache = (key, points)
        return points

    def _plan_move(self, fighter, screen_point):
        point = self.to_world(*screen_point)
        costs = self.search(fighter)
        best = min(costs, key=lambda n: metres(self.nav.position(n), point), default=None)
        if best is None or metres(self.nav.position(best), point) > CLICK_SNAP_M:
            return None
        if metres(self.nav.position(best), fighter.pos) < MIN_MOVE_M:
            return None
        blockers = self.blockers(fighter)
        points = self.nav.route(fighter.pos, best, costs, blockers)
        # Finish exactly where the player clicked when that spot is open and in budget.
        if self.nav.open_at(point, blockers):
            if self.nav.segment_clear(fighter.pos, point, blockers):
                exact = [fighter.pos, point]
            elif len(points) > 2 and self.nav.segment_clear(points[-2], point, blockers):
                exact = points[:-1] + [point]
            else:
                exact = points[:-1] + [points[-1], point] if self.nav.segment_clear(points[-1], point, blockers) else None
            if exact and path_length(exact) <= fighter.moves_left + 1e-6:
                points = exact
        return points if path_length(points) <= fighter.moves_left + 1e-6 else truncate(points, fighter.moves_left)

    def plan_approach(self, fighter, target):
        """Path that ends inside melee reach of the target within the movement left, or None."""
        key = ("approach", id(fighter), fighter.pos, round(fighter.moves_left, 3), target.pos)
        if self._approach_cache is not None and self._approach_cache[0] == key:
            return self._approach_cache[1]
        costs = self.search(fighter)
        goals = [n for n in costs if metres(self.nav.position(n), target.pos) <= REACH_M - 0.15]
        points = None
        if goals:
            goal = min(goals, key=lambda n: costs[n][0] + self.side_penalty(n, target))
            points = self.nav.route(fighter.pos, goal, costs, self.blockers(fighter))
            if path_length(points) > fighter.moves_left + 1e-6:
                points = None
        self._approach_cache = (key, points)
        return points

    def side_penalty(self, node, target):
        """Extra cost (m) for spots not beside the target, so fighters face each other."""
        x, y = self.nav.position(node)
        return 0.5 * abs(y - target.pos[1]) / PX_PER_M_Y

    def start_moving(self, fighter, points, then_attack=None):
        self.moving = {"fighter": fighter, "points": list(points[1:]), "then_attack": then_attack}
        if fighter.team == "enemy":
            fighter.unit.transition("chase")

    def can_react(self, reactor, mover):
        return (reactor.alive and reactor.team != mover.team and reactor.reaction
                and not reactor.surprised)

    def provokers(self, mover, old, new):
        """Enemies whose reach the mover leaves by stepping from old to new."""
        return [f for f in self.fighters
                if self.can_react(f, mover) and self.in_reach(f.pos, old) and not self.in_reach(f.pos, new)]

    def path_provokes(self, mover, points):
        total = path_length(points)
        previous, walked = points[0], 0.0
        while walked < total:
            walked = min(total, walked + 0.1)
            current = point_along(points, walked)
            if self.provokers(mover, previous, current):
                return True
            previous = current
        return False

    def update_moving(self, frame_time):
        fighter, points = self.moving["fighter"], self.moving["points"]
        unit = fighter.unit
        old = fighter.pos
        target = points[0]
        remaining = metres(old, target)
        step = min(MOVE_SPEED_M * frame_time, remaining, max(0.0, fighter.moves_left))
        t = step / remaining if remaining else 1.0
        new = (old[0] + (target[0] - old[0]) * t, old[1] + (target[1] - old[1]) * t)
        if any(nav_clash(new, b) for b in self.blockers(fighter)):
            # Safety stop: never walk into another body, whatever the route said.
            points.clear()
            new = old
            step = 0.0
        reactors = self.provokers(fighter, old, new) if step else []
        if reactors:
            # Stop at the edge of reach and let the enemy take its opportunity attack.
            reactor = reactors[0]
            reactor.reaction = 0
            self.popup("기회 공격!", reactor.unit.x, reactor.unit.y + 96, (255, 214, 127))
            self.record(f"{fighter.name}이(가) 사거리를 벗어남 · {reactor.name} 기회 공격", ui.CRITICAL)
            self.start_attack(reactor, fighter, reaction=True)
            return
        if abs(target[0] - old[0]) > 1:
            unit.direction = 1 if target[0] > old[0] else -1
        unit.x, unit.y = new
        unit.walk_time += frame_time
        fighter.moves_left = max(0.0, fighter.moves_left - step)
        if metres(new, target) < 1e-3:
            unit.x, unit.y = target
            points.pop(0)
        if points and fighter.moves_left > 1e-3:
            return
        then_attack = self.moving.get("then_attack")
        self.moving = None
        unit.walk_time = 0.0
        if fighter.team == "enemy":
            unit.transition("idle")
            self.enemy_act(fighter)
        elif then_attack is not None and then_attack.alive and fighter.action \
                and self.in_reach(fighter.pos, then_attack.pos):
            self.start_attack(fighter, then_attack)

    # Enemy turn -----------------------------------------------------------

    def enemy_approach(self, fighter):
        targets = self.living("party")
        target = min(targets, key=lambda f: metres(f.pos, fighter.pos))
        if self.in_reach(target.pos, fighter.pos):
            self.enemy_act(fighter)
            return
        blockers = self.blockers(fighter)
        costs = self.nav.search(fighter.pos, blockers)
        goals = [n for n in costs if metres(self.nav.position(n), target.pos) <= REACH_M - 0.15]
        if goals:
            goal = min(goals, key=lambda n: costs[n][0] + self.side_penalty(n, target))
        else:
            goal = min(costs, key=lambda n: metres(self.nav.position(n), target.pos), default=None)
        if goal is None:
            self.wait_time = ENEMY_PAUSE
            return
        points = truncate(self.nav.route(fighter.pos, goal, costs, blockers), fighter.moves_left)
        if len(points) < 2:
            self.enemy_act(fighter)
            return
        self.start_moving(fighter, points)

    def enemy_act(self, fighter):
        targets = self.attack_targets(fighter)
        if targets and fighter.action:
            self.start_attack(fighter, min(targets, key=lambda f: f.hp))
        else:
            self.wait_time = ENEMY_PAUSE

    # Selection and action bar ---------------------------------------------

    def actions(self):
        """Action bar entries for the selected fighter: (key, label, cost, enabled)."""
        fighter = self.selected
        return [
            ("move", "이동", fmt_m(fighter.moves_left), fighter.moves_left >= MIN_MOVE_M),
            ("attack", "공격", "행동", bool(fighter.action) and bool(self.attack_targets(fighter))),
            ("end", "턴 종료", "Space", True),
        ]

    def bottom_slots(self):
        """Hotbar slots in bar coordinates: (entry or None, (left, bottom, right, top))."""
        entries = [e for e in self.actions() if e[0] != "end"] if self.selected else []
        slots = []
        for index in range(SLOT_COLUMNS * SLOT_ROWS):
            column, row = index % SLOT_COLUMNS, SLOT_ROWS - 1 - index // SLOT_COLUMNS
            left = SLOTS_LEFT + column * (SLOT_SIZE + SLOT_GAP)
            bottom = SLOTS_BOTTOM + row * (SLOT_SIZE + SLOT_GAP)
            entry = entries[index] if index < len(entries) else None
            slots.append((entry, (left, bottom, left + SLOT_SIZE, bottom + SLOT_SIZE)))
        return slots

    def end_turn_rect(self):
        x, y = END_TURN_CENTER
        return x - END_TURN_RADIUS, y - END_TURN_RADIUS, x + END_TURN_RADIUS, y + END_TURN_RADIUS

    def button_rects(self):
        """Usable bar buttons (bar coordinates), including end turn."""
        if not self.is_player_turn():
            return []
        rects = [(entry, rect) for entry, rect in self.bottom_slots() if entry is not None]
        rects.append((("end", "턴 종료", "Space", True), self.end_turn_rect()))
        return rects

    def slot_at(self, x, y):
        for entry, (left, bottom, right, top) in self.bottom_slots():
            if left <= x <= right and bottom <= y <= top:
                return entry, (left, bottom, right, top)
        return None

    def click_bottom(self, x, y):
        if not self.is_player_turn():
            return
        cx, cy = END_TURN_CENTER
        if (x - cx) ** 2 + (y - cy) ** 2 <= END_TURN_RADIUS ** 2:
            self.choose_action("end")
            return
        hit = self.slot_at(x, y)
        if hit is not None and hit[0] is not None:
            self.choose_action(hit[0][0])

    def choose_action(self, kind):
        if not self.is_player_turn():
            return
        if kind == "end":
            self.end_turn()
            return
        if self.selected is None:
            self.log = "먼저 내 캐릭터를 클릭해 선택하세요."
            return
        entry = next(e for e in self.actions() if e[0] == kind)
        if not entry[3]:
            if kind == "move":
                self.log = "남은 이동 거리가 없습니다."
            elif not self.selected.action:
                self.log = "이번 턴의 행동을 이미 썼습니다."
            else:
                self.log = f"근접 거리({fmt_m(REACH_M)}) 안에 적이 없습니다. 먼저 다가가세요."
        else:
            self.mode = kind
            self.log = "갈 곳을 클릭하세요 · 우클릭 취소" if kind == "move" else "공격할 적을 클릭하세요 · 우클릭 취소"

    def right_click(self):
        if not self.is_player_turn():
            return
        if self.mode is not None:
            self.mode = None
            self.log = "행동을 고르세요"

    def log_header_rect(self):
        return LOG_RIGHT - LOG_WIDTH, LOG_TOP - LOG_HEADER, LOG_RIGHT, LOG_TOP

    def toggle_log(self):
        self.log_open = not self.log_open

    def click(self, screen_x, y):
        left, bottom, right, top = self.log_header_rect()
        if left <= screen_x <= right and bottom <= y <= top:
            self.toggle_log()
            return
        if not self.is_player_turn():
            return
        fighter = self.current
        clicked = self.fighter_under((screen_x, y))
        if clicked is fighter and self.mode is None:
            self.selected = fighter
            self.log = "행동을 고르세요 · 1 이동  2 공격  Space 턴 종료"
            return
        if clicked is not None and clicked.team != fighter.team:
            self.attack_or_approach(fighter, clicked)
            return
        if self.mode == "attack":
            self.log = "공격할 적을 클릭하세요 · 우클릭 취소"
        elif self.mode == "move":
            points = self.plan_move(fighter, (screen_x, y))
            if points:
                self.mode = None
                self.log = "행동을 고르세요"
                self.start_moving(fighter, points)
            else:
                self.log = "갈 수 없는 곳입니다 · 파란 영역 안을 클릭하세요"
        else:
            self.log = "아래 행동 막대에서 행동을 고르세요."

    def attack_or_approach(self, fighter, target):
        if not fighter.action:
            self.log = "자원이 충분하지 않음: 행동"
            return
        if self.in_reach(fighter.pos, target.pos):
            self.mode = None
            self.start_attack(fighter, target)
            return
        points = self.plan_approach(fighter, target)
        if points is None:
            self.log = "너무 멉니다 · 이번 턴에는 닿을 수 없습니다"
            return
        self.mode = None
        self.log = f"{target.name}에게 다가가 공격합니다"
        self.start_moving(fighter, points, then_attack=target)

    # Attacks --------------------------------------------------------------

    def start_attack(self, fighter, target, reaction=False):
        if not reaction:
            fighter.action = 0
        dx = target.unit.x - fighter.unit.x
        if abs(dx) > 1:
            fighter.unit.direction = 1 if dx > 0 else -1
        self.log = f"{fighter.name}의 공격 · 주사위를 굴립니다"
        # Roll up front: show the dice result first, then swing and apply it on contact.
        self.attack = {"attacker": fighter, "target": target, "resolved": False, "time": 0.0,
                       "reaction": reaction, "result": self.roll_attack(fighter, target),
                       "phase": "dice", "dice_time": 0.0, "landed": False}

    def roll_attack(self, attacker, target):
        roll = self.roll()
        total = roll + attacker.attack_bonus
        hit = roll == 20 or (roll != 1 and total >= target.armor_class)
        count, sides = attacker.damage_dice
        critical = roll == 20
        if critical:
            count *= 2
        damage_rolls = [self.roll(sides) for _ in range(count)] if hit else []
        return {
            "roll": roll, "total": total, "hit": hit, "critical": critical, "fumble": roll == 1,
            "damage_rolls": damage_rolls, "damage": sum(damage_rolls) + attacker.damage_bonus if hit else 0,
        }

    def start_swing(self, attack):
        fighter = attack["attacker"]
        if fighter.team == "party":
            attack["swing"] = BatSwing((fighter.unit.direction, 0))
        else:
            fighter.unit.transition("windup", WINDUP_TIME)

    def resolve_attack(self, attacker, target):
        self.attack["resolved"] = True
        result = self.attack["result"]
        x, y = target.unit.x, target.unit.y + 62
        kind = "기회 공격" if self.attack["reaction"] else "공격"
        roll_text = f"합 {result['total']}, 필요 {target.armor_class}"
        if not result["hit"]:
            label = "대실패" if result["fumble"] else "빗나감"
            self.record(f"{attacker.name} {kind}: {label} ({roll_text})", ui.MISS)
            self.popup(label, x, y, (181, 197, 209))
            self.log = f"{attacker.name}의 {kind}이 빗나갔습니다."
            return
        damage = result["damage"]
        target.hp = max(0, target.hp - damage)
        label = "치명타!" if result["critical"] else "명중"
        color = (255, 214, 127) if result["critical"] else (255, 160, 130)
        self.popup(f"{label} -{damage}", x, y, color)
        self.record(f"{attacker.name} {kind}: {label} ({roll_text})", color)
        self.record(f"  {target.name} 피해 {damage} · 체력 {target.hp}/{target.max_hp}", TEXT_COLOR)
        self.log = f"{attacker.name} {label}: {target.name}에게 피해 {damage}"
        self.effects.append(("impact", target.unit.x, target.unit.y))
        if not target.alive:
            self.defeat(target)

    def defeat(self, fighter):
        if fighter.team == "enemy":
            fighter.unit.transition("stunned")
            self.log = f"{fighter.name}을(를) 쓰러뜨렸습니다."
            self.record(f"{fighter.name} 쓰러짐", ui.ACCENT)
        if not self.living("enemy"):
            self.outcome = "victory"
            self.wait_time = VICTORY_PAUSE
            self.log = "승리! 모든 적을 쓰러뜨렸습니다."
            self.record("승리", ui.PARTY)
        elif not self.living("party"):
            self.outcome = "defeat"
            self.wait_time = VICTORY_PAUSE
            self.log = "주인공이 쓰러졌습니다."
            self.record("패배 · 주인공이 쓰러짐", ui.ENEMY)

    def update_attack(self, frame_time):
        attack = self.attack
        attacker, target = attack["attacker"], attack["target"]
        if attack["phase"] == "dice":
            attack["dice_time"] += frame_time
            if not attack["landed"] and attack["dice_time"] >= DICE_ROLL_TIME:
                attack["landed"] = True
                result = attack["result"]
                self.badges.append({
                    "unit": attacker.unit, "time": BADGE_TIME, "face": result["roll"],
                    "title": badge_label(result),
                    "detail": f"주사위 {result['roll']} + 명중 {attacker.attack_bonus} = {result['total']}"
                              f" · 필요 {target.armor_class}",
                    "color": badge_color(result),
                })
            if attack["dice_time"] >= DICE_ROLL_TIME + DICE_HOLD_TIME:
                attack["phase"] = "swing"
                self.start_swing(attack)
            return
        attack["time"] += frame_time
        if attacker.team == "party":
            swing = attack["swing"]
            if swing.update(frame_time):
                self.resolve_attack(attacker, target)
            if swing.elapsed >= BAT_DURATION:
                self.finish_attack()
            return
        zombie = attacker.unit
        if not attack["resolved"]:
            zombie.time_left = max(0.0, WINDUP_TIME - attack["time"])
            if attack["time"] >= WINDUP_TIME:
                attack["resolved"] = True
                zombie.transition("strike", STRIKE_TIME)
                self.resolve_attack(attacker, target)
            return
        zombie.time_left = max(0.0, zombie.time_left - frame_time)
        if not zombie.time_left:
            zombie.transition("idle")
            self.finish_attack()

    def finish_attack(self):
        attack = self.attack
        self.attack = None
        if not attack["reaction"]:
            if attack["attacker"].team == "enemy" and self.outcome is None:
                self.wait_time = ENEMY_PAUSE
            return
        # An opportunity attack interrupted a move: resume it unless the mover fell.
        mover = attack["target"]
        if self.moving is None or mover.alive:
            return
        self.moving = None
        if self.outcome is None and mover is self.current:
            self.wait_time = ENEMY_PAUSE

    # Frame update ---------------------------------------------------------

    def popup(self, text, x, y, color):
        self.popups.append([text, x, y, POPUP_TIME, color])

    def update(self, frame_time):
        self.banner_time = max(0.0, self.banner_time - frame_time)
        for popup in self.popups:
            popup[3] -= frame_time
        for badge in self.badges:
            badge["time"] -= frame_time
        self.badges = [b for b in self.badges if b["time"] > 0]
        self.popups = [p for p in self.popups if p[3] > 0]
        # An opportunity attack pauses the move it interrupted, so attacks go first.
        if self.attack is not None:
            self.update_attack(frame_time)
        elif self.moving is not None:
            self.update_moving(frame_time)
        elif self.wait_time:
            self.wait_time = max(0.0, self.wait_time - frame_time)
            if not self.wait_time and self.outcome is None:
                self.end_turn()

    def finished(self):
        return self.outcome is not None and not self.wait_time and self.attack is None

    # Drawing --------------------------------------------------------------

    def swing_for(self, unit):
        if self.attack is not None and self.attack["attacker"].unit is unit:
            return self.attack.get("swing")
        return None

    def draw_badges(self):
        """Small d20 badges over attackers: rolling first, then the landed result."""
        attack = self.attack
        if attack is not None and attack.get("phase") == "dice" and not attack["landed"]:
            tick = int(attack["dice_time"] / BADGE_FLICKER)
            if attack.get("tick") != tick:
                attack["tick"] = tick
                attack["face"] = self.dice_visual.randint(1, 20)
            target = attack["target"]
            chance = round(hit_chance(attack["attacker"].attack_bonus, target.armor_class) * 100)
            self.draw_badge(attack["attacker"].unit, attack["face"], f"명중 판정 {chance}%",
                            f"{target.armor_class} 이상이면 명중", ui.TEXT)
        for badge in self.badges:
            self.draw_badge(badge["unit"], badge["face"], badge["title"], badge["detail"], badge["color"])

    def draw_badge(self, unit, face, title, detail, color):
        """Two-line badge: the outcome in large text, the plain-language sum below."""
        x = unit.x - self.camera_x
        y = unit.y + 82
        icon = 32 if face is not None else 0
        width = icon + max(ui.text_width(title, 16), ui.text_width(detail, 13)) + 18
        left = max(4, min(WIDTH - 4 - width, x - width / 2))
        ui.panel(left, y - 19, left + width, y + 19, color)
        if face is not None:
            ui.d20_icon(left + 18, y, 13, face, color, 14)
        ui.text(left + icon + 9, y + 8, title, color, 16)
        ui.text(left + icon + 9, y - 9, detail, ui.MUTED, 13)

    def hovered_target(self):
        target = self.fighter_under(self.hover)
        if target is None or target.team == self.current.team:
            return None
        return target

    def foot_ring(self, fighter, color, scale=1.0, dashed=False):
        x, y = fighter.pos
        ui.ellipse(x - self.camera_x, y - 10, FOOT_RX * scale, FOOT_RY * scale, color, dashed=dashed)

    # Board layer (under the units) ----------------------------------------

    def draw(self):
        player_turn = self.is_player_turn()
        if player_turn and self.mode == "move":
            self.draw_reach_area()
        if player_turn and self.mode == "attack":
            x, y = self.current.pos
            # Melee reach drawn as a dashed ellipse in floor perspective.
            ui.ellipse(x - self.camera_x, y - 10, REACH_M * PX_PER_M_X, REACH_M * PX_PER_M_Y,
                       ui.DANGER, 40, dashed=True)
        for fighter in self.fighters:
            if not fighter.alive:
                continue
            color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
            active = fighter is self.current and self.outcome is None
            self.foot_ring(fighter, ui.ACCENT if active else color)
            if active:
                self.foot_ring(fighter, ui.ACCENT, 1.2)
        if player_turn:
            if self.mode == "attack":
                for enemy in self.attack_targets(self.current):
                    self.foot_ring(enemy, ui.DANGER, 1.35)
            hovered = self.hovered_target()
            if hovered is not None:
                self.foot_ring(hovered, ui.DANGER, 1.2)
            if self.mode == "move":
                self.draw_move_path()
            elif hovered is not None and self.current.action and not self.in_reach(self.current.pos, hovered.pos):
                points = self.plan_approach(self.current, hovered)
                if points:
                    screen = [(px - self.camera_x, py) for px, py in points]
                    for (x1, y1), (x2, y2) in zip(screen, screen[1:]):
                        pico2d.draw_line(x1, y1, x2, y2, *ui.ACCENT)
                    ui.ellipse(screen[-1][0], screen[-1][1] - 10, FOOT_RX, FOOT_RY, ui.ACCENT, dashed=True)

    def draw_reach_area(self):
        """BG3-like movement area: a soft fill with a brighter rim."""
        costs = self.search(self.current)
        if self._area_cache is None or self._area_cache[0] is not costs:
            self._area_cache = (costs, self.area_shapes(set(costs)))
        runs, rim = self._area_cache[1]
        for left, right, y in runs:
            pico2d.draw_rectangle(left - self.camera_x, y - NODE_Y / 2, right - self.camera_x, y + NODE_Y / 2 - 1,
                                  *ui.MOVE, 34, filled=True)
        for x, y in rim:
            pico2d.draw_rectangle(x - self.camera_x - 1, y - 1, x - self.camera_x + 1, y + 1, *ui.MOVE, filled=True)

    def area_shapes(self, nodes):
        """Merge reachable nodes into row runs for the fill and collect rim points."""
        runs, rim = [], []
        for row in sorted({r for _, r in nodes}):
            columns = sorted(c for c, r in nodes if r == row)
            start = previous = columns[0]
            for column in columns[1:] + [None]:
                if column is not None and column == previous + 1:
                    previous = column
                    continue
                left, y = self.nav.position((start, row))
                right, _ = self.nav.position((previous, row))
                runs.append((left - NODE_X / 2, right + NODE_X / 2 - 1, y))
                if column is not None:
                    start = previous = column
        for c, r in nodes:
            if any((c + dc, r + dr) not in nodes for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                rim.append(self.nav.position((c, r)))
        return runs, rim

    def draw_move_path(self):
        points = self.plan_move(self.current, self.hover)
        if not points:
            return
        danger = self.path_provokes(self.current, points)
        color = ui.DANGER if danger else ui.ACCENT
        screen = [(x - self.camera_x, y) for x, y in points]
        for (x1, y1), (x2, y2) in zip(screen, screen[1:]):
            pico2d.draw_line(x1, y1, x2, y2, *color)
            pico2d.draw_line(x1, y1 + 1, x2, y2 + 1, *color)
        end_x, end_y = screen[-1]
        ui.ellipse(end_x, end_y - 10, FOOT_RX, FOOT_RY, color)

    # Overlay layer (above the units) --------------------------------------

    def draw_overlay(self):
        for fighter in self.fighters:
            if fighter.alive:
                self.draw_health(fighter)
        self.draw_party_column()
        target = self.hovered_target() if self.is_player_turn() else None
        if target is None and self.attack is not None:
            target = self.attack["target"]
        if target is not None:
            self.draw_target_header(target)
        if self.is_player_turn():
            if target is not None and self.hovered_target() is not None:
                self.draw_hit_chip(self.current, target)
            elif self.mode == "move":
                self.draw_move_label()
        for text, x, y, time_left, color in self.popups:
            rise = (POPUP_TIME - time_left) * 22
            ui.text_center(x - self.camera_x, y + rise, text, color)
        self.draw_badges()
        if self.current.team == "party" and self.outcome is None:
            self.draw_resource_row()
        if self.is_player_turn():
            self.draw_slot_tooltip()
        self.draw_log()
        if self.banner_time:
            label = "기습! 전투 시작" if self.surprise else "발각! 전투 시작"
            width = ui.text_width(label, 20) + 48
            ui.panel(WIDTH / 2 - width / 2, 300, WIDTH / 2 + width / 2, 340, ui.ACCENT)
            ui.text_center(WIDTH / 2, 320, label, ui.ACCENT, 20)

    def draw_log(self):
        """Collapsible combat log in the top-right corner (click the header or press L)."""
        left, bottom, right, top = self.log_header_rect()
        mouse = self.hover
        hovered = mouse is not None and left <= mouse[0] <= right and bottom <= mouse[1] <= top
        ui.panel(left, bottom, right, top, ui.ACCENT if hovered else (120, 98, 60), ui.PANEL_RAISED, 235)
        # Open: triangle pointing down; folded: pointing right.
        tx, ty = left + 12, (bottom + top) / 2
        if self.log_open:
            pico2d.draw_line(tx - 5, ty + 3, tx + 5, ty + 3, *ui.ACCENT)
            pico2d.draw_line(tx - 5, ty + 3, tx, ty - 4, *ui.ACCENT)
            pico2d.draw_line(tx + 5, ty + 3, tx, ty - 4, *ui.ACCENT)
        else:
            pico2d.draw_line(tx - 3, ty + 5, tx - 3, ty - 5, *ui.ACCENT)
            pico2d.draw_line(tx - 3, ty + 5, tx + 4, ty, *ui.ACCENT)
            pico2d.draw_line(tx - 3, ty - 5, tx + 4, ty, *ui.ACCENT)
        ui.text(left + 24, ty, "전투 기록", ui.TEXT, 14)
        ui.text(right - 64, ty, "L 접기" if self.log_open else "L 펼치기", ui.DIM, 12)
        if not self.log_open:
            return
        lines = list(self.history)[-LOG_LINES:]
        height = LOG_LINE * len(lines) + 8
        ui.panel(left, bottom - height, right, bottom, (64, 80, 92), ui.PANEL, 215)
        for index, (line, color) in enumerate(lines):
            ui.text(left + 8, bottom - 12 - LOG_LINE * index, self.fit(line, LOG_WIDTH - 14, 12), color, 12)

    def fit(self, line, width, size):
        if ui.text_width(line, size) <= width:
            return line
        while line and ui.text_width(line + "…", size) > width:
            line = line[:-1]
        return line + "…"

    def draw_move_label(self):
        points = self.plan_move(self.current, self.hover)
        if not points:
            return
        x, y = points[-1]
        x -= self.camera_x
        danger = self.path_provokes(self.current, points)
        label = fmt_m(path_length(points)) + (" · 기회 공격 위험" if danger else "")
        color = ui.DANGER if danger else ui.ACCENT
        width = ui.text_width(label, 14) + 14
        ui.panel(x - width / 2, y + 22, x + width / 2, y + 42, color)
        ui.text_center(x, y + 32, label, color, 14)

    def draw_health(self, fighter):
        x = fighter.unit.x - self.camera_x
        y = fighter.unit.y + 52
        color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        ui.bar(x - 18, y, 36, 4, fighter.hp / fighter.max_hp, color)

    def draw_target_header(self, target):
        """BG3-style target readout under the turn order: name, big health bar, status."""
        color = ENEMY_COLOR if target.team == "enemy" else PARTY_COLOR
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
            chip = ui.text_width(label, 13) + 18
            pico2d.draw_circle(x + 6, top - 62, 5, *chip_color, filled=True)
            ui.text(x + 15, top - 62, label, ui.MUTED, 13)
            x += chip + 8

    def draw_hit_chip(self, attacker, target):
        """BG3-style hover readout: the chance to hit in large type, then damage and range."""
        x = target.unit.x - self.camera_x + 24
        y = target.unit.y + 30
        chance = round(hit_chance(attacker.attack_bonus, target.armor_class) * 100)
        low, high = attacker.damage_range()
        approach = None
        if not attacker.action:
            note, note_color = "자원이 충분하지 않음: 행동", ui.DANGER
        elif self.in_reach(attacker.pos, target.pos):
            note, note_color = "클릭하면 공격", ui.MUTED
        else:
            approach = self.plan_approach(attacker, target)
            if approach:
                note, note_color = f"{fmt_m(path_length(approach))} 이동 후 공격", ui.ACCENT
            else:
                note, note_color = f"닿지 않음 · 거리 {fmt_m(metres(attacker.pos, target.pos))}", ui.DANGER
        usable = bool(attacker.action) and (self.in_reach(attacker.pos, target.pos) or approach)
        big = f"{chance}%"
        detail = f"피해 {low}~{high} · 방어 {target.armor_class}"
        width = max(32 + ui.text_width(big, 24) + 6 + ui.text_width("명중 확률", 13),
                    ui.text_width(detail, 13), ui.text_width(note, 13)) + 20
        height = 70
        x = min(x, WIDTH - width - 4)
        border = ui.ACCENT if usable else ui.DIM
        ui.panel(x, y, x + width, y + height, border, ui.PANEL, 235)
        # Weapon glyph and the percentage, like BG3's cursor tooltip.
        for offset in (-1, 0, 1):
            pico2d.draw_line(x + 10 + offset, y + height - 30, x + 24 + offset, y + height - 12, 196, 160, 110)
        ui.text(x + 32, y + height - 20, big, ui.ACCENT if usable else ui.DIM, 24)
        ui.text(x + 32 + ui.text_width(big, 24) + 6, y + height - 24, "명중 확률", ui.MUTED, 13)
        ui.text(x + 10, y + 26, detail, ui.TEXT, 13)
        ui.text(x + 10, y + 10, note, note_color, 13)

    def draw_party_column(self):
        """Party portraits down the left edge with health, as in BG3."""
        top = HUD_BOTTOM - 14
        for fighter in self.fighters:
            if fighter.team != "party":
                continue
            active = fighter is self.current and self.outcome is None
            border = ui.ACCENT if active else (PARTY_COLOR if fighter.alive else ui.DIM)
            left, bottom = 8, top - 66
            pico2d.draw_rectangle(left - 2, bottom - 2, left + 54, top + 2, *ui.PANEL, 220, filled=True)
            self.draw_portrait(fighter, left, bottom, 52, 66, border)
            label = f"{fighter.hp}/{fighter.max_hp}"
            ui.panel(left + 4, bottom + 2, left + 48, bottom + 18, border, ui.PANEL, 230)
            ui.text_center(left + 26, bottom + 10, label, ui.TEXT, 12)
            top = bottom - 10

    def draw_portrait(self, fighter, left, bottom, width, height, color):
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

    # Top HUD strip: turn order portraits ----------------------------------

    def draw_hud(self):
        ui.panel(0, HUD_BOTTOM, WIDTH - 1, HUD_TOP - 1, ui.BORDER, ui.PANEL, 255)
        pico2d.draw_line(0, HUD_BOTTOM + 1, WIDTH, HUD_BOTTOM + 1, 120, 98, 60)
        ui.text(14, HUD_BOTTOM + 40, f"{self.round}라운드", ui.ACCENT, 16)
        ui.text(14, HUD_BOTTOM + 18, "선공 1d4 + 민첩", ui.DIM, 12)
        size, gap = 46, 6
        count = len(self.order)
        left = WIDTH / 2 - (count * size + (count - 1) * gap) / 2
        for index, fighter in enumerate(self.order):
            x = left + index * (size + gap)
            current = index == self.turn_index and self.outcome is None
            team_color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
            border = ui.ACCENT if current else (team_color if fighter.alive else ui.DIM)
            bottom = HUD_BOTTOM + 8
            self.draw_portrait(fighter, x, bottom, size, 50, border)
            if current:
                pico2d.draw_rectangle(x - 2, bottom - 2, x + size + 2, bottom + 52, *ui.ACCENT)
            ui.bar(x + 3, bottom + 3, size - 6, 4, fighter.hp / fighter.max_hp, team_color)
            ui.text(x + size - 12, bottom + 42, str(fighter.initiative), ui.MUTED, 11)
            if fighter.surprised:
                ui.text_center(x + size / 2, bottom + 25, "기습", ui.DANGER, 12)
        if self.log:
            ui.text(left + count * (size + gap) + 20, HUD_BOTTOM + 32, self.log, ui.MUTED, 13)

    # Bottom hotbar ----------------------------------------------------------

    def draw_bottom(self):
        """BG3-style hotbar: round portrait, weapon, action slots, round end-turn button."""
        ui.panel(0, 0, WIDTH - 1, BAR_HEIGHT - 1, ui.BORDER, ui.PANEL, 255)
        pico2d.draw_line(0, BAR_HEIGHT - 2, WIDTH, BAR_HEIGHT - 2, 120, 98, 60)
        fighter = self.current
        self.draw_round_portrait(fighter)
        self.draw_weapon_slot(fighter)
        player_turn = self.is_player_turn()
        mouse = self.hover_bottom
        for entry, (left, bottom, right, top) in self.bottom_slots():
            hovered = mouse is not None and left <= mouse[0] <= right and bottom <= mouse[1] <= top
            self.draw_slot(entry, left, bottom, right, top, hovered and player_turn)
        self.draw_end_turn(player_turn)

    def draw_round_portrait(self, fighter):
        x, y = PORTRAIT_CENTER
        team_color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        pico2d.draw_circle(x, y, PORTRAIT_RADIUS, 24, 32, 40, filled=True)
        clip = getattr(fighter.unit, "portrait_clip", None)
        if clip is not None:
            image, sx, sy, sw, sh = clip()
            size = PORTRAIT_RADIUS * 1.35
            scale = size / max(sw, sh)
            image.clip_draw(sx, sy, sw, sh, x, y + 6, sw * scale, sh * scale)
        # Lost health fills the circle from below in red, as in BG3.
        lost = 1 - fighter.hp / fighter.max_hp
        if lost:
            height = 2 * PORTRAIT_RADIUS * lost
            pico2d.draw_rectangle(x - PORTRAIT_RADIUS + 8, y - PORTRAIT_RADIUS + 4,
                                  x + PORTRAIT_RADIUS - 8, y - PORTRAIT_RADIUS + 4 + height,
                                  170, 40, 40, 110, filled=True)
        ui.ring(x, y, PORTRAIT_RADIUS, team_color, 3)
        ui.ring(x, y, PORTRAIT_RADIUS + 3, (120, 98, 60), 1)
        label = f"{fighter.hp}/{fighter.max_hp}"
        width = ui.text_width(label, 14) + 12
        ui.panel(x - width / 2, y - PORTRAIT_RADIUS - 2, x + width / 2, y - PORTRAIT_RADIUS + 16, team_color)
        ui.text_center(x, y - PORTRAIT_RADIUS + 7, label, ui.TEXT, 14)

    def draw_weapon_slot(self, fighter):
        left, bottom, right, top = 112, 30, 160, 78
        ui.panel(left, bottom, right, top, ui.BORDER_LIGHT, ui.PANEL_RAISED, 255)
        # A simple baseball-bat glyph.
        for offset in (-1, 0, 1):
            pico2d.draw_line(left + 12 + offset, bottom + 10, right - 12 + offset, top - 10, 196, 160, 110)
        pico2d.draw_line(left + 10, bottom + 8, left + 16, bottom + 14, 90, 70, 50)
        ui.text_center((left + right) / 2, bottom - 10, "방망이", ui.MUTED, 12)

    def draw_slot(self, entry, left, bottom, right, top, hovered):
        if entry is None:
            ui.panel(left, bottom, right, top, (44, 54, 62), (20, 27, 34), 255)
            return
        kind, label, cost, enabled = entry
        chosen = kind == self.mode
        if chosen:
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
        mouse = self.hover_bottom
        hovered = mouse is not None and (mouse[0] - x) ** 2 + (mouse[1] - y) ** 2 <= END_TURN_RADIUS ** 2
        pico2d.draw_circle(x, y, END_TURN_RADIUS, 22, 44, 58, filled=True)
        ring_color = ui.ACCENT if hovered and enabled else ((96, 170, 190) if enabled else ui.DIM)
        ui.ring(x, y, END_TURN_RADIUS, ring_color, 4)
        ui.ring(x, y, END_TURN_RADIUS + 3, (120, 98, 60), 1)
        ui.text_center(x, y + 6, "턴 종료", ui.TEXT if enabled else ui.DIM)
        ui.text_center(x, y - 14, "Space", ui.MUTED if enabled else ui.DIM, 12)

    def draw_resource_row(self):
        """Resource icons with names above the hotbar (drawn in the world, under the floor)."""
        fighter = self.selected or self.current
        x = 238
        y = 13
        ui.panel(x - 12, y - 11, x + 404, y + 11, ui.BORDER, ui.PANEL, 210)
        ui.action_icon(x, y, 6, bool(fighter.action))
        ui.text(x + 10, y, "행동", ui.TEXT if fighter.action else ui.DIM, 12)
        ui.bonus_icon(x + 52, y, 7, bool(fighter.bonus_action))
        ui.text(x + 62, y, "보조", ui.TEXT if fighter.bonus_action else ui.DIM, 12)
        ui.reaction_icon(x + 104, y, 7, bool(fighter.reaction))
        ui.text(x + 114, y, "반응", ui.TEXT if fighter.reaction else ui.DIM, 12)
        total = max(0.1, fighter.move_m)
        cost = 0.0
        if self.is_player_turn() and self.mode == "move":
            points = self.plan_move(fighter, self.hover)
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

    def draw_slot_tooltip(self):
        """Tooltip above a hovered hotbar slot, drawn in world coordinates."""
        if self.hover_bottom is None:
            return
        hit = self.slot_at(*self.hover_bottom)
        if hit is None or hit[0] is None:
            return
        (kind, label, cost, enabled), (left, _, right, _) = hit
        if kind == "move":
            lines = [f"이동 · 남은 거리 {fmt_m(self.selected.moves_left)}", "원하는 곳을 클릭해 걸어갑니다"]
        else:
            lines = ["근접 공격 · 행동 1", f"{fmt_m(REACH_M)} 안의 적을 방망이로 칩니다"]
        if not enabled:
            reason = "남은 이동 거리가 없음" if kind == "move" else (
                "자원이 충분하지 않음: 행동" if not self.selected.action else "근접 거리에 적이 없음")
            lines.append(reason)
        width = max(ui.text_width(line, 13) for line in lines) + 18
        height = 18 * len(lines) + 10
        x = max(4, min(WIDTH - width - 4, (left + right) / 2 - width / 2))
        bottom = 30
        ui.panel(x, bottom, x + width, bottom + height, ui.BORDER_LIGHT, ui.PANEL, 240)
        for index, line in enumerate(lines):
            color = ui.TEXT if index == 0 else (ui.DANGER if not enabled and index == len(lines) - 1 else ui.MUTED)
            ui.text(x + 9, bottom + height - 14 - 18 * index, line, color, 13)
