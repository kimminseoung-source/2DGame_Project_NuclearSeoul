"""Turn-based combat board laid over the street floor."""

import random
from collections import deque
from math import floor

import pico2d

import ui

from bat import BAT_DURATION, BatSwing
from tile_map import FLOOR_BOTTOM, FLOOR_TOP, HEIGHT, WIDTH
from zombie import STRIKE_TIME, WINDUP_TIME


COLUMNS = 15
ROWS = 4
CELL_WIDTH = 48
ROW_HEIGHT = (FLOOR_TOP - FLOOR_BOTTOM) / ROWS
BOARD_LEFT = (WIDTH - COLUMNS * CELL_WIDTH) / 2
FLOOR_MIDDLE = (FLOOR_BOTTOM + FLOOR_TOP) / 2
# Horizontal shift per pixel of depth. Farther rows lean left so the cells
# read as parallelograms on the street instead of flat boxes.
SKEW = 0.32
STAND_CLEARANCE = 8
BANNER_TIME = 1.4
MOVE_SPEED = 150
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
# The combat hotbar replaces the exploration HUD strip at the top of the window.
HUD_BOTTOM = HEIGHT
HUD_TOP = HEIGHT + 64
SLOT_SIZE = 50
SLOT_GAP = 8
SLOTS_LEFT = 352
END_TURN_RECT = (650, HUD_BOTTOM + 7, 760, HUD_TOP - 7)
CARD_WIDTH = 122
CARD_HEIGHT = 52
CARD_GAP = 8
CARDS_TOP = HEIGHT - 8

GRID_COLOR = (74, 92, 104)
REACH_COLOR = ui.MOVE
HOVER_COLOR = ui.ACCENT
PARTY_COLOR = ui.PARTY
ENEMY_COLOR = ui.ENEMY
TARGET_COLOR = ui.DANGER
TEXT_COLOR = ui.TEXT
NEIGHBOURS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def skew_at(y):
    return (FLOOR_MIDDLE - y) * SKEW


