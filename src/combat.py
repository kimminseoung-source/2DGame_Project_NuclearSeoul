"""Turn-based combat board laid over the street floor."""

import pico2d

from tile_map import FLOOR_BOTTOM, FLOOR_TOP, WIDTH


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


def skew_at(y):
    return (FLOOR_MIDDLE - y) * SKEW


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

    def draw(self, highlights):
        for column in range(COLUMNS):
            for row in range(ROWS):
                points = [(x - self.camera_x, y) for x, y in self.corners(column, row)]
                if self.blocked(column, row):
                    (x1, y1), _, (x3, y3), _ = points
                    _, (x2, y2), _, (x4, y4) = points
                    pico2d.draw_line(x1 + 6, y1 + 3, x3 - 6, y3 - 3, 120, 96, 82)
                    pico2d.draw_line(x2 - 6, y2 + 3, x4 + 6, y4 - 3, 120, 96, 82)
                    continue
                color = highlights.get((column, row), (74, 92, 104))
                draw_cell(points, color)


def draw_cell(points, color):
    # Inset each cell slightly so neighbouring outlines do not merge.
    cx = sum(x for x, _ in points) / 4
    cy = sum(y for _, y in points) / 4
    inset = [(x + (cx - x) * 0.06, y + (cy - y) * 0.12) for x, y in points]
    for (x1, y1), (x2, y2) in zip(inset, inset[1:] + inset[:1]):
        pico2d.draw_line(x1, y1, x2, y2, *color)


class Combat:
    """Holds the board and who stands where while a fight is running."""

    def __init__(self, camera_x, tile_map, combatants, surprise):
        self.grid = CombatGrid(camera_x, tile_map)
        self.surprise = surprise
        self.banner_time = BANNER_TIME
        self.cells = {}
        taken = []
        for unit in combatants:
            cell = self.grid.nearest_free_cell(unit.x, unit.y, taken)
            taken.append(cell)
            self.cells[unit] = cell
            unit.x, unit.y = self.grid.cell_center(*cell)

    def update(self, frame_time):
        self.banner_time = max(0.0, self.banner_time - frame_time)

    def draw(self, font, player):
        highlights = {
            cell: (97, 197, 156) if unit is player else (214, 92, 76)
            for unit, cell in self.cells.items()
        }
        self.grid.draw(highlights)
        if self.banner_time:
            text = "기습! 전투 시작" if self.surprise else "발각! 전투 시작"
            font.draw(WIDTH // 2 - 60, FLOOR_TOP + 120, text, (252, 218, 143))
