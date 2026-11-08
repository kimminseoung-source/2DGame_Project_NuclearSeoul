"""Turn-based combat on the street floor with free, metre-based movement (BG3 style)."""

import random
from collections import deque

import ui
from bat import BAT_DURATION, BatSwing
from nav import PX_PER_M_Y, NavField, metres, path_length, point_along, truncate
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
# The hit reel spins, slows down and stops on the result, holds briefly, and only then
# the swing starts. The player's own rolls spin longer: that wait is where the tension is.
DICE_ROLL_TIME = 1.5
ENEMY_ROLL_TIME = 0.8
DICE_HOLD_TIME = 0.55
# The landed hit gauge stays until the swing connects; then the damage roll shows.
HIT_GAUGE_TIME = DICE_HOLD_TIME + 0.2
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
        # Records for the dice views: one per hit roll, one per damage roll.
        self.hit_rolls = []
        self.damage_rolls = []
        self.effects = []
        self.outcome = None
        self.selected = None
        self.mode = None
        self.dice_visual = random.Random()
        self.skip_spin = False      # settings: stop the hit wheel at once (result is still shown)
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

    def living_foes(self, fighter):
        return self.living("enemy" if fighter.team == "party" else "party")

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
            ("attack", "공격", "행동", bool(fighter.action) and bool(self.living_foes(fighter))),
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
                self.log = "공격할 적이 없습니다."
        else:
            self.mode = kind
            self.log = ("갈 곳을 클릭하세요 · 우클릭 취소" if kind == "move"
                        else "공격할 적을 클릭하세요 · 멀면 다가가서 공격 · 우클릭 취소")

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
                       "phase": "dice", "dice_time": 0.0, "landed": False,
                       "roll_time": self.roll_time(fighter)}

    def roll_time(self, fighter):
        """How long the hit wheel spins before it stops on the result."""
        if self.skip_spin:
            return 0.0
        return DICE_ROLL_TIME if fighter.team == "party" else ENEMY_ROLL_TIME

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
            self.log = f"{attacker.name}의 {kind}이 빗나갔습니다."
            return
        damage = result["damage"]
        target.hp = max(0, target.hp - damage)
        label = "치명타!" if result["critical"] else "명중"
        color = (255, 214, 127) if result["critical"] else (255, 160, 130)
        # The damage roll is a second, separate roll: d6 (twice on a critical) + bonus.
        self.damage_rolls.append({
            "target": target, "time": BADGE_TIME, "rolls": list(result["damage_rolls"]),
            "bonus": attacker.damage_bonus, "sides": attacker.damage_dice[1],
            "damage": damage, "critical": result["critical"],
        })
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
            if not attack["landed"] and attack["dice_time"] >= attack["roll_time"]:
                attack["landed"] = True
                result = attack["result"]
                self.hit_rolls.append({
                    "attacker": attacker, "target": target, "result": result, "time": HIT_GAUGE_TIME,
                })
            if attack["dice_time"] >= attack["roll_time"] + DICE_HOLD_TIME:
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
        for records in (self.badges, self.hit_rolls, self.damage_rolls):
            for record in records:
                record["time"] -= frame_time
            records[:] = [r for r in records if r["time"] > 0]
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

    # Queries for the view objects ---------------------------------------------

    def swing_for(self, unit):
        if self.attack is not None and self.attack["attacker"].unit is unit:
            return self.attack.get("swing")
        return None

    def hovered_target(self):
        target = self.fighter_under(self.hover)
        if target is None or target.team == self.current.team:
            return None
        return target
