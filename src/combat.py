"""Turn-based combat board laid over the street floor."""

import random
from collections import deque
from math import floor

import pico2d

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

GRID_COLOR = (74, 92, 104)
REACH_COLOR = (112, 168, 214)
HOVER_COLOR = (252, 218, 143)
PARTY_COLOR = (97, 197, 156)
ENEMY_COLOR = (214, 92, 76)
TARGET_COLOR = (255, 140, 92)
TEXT_COLOR = (230, 230, 220)
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

    def damage_text(self):
        count, sides = self.damage_dice
        bonus = f"+{self.damage_bonus}" if self.damage_bonus else ""
        return f"{count}d{sides}{bonus}"


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
        self.moving = None
        self.attack = None
        self.wait_time = 0.0
        self.log = ""
        self.popups = []
        self.effects = []
        self.outcome = None
        self.start_turn()

    # Turn order -----------------------------------------------------------

    def roll(self, sides=20):
        return self.rng.randint(1, sides)

    def roll_initiative(self):
        for fighter in self.fighters:
            fighter.initiative_roll = self.roll()
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
        if fighter.surprised:
            self.log = f"{fighter.name}: 기습당해 이번 라운드에 행동하지 못합니다."
            self.wait_time = SKIP_PAUSE
            return
        if fighter.team == "enemy":
            self.log = f"{fighter.name}의 턴"
            self.enemy_approach(fighter)
        else:
            self.log = f"{fighter.name}의 턴 · 칸 클릭 이동 · 옆의 적 클릭 공격"

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

    def click(self, screen_x, y):
        if not self.is_player_turn():
            return
        cell = self.grid.cell_at(screen_x, y)
        target = self.fighter_at(cell)
        fighter = self.current
        if target is not None and target.team != fighter.team:
            if not fighter.action:
                self.log = "이번 턴의 행동을 이미 썼습니다."
            elif chebyshev(fighter.cell, target.cell) > 1:
                self.log = "너무 멉니다. 옆 칸으로 다가가세요."
            else:
                self.start_attack(fighter, target)
            return
        path = self.reachable(fighter).get(cell)
        if path:
            fighter.moves_left -= len(path)
            self.start_moving(fighter, path)

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
        attack = {"attacker": fighter, "target": target, "resolved": False, "time": 0.0,
                  "reaction": reaction}
        if fighter.team == "party":
            attack["swing"] = BatSwing((fighter.unit.direction, 0))
        else:
            fighter.unit.transition("windup", WINDUP_TIME)
        self.attack = attack

    def resolve_attack(self, attacker, target):
        roll = self.roll()
        total = roll + attacker.attack_bonus
        x, y = target.unit.x, target.unit.y + 62
        if roll == 1 or (roll != 20 and total < target.armor_class):
            self.popup(f"{roll}+{attacker.attack_bonus}={total} 빗나감", x, y, (181, 197, 209))
            self.log = f"{attacker.name}의 공격이 빗나갔습니다. (주사위 {roll}+{attacker.attack_bonus} < 방어 {target.armor_class})"
            return
        count, sides = attacker.damage_dice
        if roll == 20:
            count *= 2
        rolls = [self.roll(sides) for _ in range(count)]
        damage = sum(rolls) + attacker.damage_bonus
        target.hp = max(0, target.hp - damage)
        critical = roll == 20
        label = "치명타!" if critical else "명중"
        self.popup(f"{roll}+{attacker.attack_bonus}={total} {label} -{damage}", x, y,
                   (255, 214, 127) if critical else (255, 160, 130))
        self.log = f"{attacker.name} {label}: {target.name}에게 피해 {damage} ({'+'.join(map(str, rolls))}+{attacker.damage_bonus})"
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

    def status_text(self):
        fighter = self.current
        if fighter.team != "party" or self.outcome is not None:
            return self.log
        action = "행동 1" if fighter.action else "행동 0"
        bonus = "보조 1" if fighter.bonus_action else "보조 0"
        reaction = "반응 1" if fighter.reaction else "반응 0"
        return (f"{self.round}R · 이동 {fighter.moves_left}/{fighter.move_cells} · {action} · {bonus}"
                f" · {reaction} · Space 턴 종료")

    def hovered_target(self):
        target = self.fighter_at(self.hover)
        if target is None or target.team == self.current.team:
            return None
        return target

    def draw(self, font):
        highlights = {}
        target = None
        if self.is_player_turn():
            for cell in self.reachable(self.current):
                highlights[cell] = REACH_COLOR
            if self.hover in highlights:
                highlights[self.hover] = HOVER_COLOR
            target = self.hovered_target()
        for fighter in self.fighters:
            if fighter.alive:
                highlights[fighter.cell] = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        self.grid.draw(highlights)
        if not self.busy() and self.outcome is None:
            active = self.grid.corners(*self.current.cell)
            draw_cell([(x - self.grid.camera_x, y) for x, y in active], HOVER_COLOR, 0.0, 0.0)
        if target is not None:
            corners = self.grid.corners(*target.cell)
            draw_cell([(x - self.grid.camera_x, y) for x, y in corners], TARGET_COLOR, 0.0, 0.0)
        self.draw_turn_order(font)
        if self.banner_time:
            text = "기습! 전투 시작" if self.surprise else "발각! 전투 시작"
            font.draw(WIDTH // 2 - 60, FLOOR_TOP + 150, text, (252, 218, 143))

    def draw_overlay(self, font):
        """Health bars, attack preview and roll popups drawn above the units."""
        for fighter in self.fighters:
            if fighter.alive:
                self.draw_health(fighter, font)
        if self.is_player_turn():
            target = self.hovered_target()
            if target is not None:
                self.draw_attack_preview(self.current, target, font)
            else:
                path = self.reachable(self.current).get(self.hover)
                if path and self.path_provokes(self.current, path):
                    x, y = self.grid.cell_center(*self.hover)
                    font.draw(x - self.grid.camera_x - 52, y + 30, "기회 공격 위험!", (255, 160, 130))
        for text, x, y, time_left, color in self.popups:
            rise = (POPUP_TIME - time_left) * 22
            font.draw(x - self.grid.camera_x - 40, y + rise, text, color)

    def draw_health(self, fighter, font):
        x = fighter.unit.x - self.grid.camera_x
        y = fighter.unit.y + 52
        width = 36
        ratio = fighter.hp / fighter.max_hp
        color = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        pico2d.draw_rectangle(x - width / 2, y, x + width / 2, y + 4, 15, 23, 31, filled=True)
        if ratio:
            pico2d.draw_rectangle(x - width / 2, y, x - width / 2 + width * ratio, y + 4, *color, filled=True)

    def draw_attack_preview(self, attacker, target, font):
        x = target.unit.x - self.grid.camera_x
        y = target.unit.y + 72
        lines = [f"{target.name} 체력 {target.hp}/{target.max_hp}"]
        if not attacker.action:
            lines.append("행동을 이미 썼습니다")
        elif chebyshev(attacker.cell, target.cell) > 1:
            lines.append("근접 공격 · 너무 멂")
        else:
            chance = round(hit_chance(attacker.attack_bonus, target.armor_class) * 100)
            lines += [f"공격 명중 {chance}%", f"피해 {attacker.damage_text()} · 방어 {target.armor_class}"]
        width = 176
        height = 18 * len(lines) + 8
        pico2d.draw_rectangle(x - width / 2, y, x + width / 2, y + height, 15, 23, 31, filled=True)
        pico2d.draw_rectangle(x - width / 2, y, x + width / 2, y + height, *TARGET_COLOR)
        for index, line in enumerate(lines):
            font.draw(x - width / 2 + 8, y + height - 13 - 18 * index, line, TEXT_COLOR)

    def draw_turn_order(self, font):
        width, height, gap = 132, 30, 8
        left = WIDTH // 2 - (len(self.order) * (width + gap) - gap) // 2
        top = HEIGHT - 12
        for index, fighter in enumerate(self.order):
            x = left + index * (width + gap)
            current = index == self.turn_index
            fill = (38, 52, 62) if current else (15, 23, 31)
            border = HOVER_COLOR if current else (PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR)
            pico2d.draw_rectangle(x, top - height, x + width, top, *fill, filled=True)
            pico2d.draw_rectangle(x, top - height, x + width, top, *border)
            label = f"{fighter.name} {fighter.initiative}"
            if not fighter.alive:
                label += " 쓰러짐"
            elif fighter.surprised:
                label += " 기습"
            font.draw(x + 8, top - height / 2, label, TEXT_COLOR if fighter.alive else (120, 120, 120))
        font.draw(left, top - height - 16, f"{self.round}라운드 · 선공 = 주사위 + 민첩", (181, 197, 209))
