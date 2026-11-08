"""Turn-based combat board laid over the street floor."""

import random
from collections import deque
from math import floor

import pico2d

from tile_map import FLOOR_BOTTOM, FLOOR_TOP, HEIGHT, WIDTH


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

GRID_COLOR = (74, 92, 104)
REACH_COLOR = (112, 168, 214)
HOVER_COLOR = (252, 218, 143)
PARTY_COLOR = (97, 197, 156)
ENEMY_COLOR = (214, 92, 76)
NEIGHBOURS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]


def skew_at(y):
    return (FLOOR_MIDDLE - y) * SKEW


def roll_d20(rng):
    return rng.randint(1, 20)


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
    """Turn data for one unit on the board."""

    def __init__(self, unit, name, team, dexterity, move_cells):
        self.unit = unit
        self.name = name
        self.team = team
        self.dexterity = dexterity
        self.move_cells = move_cells
        self.cell = None
        self.initiative = 0
        self.initiative_roll = 0
        self.surprised = False
        self.moves_left = 0
        self.action = 0
        self.bonus_action = 0


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
        self.wait_time = 0.0
        self.log = ""
        self.start_turn()

    # Turn order -----------------------------------------------------------

    def roll_initiative(self):
        for fighter in self.fighters:
            fighter.initiative_roll = roll_d20(self.rng)
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

    def is_player_turn(self):
        return self.current.team == "party" and self.moving is None and not self.wait_time

    def start_turn(self):
        fighter = self.current
        fighter.moves_left = fighter.move_cells
        fighter.action = 1
        fighter.bonus_action = 1
        if fighter.surprised:
            self.log = f"{fighter.name}: 기습당해 이번 라운드에 행동하지 못합니다."
            self.wait_time = SKIP_PAUSE
            return
        if fighter.team == "enemy":
            self.log = f"{fighter.name}의 턴"
            self.enemy_approach(fighter)
        else:
            self.log = f"{fighter.name}의 턴 · 칸을 클릭해 이동 · Enter 임시 종료"

    def end_turn(self):
        if self.moving is not None:
            return
        self.current.surprised = False
        self.turn_index += 1
        if self.turn_index == len(self.order):
            self.turn_index = 0
            self.round += 1
        self.wait_time = 0.0
        self.start_turn()

    # Movement -------------------------------------------------------------

    def occupied(self, ignore=None):
        return {f.cell for f in self.fighters if f is not ignore}

    def reachable(self, fighter):
        return self.grid.paths_from(fighter.cell, self.occupied(fighter), fighter.moves_left)

    def click(self, screen_x, y):
        if not self.is_player_turn():
            return
        cell = self.grid.cell_at(screen_x, y)
        path = self.reachable(self.current).get(cell)
        if path:
            self.current.moves_left -= len(path)
            self.start_moving(self.current, path)

    def start_moving(self, fighter, path):
        fighter.cell = path[-1]
        self.moving = fighter, list(path)
        if fighter.team == "enemy":
            fighter.unit.transition("chase")

    def enemy_approach(self, fighter):
        targets = [f for f in self.fighters if f.team == "party"]
        target = min(targets, key=lambda f: max(abs(f.cell[0] - fighter.cell[0]),
                                                abs(f.cell[1] - fighter.cell[1])))
        if max(abs(target.cell[0] - fighter.cell[0]), abs(target.cell[1] - fighter.cell[1])) <= 1:
            self.wait_time = ENEMY_PAUSE
            return
        paths = self.grid.paths_from(fighter.cell, self.occupied(fighter))
        goals = [
            path for cell, path in paths.items()
            if max(abs(cell[0] - target.cell[0]), abs(cell[1] - target.cell[1])) == 1
        ]
        if not goals:
            self.wait_time = ENEMY_PAUSE
            return
        path = min(goals, key=len)[:fighter.move_cells]
        fighter.moves_left -= len(path)
        self.start_moving(fighter, path)

    def update_moving(self, frame_time):
        fighter, path = self.moving
        unit = fighter.unit
        target_x, target_y = self.grid.cell_center(*path[0])
        dx, dy = target_x - unit.x, target_y - unit.y
        distance = (dx * dx + dy * dy) ** 0.5
        step = MOVE_SPEED * frame_time
        if abs(dx) > 1:
            unit.direction = 1 if dx > 0 else -1
        unit.walk_time += frame_time
        if distance <= step:
            unit.x, unit.y = target_x, target_y
            path.pop(0)
            if not path:
                self.moving = None
                unit.walk_time = 0.0
                if fighter.team == "enemy":
                    unit.transition("idle")
                    self.wait_time = ENEMY_PAUSE
        else:
            unit.x += dx / distance * step
            unit.y += dy / distance * step

    def update(self, frame_time):
        self.banner_time = max(0.0, self.banner_time - frame_time)
        if self.moving is not None:
            self.update_moving(frame_time)
            return
        if self.wait_time:
            self.wait_time = max(0.0, self.wait_time - frame_time)
            if not self.wait_time:
                self.end_turn()

    # Drawing --------------------------------------------------------------

    def status_text(self):
        fighter = self.current
        if fighter.team != "party":
            return self.log
        action = "행동 1" if fighter.action else "행동 0"
        bonus = "보조 1" if fighter.bonus_action else "보조 0"
        return f"{self.round}라운드 · 이동 {fighter.moves_left}/{fighter.move_cells}칸 · {action} · {bonus} · Space 턴 종료"

    def draw(self, font):
        highlights = {}
        if self.is_player_turn():
            for cell in self.reachable(self.current):
                highlights[cell] = REACH_COLOR
            if self.hover in highlights:
                highlights[self.hover] = HOVER_COLOR
        for fighter in self.fighters:
            highlights[fighter.cell] = PARTY_COLOR if fighter.team == "party" else ENEMY_COLOR
        self.grid.draw(highlights)
        if self.moving is None:
            active = self.grid.corners(*self.current.cell)
            draw_cell([(x - self.grid.camera_x, y) for x, y in active], HOVER_COLOR, 0.0, 0.0)
        self.draw_turn_order(font)
        if self.banner_time:
            text = "기습! 전투 시작" if self.surprise else "발각! 전투 시작"
            font.draw(WIDTH // 2 - 60, FLOOR_TOP + 150, text, (252, 218, 143))

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
            if fighter.surprised:
                label += " 기습"
            font.draw(x + 8, top - height / 2, label, (230, 230, 220))
        font.draw(left, top - height - 16, f"{self.round}라운드 · 선공 = 주사위 + 민첩", (181, 197, 209))