def chebyshev(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def hit_chance(attack_bonus, armor_class):
    """Chance that d20 + bonus meets the armour class; 1 misses, 20 hits."""
    hits = sum(1 for roll in range(2, 20) if roll + attack_bonus >= armor_class) + 1
    return hits / 20


class CombatGrid:
    """A slanted board fixed to the screen area where combat started."""

    def __init__(self, camera_x, tile_map):
        self.camera_x = camera_x
        self.tile_map = tile_map

    def cell_center(self, column, row):
        y = FLOOR_BOTTOM + ROW_HEIGHT * row + ROW_HEIGHT / 2
        x = self.camera_x + BOARD_LEFT + CELL_WIDTH * column + CELL_WIDTH / 2 + skew_at(y)
        return x, y

    def corners(self, column, row):
        bottom = FLOOR_BOTTOM + ROW_HEIGHT * row
        top = bottom + ROW_HEIGHT
        left = self.camera_x + BOARD_LEFT + CELL_WIDTH * column
        right = left + CELL_WIDTH
        return (
            (left + skew_at(bottom), bottom), (right + skew_at(bottom), bottom),
            (right + skew_at(top), top), (left + skew_at(top), top),
        )

    def cell_at(self, screen_x, y):
        """Return the cell under a screen point, or None outside the board."""
        row = floor((y - FLOOR_BOTTOM) / ROW_HEIGHT)
        column = floor((screen_x - BOARD_LEFT - skew_at(y)) / CELL_WIDTH)
        return (column, row) if self.in_bounds(column, row) else None

    def in_bounds(self, column, row):
        return 0 <= column < COLUMNS and 0 <= row < ROWS

    def blocked(self, column, row):
        # Use the same floor and wreck collision as exploration.
        return not self.tile_map.can_stand(*self.cell_center(column, row), STAND_CLEARANCE)

    def nearest_free_cell(self, x, y, taken=()):
        cells = [
            (column, row)
            for column in range(COLUMNS)
            for row in range(ROWS)
            if not self.blocked(column, row) and (column, row) not in taken
        ]

        def distance(cell):
            cx, cy = self.cell_center(*cell)
            return (cx - x) ** 2 + (cy - y) ** 2

        return min(cells, key=distance)

    def paths_from(self, start, occupied, limit=None):
        """Shortest step paths to every reachable cell (8 directions)."""
        paths = {start: []}
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            if limit is not None and len(paths[cell]) >= limit:
                continue
            for dx, dy in NEIGHBOURS:
                step = cell[0] + dx, cell[1] + dy
                if step in paths or not self.walkable(step, occupied):
                    continue
                # Do not cut diagonally past the corner of an obstacle.
                if dx and dy and not (self.walkable((cell[0] + dx, cell[1]), occupied)
                                      and self.walkable((cell[0], cell[1] + dy), occupied)):
                    continue
                paths[step] = paths[cell] + [step]
                queue.append(step)
        del paths[start]
        return paths

    def walkable(self, cell, occupied):
        return self.in_bounds(*cell) and not self.blocked(*cell) and cell not in occupied

    def draw(self, highlights):
        for column in range(COLUMNS):
            for row in range(ROWS):
                points = [(x - self.camera_x, y) for x, y in self.corners(column, row)]
                if self.blocked(column, row):
                    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = points
                    pico2d.draw_line(x1 + 6, y1 + 3, x3 - 6, y3 - 3, 120, 96, 82)
                    pico2d.draw_line(x2 - 6, y2 + 3, x4 + 6, y4 - 3, 120, 96, 82)
                    continue
                draw_cell(points, highlights.get((column, row), GRID_COLOR))


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


def draw_cell(points, color, inset_x=0.06, inset_y=0.12):
    # Inset each cell slightly so neighbouring outlines do not merge.
    cx = sum(x for x, _ in points) / 4
    cy = sum(y for _, y in points) / 4
    inset = [(x + (cx - x) * inset_x, y + (cy - y) * inset_y) for x, y in points]
    for (x1, y1), (x2, y2) in zip(inset, inset[1:] + inset[:1]):
        pico2d.draw_line(x1, y1, x2, y2, *color)


class Fighter:
    """Turn data and combat stats for one unit on the board."""

    def __init__(self, unit, name, team, *, dexterity, move_cells, max_hp,
                 armor_class, attack_bonus, damage_dice, damage_bonus, hp=None):
        self.unit = unit
        self.name = name
        self.team = team
        self.dexterity = dexterity
        self.move_cells = move_cells
        self.max_hp = max_hp
        self.hp = max_hp if hp is None else hp
        self.armor_class = armor_class
        self.attack_bonus = attack_bonus
        self.damage_dice = damage_dice  # (count, sides)
        self.damage_bonus = damage_bonus
        self.cell = None
        self.initiative = 0
        self.initiative_roll = 0
        self.surprised = False
        self.moves_left = 0
        self.action = 0
        self.bonus_action = 0
        # One reaction per round, refreshed at the start of the fighter's turn.
        self.reaction = 1

    @property
    def alive(self):
        return self.hp > 0

    def damage_range(self):
        count, sides = self.damage_dice
        return count + self.damage_bonus, count * sides + self.damage_bonus


class Combat:
    """Board, initiative order and the turn currently being played."""

    def __init__(self, camera_x, tile_map, fighters, surprise, rng=None):
        self.grid = CombatGrid(camera_x, tile_map)
        self.surprise = surprise
        self.rng = rng or random.Random()
        self.banner_time = BANNER_TIME
        self.fighters = fighters
        taken = []
        for fighter in fighters:
            fighter.cell = self.grid.nearest_free_cell(fighter.unit.x, fighter.unit.y, taken)
            taken.append(fighter.cell)
            fighter.unit.x, fighter.unit.y = self.grid.cell_center(*fighter.cell)
            fighter.surprised = surprise and fighter.team == "enemy"
        self.roll_initiative()
        self.round = 1
        self.turn_index = 0
        self.hover = None
        self.hover_screen = None
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
        # Small result badges over each fighter, starting with the initiative roll.
        self.badges = [
            {"unit": f.unit, "time": BADGE_TIME + 0.6, "face": None, "color": (181, 197, 209),
             "title": f"선공 {f.initiative}",
             "detail": f"주사위 {f.initiative_roll} + 민첩 {f.dexterity}"}
            for f in self.fighters
        ]
        self.start_turn()


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
        fighter.moves_left = fighter.move_cells
        fighter.action = 1
        fighter.bonus_action = 1
        fighter.reaction = 1
        self.selected = None
        self.mode = None
        if fighter.surprised:
            self.log = f"{fighter.name}: 기습당해 이번 라운드에 행동하지 못합니다."
            self.wait_time = SKIP_PAUSE
            return
        if fighter.team == "enemy":
            self.log = f"{fighter.name}의 턴"
            self.enemy_approach(fighter)
        else:
            self.log = f"{fighter.name}의 턴 · 캐릭터를 클릭해 선택하세요"

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

    # Movement -------------------------------------------------------------

    def occupied(self, ignore=None):
        return {f.cell for f in self.fighters if f is not ignore and f.alive}

    def reachable(self, fighter):
        return self.grid.paths_from(fighter.cell, self.occupied(fighter), fighter.moves_left)

    def fighter_at(self, cell):
        return next((f for f in self.fighters if f.cell == cell and f.alive), None)

    # Selection and action bar ---------------------------------------------

    def actions(self):
        """Action bar entries for the selected fighter: (key, label, cost, enabled)."""
        fighter = self.selected
        return [
            ("move", "이동", f"{fighter.moves_left}칸", fighter.moves_left > 0),
            ("attack", "공격", "행동", bool(fighter.action) and bool(self.attack_targets(fighter))),
            ("end", "턴 종료", "Space", True),
        ]

    def button_rects(self):
        """Clickable hotbar slots in the top HUD strip, plus the end-turn button."""
        if not self.is_player_turn():
            return []
        rects = []
        if self.selected is not None:
            for index, entry in enumerate(e for e in self.actions() if e[0] != "end"):
                left = SLOTS_LEFT + index * (SLOT_SIZE + SLOT_GAP)
                rects.append((entry, (left, HUD_BOTTOM + 7, left + SLOT_SIZE, HUD_BOTTOM + 7 + SLOT_SIZE)))
        end_entry = next(e for e in self.actions() if e[0] == "end") if self.selected else ("end", "턴 종료", "Space", True)
        rects.append((end_entry, END_TURN_RECT))
        return rects

    def attack_targets(self, fighter):
        return [f for f in self.living("enemy" if fighter.team == "party" else "party")
                if chebyshev(f.cell, fighter.cell) <= 1]

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
                self.log = "남은 이동 칸이 없습니다."
            elif not self.selected.action:
                self.log = "이번 턴의 행동을 이미 썼습니다."
            else:
                self.log = "옆 칸에 공격할 적이 없습니다. 먼저 다가가세요."
        else:
            self.mode = kind
            self.log = "이동할 칸을 클릭하세요 · 우클릭 취소" if kind == "move" else "공격할 적을 클릭하세요 · 우클릭 취소"

    def right_click(self):
        if not self.is_player_turn():
            return
        if self.mode is not None:
            self.mode = None
            self.log = "행동을 고르세요"
        elif self.selected is not None:
            self.selected = None
            self.log = f"{self.current.name}의 턴 · 캐릭터를 클릭해 선택하세요"

    def click(self, screen_x, y):
        if not self.is_player_turn():
            return
        for (kind, *_), (left, bottom, right, top) in self.button_rects():
            if left <= screen_x <= right and bottom <= y <= top:
                self.choose_action(kind)
                return
        cell = self.grid.cell_at(screen_x, y)
        clicked = self.fighter_at(cell)
        fighter = self.current
        if clicked is fighter:
            self.selected = fighter
            self.mode = None
            self.log = "행동을 고르세요 · 1 이동  2 공격  Space 턴 종료"
            return
        if self.selected is None:
            self.log = "먼저 내 캐릭터를 클릭해 선택하세요."
            return
        if self.mode == "attack":
            if clicked is not None and clicked in self.attack_targets(fighter):
                self.mode = None
                self.start_attack(fighter, clicked)
            else:
                self.log = "옆 칸의 적을 클릭하세요 · 우클릭 취소"
        elif self.mode == "move":
            path = self.reachable(fighter).get(cell)
            if path:
                fighter.moves_left -= len(path)
                self.mode = None
                self.log = "행동을 고르세요"
                self.start_moving(fighter, path)
        else:
            self.log = "아래 행동 막대에서 행동을 고르세요."

    def start_moving(self, fighter, path):
        self.moving = {"fighter": fighter, "path": list(path), "from": fighter.cell}
        fighter.cell = path[-1]
        if fighter.team == "enemy":
            fighter.unit.transition("chase")
        self.check_provoke()

    def can_react(self, reactor, mover):
        return (reactor.alive and reactor.team != mover.team and reactor.reaction
                and not reactor.surprised)

    def provokers(self, mover, from_cell, to_cell):
        """Enemies whose reach the mover leaves by stepping from one cell to the next."""
        return [
            f for f in self.fighters
            if self.can_react(f, mover)
            and chebyshev(f.cell, from_cell) <= 1 < chebyshev(f.cell, to_cell)
        ]

    def path_provokes(self, mover, path):
        previous = mover.cell
        for step in path:
            if self.provokers(mover, previous, step):
                return True
            previous = step
        return False

    def check_provoke(self):
        """Pause the move for an opportunity attack before leaving reach."""
        move = self.moving
        mover = move["fighter"]
        reactors = self.provokers(mover, move["from"], move["path"][0])
        if not reactors:
            return
        reactor = reactors[0]
        reactor.reaction = 0
        self.popup("기회 공격!", reactor.unit.x, reactor.unit.y + 96, (255, 214, 127))
        self.start_attack(reactor, mover, reaction=True)

    def enemy_approach(self, fighter):
        targets = self.living("party")
        target = min(targets, key=lambda f: chebyshev(f.cell, fighter.cell))
        if chebyshev(target.cell, fighter.cell) <= 1:
            self.enemy_act(fighter)
            return
        paths = self.grid.paths_from(fighter.cell, self.occupied(fighter))
        goals = [path for cell, path in paths.items() if chebyshev(cell, target.cell) == 1]
        if not goals:
            self.wait_time = ENEMY_PAUSE
            return
        path = min(goals, key=len)[:fighter.move_cells]
        fighter.moves_left -= len(path)
        self.start_moving(fighter, path)

    def enemy_act(self, fighter):
        targets = [f for f in self.living("party") if chebyshev(f.cell, fighter.cell) <= 1]
        if targets and fighter.action:
            self.start_attack(fighter, min(targets, key=lambda f: f.hp))
        else:
            self.wait_time = ENEMY_PAUSE

    def update_moving(self, frame_time):
        fighter, path = self.moving["fighter"], self.moving["path"]
        unit = fighter.unit
        target_x, target_y = self.grid.cell_center(*path[0])
        dx, dy = target_x - unit.x, target_y - unit.y
        distance = (dx * dx + dy * dy) ** 0.5
        step = MOVE_SPEED * frame_time
        if abs(dx) > 1:
            unit.direction = 1 if dx > 0 else -1
        unit.walk_time += frame_time
        if distance > step:
            unit.x += dx / distance * step
            unit.y += dy / distance * step
            return
        unit.x, unit.y = target_x, target_y
        self.moving["from"] = path.pop(0)
        if path:
            self.check_provoke()
            return
        self.moving = None
        unit.walk_time = 0.0
        if fighter.team == "enemy":
            unit.transition("idle")
            self.enemy_act(fighter)

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
        if not result["hit"]:
            label = "대실패" if result["fumble"] else "빗나감"
            self.popup(label, x, y, (181, 197, 209))
            self.log = f"{attacker.name}의 {kind}이 빗나갔습니다."
            return
        damage = result["damage"]
        target.hp = max(0, target.hp - damage)
        label = "치명타!" if result["critical"] else "명중"
        color = (255, 214, 127) if result["critical"] else (255, 160, 130)
        self.popup(f"{label} -{damage}", x, y, color)
        rolls = "+".join(map(str, result["damage_rolls"]))
        count, sides = attacker.damage_dice
        if result["critical"]:
            count *= 2
        self.log = f"{attacker.name} {label}: {target.name}에게 피해 {damage}"
        self.effects.append(("impact", target.unit.x, target.unit.y))
        if not target.alive:
            self.defeat(target)

    def defeat(self, fighter):
        if fighter.team == "enemy":
            fighter.unit.transition("stunned")
            self.log = f"{fighter.name}을(를) 쓰러뜨렸습니다."
        if not self.living("enemy"):
            self.outcome = "victory"
            self.wait_time = VICTORY_PAUSE
            self.log = "승리! 모든 적을 쓰러뜨렸습니다."
        elif not self.living("party"):
            self.outcome = "defeat"
            self.wait_time = VICTORY_PAUSE
            self.log = "주인공이 쓰러졌습니다."

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
        mover.cell = self.moving["from"]
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
            self.draw_badge(attack["attacker"].unit, attack["face"], "명중 판정",
                            f"{target.armor_class} 이상이면 명중", ui.TEXT)
        for badge in self.badges:
            self.draw_badge(badge["unit"], badge["face"], badge["title"], badge["detail"], badge["color"])

    def draw_badge(self, unit, face, title, detail, color):
        """Two-line badge: the outcome in large text, the plain-language sum below."""
        x = unit.x - self.grid.camera_x
        y = unit.y + 82
        icon = 32 if face is not None else 0
        width = icon + max(ui.text_width(title, 16), ui.text_width(detail, 13)) + 18
        left, right = x - width / 2, x + width / 2
        left, right = max(4, left), max(4, left) + width
        if right > WIDTH - 4:
            left, right = WIDTH - 4 - width, WIDTH - 4
        ui.panel(left, y - 19, right, y + 19, color)
        if face is not None:
            ui.d20_icon(left + 18, y, 13, face, color, 14)
        ui.text(left + icon + 9, y + 8, title, color, 16)
        ui.text(left + icon + 9, y - 9, detail, ui.MUTED, 13)

    def hovered_target(self):
        target = self.fighter_at(self.hover)
        if target is None or target.team == self.current.team:
            return None
        return target

    def outline(self, cell, color):
        corners = self.grid.corners(*cell)
        draw_cell([(x - self.grid.camera_x, y) for x, y in corners], color, 0.0, 0.0)

    # Board layer (under the units) ----------------------------------------

    def draw(self):
        highlights = {}
        player_turn = self.is_player_turn()
        if player_turn and self.mode == "move":
            for cell in self.reachable(self.current):
                highlights[cell] = REACH_COLOR
            if self.hover in highlights:
                highlights[self.hover] = HOVER_COLOR
        for fighter in self.fighters:
            if fighter.alive:
                highlights[fighter.cell] = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        self.grid.draw(highlights)
        if player_turn:
            if self.mode == "attack":
                for enemy in self.attack_targets(self.current):
                    self.outline(enemy.cell, TARGET_COLOR)
            if self.selected is not None:
                self.outline(self.selected.cell, HOVER_COLOR)
            elif self.hover == self.current.cell:
                self.outline(self.current.cell, (200, 230, 210))
            if self.mode == "move":
                self.draw_move_path()

    def draw_move_path(self):
        path = self.reachable(self.current).get(self.hover)
        if not path:
            return
        danger = self.path_provokes(self.current, path)
        color = ui.DANGER if danger else ui.ACCENT
        points = [self.grid.cell_center(*cell) for cell in [self.current.cell] + path]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            pico2d.draw_line(x1 - self.grid.camera_x, y1, x2 - self.grid.camera_x, y2, *color)
        for x, y in points[1:-1]:
            pico2d.draw_circle(x - self.grid.camera_x, y, 2, *color, filled=True)

    # Overlay layer (above the units) --------------------------------------

    def draw_overlay(self):
        for fighter in self.fighters:
            if fighter.alive:
                self.draw_health(fighter)
        self.draw_turn_order()
        if self.is_player_turn():
            target = self.hovered_target()
            if target is not None:
                self.draw_target_panel(self.current, target)
            elif self.mode == "move":
                self.draw_move_label()
        for text, x, y, time_left, color in self.popups:
            rise = (POPUP_TIME - time_left) * 22
            ui.text_center(x - self.grid.camera_x, y + rise, text, color)
        self.draw_badges()
        if self.log:
            y = CARDS_TOP - CARD_HEIGHT - 24
            width = ui.text_width(self.log, 14) + 20
            ui.panel(WIDTH / 2 - width / 2, y - 11, WIDTH / 2 + width / 2, y + 11, ui.BORDER, ui.PANEL, 170)
            ui.text_center(WIDTH / 2, y, self.log, ui.TEXT, 14)
        if self.banner_time:
            label = "기습! 전투 시작" if self.surprise else "발각! 전투 시작"
            width = ui.text_width(label, 20) + 48
            ui.panel(WIDTH / 2 - width / 2, 300, WIDTH / 2 + width / 2, 340, ui.ACCENT)
            ui.text_center(WIDTH / 2, 320, label, ui.ACCENT, 20)

    def draw_move_label(self):
        path = self.reachable(self.current).get(self.hover)
        if not path:
            return
        x, y = self.grid.cell_center(*self.hover)
        x -= self.grid.camera_x
        danger = self.path_provokes(self.current, path)
        label = f"{len(path)}칸" + (" · 기회 공격 위험" if danger else "")
        color = ui.DANGER if danger else ui.ACCENT
        width = ui.text_width(label, 14) + 14
        ui.panel(x - width / 2, y + 22, x + width / 2, y + 42, color)
        ui.text_center(x, y + 32, label, color, 14)

    def draw_health(self, fighter):
        x = fighter.unit.x - self.grid.camera_x
        y = fighter.unit.y + 52
        color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        ui.bar(x - 18, y, 36, 4, fighter.hp / fighter.max_hp, color)

    def draw_target_panel(self, attacker, target):
        """BG3-style target card: name, health, armour and the attack preview."""
        x = target.unit.x - self.grid.camera_x
        width, height = 200, 92
        left = max(8, min(WIDTH - width - 8, x - width / 2))
        bottom = target.unit.y + 92
        ui.panel(left, bottom, left + width, bottom + height, ENEMY_COLOR)
        ui.text(left + 10, bottom + height - 14, target.name, ENEMY_COLOR)
        ui.text(left + width - 62, bottom + height - 14, f"방어 {target.armor_class}", ui.MUTED, 14)
        ui.bar(left + 10, bottom + height - 34, width - 20, 8, target.hp / target.max_hp, ENEMY_COLOR)
        ui.text(left + 10, bottom + height - 46, f"체력 {target.hp}/{target.max_hp}", ui.MUTED, 14)
        if self.mode != "attack":
            ui.text(left + 10, bottom + 16, "2 공격을 고르면 명중 확률 표시", ui.DIM, 14)
        elif not attacker.action:
            ui.text(left + 10, bottom + 16, "이번 턴 행동을 이미 썼습니다", ui.DIM, 14)
        elif chebyshev(attacker.cell, target.cell) > 1:
            ui.text(left + 10, bottom + 16, "근접 공격 · 너무 멉니다", ui.DIM, 14)
        else:
            chance = round(hit_chance(attacker.attack_bonus, target.armor_class) * 100)
            ui.action_icon(left + 18, bottom + 18, 6, True)
            ui.text(left + 30, bottom + 18, f"명중 {chance}%", ui.ACCENT, 20)
            low, high = attacker.damage_range()
            ui.text(left + 120, bottom + 18, f"피해 {low}~{high}", ui.TEXT, 14)

    def draw_turn_order(self):
        count = len(self.order)
        total = count * CARD_WIDTH + (count - 1) * CARD_GAP
        left = WIDTH / 2 - total / 2
        ui.text(left - 44, CARDS_TOP - CARD_HEIGHT / 2, f"{self.round}R", ui.MUTED, 20)
        for index, fighter in enumerate(self.order):
            current = index == self.turn_index and self.outcome is None
            x = left + index * (CARD_WIDTH + CARD_GAP)
            top = CARDS_TOP + (4 if current else 0)
            bottom = top - CARD_HEIGHT
            team_color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
            border = ui.ACCENT if current else (team_color if fighter.alive else ui.DIM)
            ui.panel(x, bottom, x + CARD_WIDTH, top, border, ui.PANEL_RAISED if current else ui.PANEL)
            self.draw_portrait(fighter, x + 4, bottom + 4, 40, CARD_HEIGHT - 8, team_color)
            name_color = ui.TEXT if fighter.alive else ui.DIM
            ui.text(x + 50, top - 13, fighter.name, name_color, 14)
            if not fighter.alive:
                status, status_color = "쓰러짐", ui.DIM
            elif fighter.surprised:
                status, status_color = "기습당함", ui.DANGER
            else:
                status, status_color = f"선공 {fighter.initiative}", ui.MUTED
            ui.text(x + 50, top - 29, status, status_color, 13)
            ui.bar(x + 50, bottom + 7, CARD_WIDTH - 58, 5, fighter.hp / fighter.max_hp, team_color)

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

    # Top HUD strip ----------------------------------------------------------

    def draw_hud(self):
        ui.panel(0, HUD_BOTTOM, WIDTH - 1, HUD_TOP - 1, ui.BORDER, ui.PANEL, 255)
        fighter = self.current
        team_color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        self.draw_portrait(fighter, 8, HUD_BOTTOM + 7, 44, 50, team_color)
        ui.text(60, HUD_TOP - 15, f"{fighter.name}의 턴", team_color)
        ui.bar(60, HUD_BOTTOM + 26, 130, 7, fighter.hp / fighter.max_hp, team_color)
        ui.text(60, HUD_BOTTOM + 13, f"체력 {fighter.hp}/{fighter.max_hp}", ui.MUTED, 13)
        self.draw_resources(fighter, 206)
        if fighter.team != "party" or self.outcome is not None:
            ui.text(SLOTS_LEFT, HUD_BOTTOM + 32, self.log, ui.MUTED, 14)
            return
        if self.selected is None and self.is_player_turn():
            ui.text(SLOTS_LEFT, HUD_BOTTOM + 32, "캐릭터를 클릭해 선택하세요", ui.ACCENT, 14)
        self.draw_hotbar()

    def draw_resources(self, fighter, left):
        y = HUD_BOTTOM + 42
        ui.action_icon(left + 10, y, 8, bool(fighter.action))
        ui.bonus_icon(left + 36, y, 10, bool(fighter.bonus_action))
        ui.reaction_icon(left + 62, y, 10, bool(fighter.reaction))
        ui.text(left, HUD_BOTTOM + 22, f"이동 {fighter.moves_left}/{fighter.move_cells}칸", ui.MUTED, 13)
        ui.bar(left, HUD_BOTTOM + 8, 120, 5, fighter.moves_left / max(1, fighter.move_cells), ui.MOVE)

    def draw_hotbar(self):
        mouse = self.hover_screen
        for (kind, label, cost, enabled), (left, bottom, right, top) in self.button_rects():
            chosen = kind == self.mode
            hovered = mouse is not None and left <= mouse[0] <= right and bottom <= mouse[1] <= top
            if kind == "end":
                border = ui.ACCENT if hovered else ui.BORDER_LIGHT
                ui.panel(left, bottom, right, top, border, ui.PANEL_RAISED, 255)
                ui.text_center((left + right) / 2, top - 17, "턴 종료", ui.TEXT)
                ui.text_center((left + right) / 2, bottom + 11, "Space", ui.MUTED, 13)
                continue
            if chosen:
                border, fill = ui.ACCENT, (52, 70, 82)
            elif enabled:
                border, fill = (ui.ACCENT if hovered else ui.BORDER_LIGHT), ui.PANEL_RAISED
            else:
                border, fill = ui.DIM, ui.PANEL
            ui.panel(left, bottom, right, top, border, fill, 255)
            color = ui.TEXT if enabled else ui.DIM
            number = {"move": "1", "attack": "2"}[kind]
            ui.text(left + 4, top - 9, number, ui.MUTED if enabled else ui.DIM, 12)
            ui.text_center((left + right) / 2, bottom + 22, label, color)
            if kind == "move":
                ui.bar(left + 8, bottom + 6, SLOT_SIZE - 16, 4,
                       self.selected.moves_left / max(1, self.selected.move_cells),
                       ui.MOVE if enabled else ui.DIM)
            else:
                ui.action_icon(right - 9, top - 9, 5, enabled)
