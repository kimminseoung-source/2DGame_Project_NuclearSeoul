"""Where things lie on the bag's ground sheet (2026-11-16, bag screen B: "바닥 천에 늘어놓기").

One cell holds 0.1 weight, so the 5 x 4 sheet is the bag's whole 2.0 (supplies.BAG_CAPACITY):
a thing takes as many cells as it weighs (Tarkov / This War of Mine: room shows as cells, see
docs/research/GROUND_INVENTORY_UI_RESEARCH.md). Every unit lies apart, so two bandages are two
cells. The same rules lay out what lies on the ground nearby, on a smaller grid.
"""

from math import ceil

from supplies import KINDS, weight_of

CELL_WEIGHT = 0.1
BAG_GRID = (5, 4)
NEAR_GRID = (3, 2)


def shape(kind):
    """(columns, rows) a thing takes: 1 -> 1x1, 2 -> 2x1, 3 -> 3x1, 4 -> 2x2, more -> squarish."""
    n = max(1, round(weight_of(kind) / CELL_WEIGHT))
    if n <= 3:
        return n, 1
    w = ceil(n ** 0.5)
    return w, ceil(n / w)


def pack(things, grid):
    """Lay `things` [(kind, ref)] row by row in the first place each fits.
    Returns ([(kind, ref, col, row, w, h)], [things that did not fit])."""
    cols, rows = grid
    used = [[False] * cols for _ in range(rows)]
    placed, left = [], []
    for kind, ref in things:
        w, h = shape(kind)
        spot = next(((c, r) for r in range(rows - h + 1) for c in range(cols - w + 1)
                     if all(not used[r + j][c + i] for j in range(h) for i in range(w))), None)
        if spot is None and (w, h) != (1, 1):     # no room for its shape: squeeze into one cell
            w = h = 1
            spot = next(((c, r) for r in range(rows) for c in range(cols) if not used[r][c]), None)
        if spot is None:
            left.append((kind, ref))
            continue
        c, r = spot
        for j in range(h):
            for i in range(w):
                used[r + j][c + i] = True
        placed.append((kind, ref, c, r, w, h))
    return placed, left


def bag_things(bag, shown=lambda kind: True):
    """Every unit in the bag: supplies in the order supplies.KINDS lists them, then weapons."""
    things = [(kind, None) for kind in KINDS if shown(kind) for _ in range(bag.get(kind, 0))]
    things += [(kind, None) for kind in sorted(bag) if kind.startswith("w:") for _ in range(bag[kind])]
    return things


def at(placed, col, row):
    """The placed thing covering a cell, or None."""
    for p in placed:
        _, _, c, r, w, h = p
        if c <= col < c + w and r <= row < r + h:
            return p
    return None
