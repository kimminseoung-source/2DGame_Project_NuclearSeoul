"""Where things lie: the bag's sheet and the ground nearby (2026-11-16 bag B, 2026-11-18 "배낭,
인벤토리 많이 손봐야 함, 커서로 정리할 수 있게").

The bag is cells, not weight (2026-11-17 decision: "무게 계산 없애고 칸 수만"): a 5 x 4 sheet,
each thing a fixed shape (a bandage 1 x 1, a can 2 x 2, a weapon lying flat). Every unit in the bag
keeps its own spot - game.bag_places, [kind, col, row, turned] - so what the player arranges by
hand stays arranged. game.bag (kind -> count) stays the one truth of what is carried; sync() adds
a spot for anything new (the first place it fits) and lets go of spots for what is gone.
The ground nearby is still laid out fresh each time (pack).
"""

BAG_GRID = (5, 4)
NEAR_GRID = (3, 2)
SUPPLY_SHAPE = {"bandage": (1, 1), "pill": (1, 1), "can": (1, 1)}    # 2026-11-18 "통조림은 1칸으로"
# Supplies of one kind stack in one spot (2026-11-18 bag step 2), up to this many; weapons do not.
STACK = {"bandage": 5, "pill": 5, "can": 3}


def stack_max(kind):
    import weapons
    return 1 if weapons.key_of(kind) else STACK.get(kind, 1)


def shape(kind, turned=False):
    """(columns, rows) a thing takes; `turned` = rotated a quarter."""
    import weapons
    key = weapons.key_of(kind)
    w, h = weapons.SHAPE[key] if key else SUPPLY_SHAPE.get(kind, (1, 1))
    return (h, w) if turned else (w, h)


def pack(things, grid):
    """Lay `things` [(kind, ref)] row by row in the first place each fits (the ground nearby).
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


def at(placed, col, row):
    """The placed thing covering a cell, or None."""
    for p in placed:
        _, _, c, r, w, h = p
        if c <= col < c + w and r <= row < r + h:
            return p
    return None


# ---- the bag: every unit keeps its spot ------------------------------------------------------------
def cells(place):
    kind, c, r, turned = place[:4]
    w, h = shape(kind, turned)
    return {(c + i, r + j) for i in range(w) for j in range(h)}


def free(places, kind, c, r, turned, ignore=None):
    """Can `kind` lie at (c, r), turned or not, among `places` (leaving out `ignore`)?"""
    w, h = shape(kind, turned)
    cols, rows = BAG_GRID
    if c < 0 or r < 0 or c + w > cols or r + h > rows:
        return False
    taken = set()
    for p in places:
        if p is not ignore:
            taken |= cells(p)
    return not any((c + i, r + j) in taken for i in range(w) for j in range(h))


def first_spot(places, kind, ignore=None):
    """The first (col, row, turned) where `kind` fits - flat first, then turned - or None."""
    cols, rows = BAG_GRID
    for turned in (False, True):
        for r in range(rows):
            for c in range(cols):
                if free(places, kind, c, r, turned, ignore):
                    return c, r, turned
    return None


def shown(kind):
    from settings import EXPOSURE_ON
    return EXPOSURE_ON or kind != "pill"


def sync(game):
    """game.bag_places ([kind, col, row, turned, count]) brought in line with game.bag: what was
    added fills its kind's stacks first, then new spots; what is gone leaves the last stacks first."""
    places = getattr(game, "bag_places", None)
    if places is None:
        places = game.bag_places = []
    for p in places:
        if len(p) < 5:
            p.append(1)
    want = {kind: n for kind, n in game.bag.items() if n > 0 and shown(kind)}
    for kind in {p[0] for p in places}:
        stacks = [p for p in places if p[0] == kind]
        extra = sum(p[4] for p in stacks) - want.get(kind, 0)
        for p in reversed(stacks):                             # the last laid down gives way first
            if extra <= 0:
                break
            n = min(p[4], extra)
            p[4] -= n
            extra -= n
            if p[4] == 0:
                places.remove(p)
    big_first = sorted(want, key=lambda k: -(shape(k)[0] * shape(k)[1]))
    for kind in big_first:
        most = stack_max(kind)
        need = want[kind] - sum(p[4] for p in places if p[0] == kind)
        for p in places:
            if need > 0 and p[0] == kind and p[4] < most:
                n = min(most - p[4], need)
                p[4] += n
                need -= n
        while need > 0:
            spot = first_spot(places, kind)
            if spot is None:                                   # no room (should not happen): leave it out
                break
            n = min(most, need)
            places.append([kind, *spot, n])
            need -= n
    return places


def placed(game):
    """The bag's things as pack() gives them: (kind, place, col, row, w, h); a place's count is place[4]."""
    return [(p[0], p, p[1], p[2], *shape(p[0], p[3])) for p in sync(game)]


def room_for(game, kind, without=None):
    """Is there a place for one more `kind` - a stack with room or a free spot - after one
    `without` is taken out?"""
    places = [list(p) for p in sync(game)]
    if without is not None:
        gone = next((p for p in reversed(places) if p[0] == without), None)
        if gone is not None:
            gone[4] -= 1
            if gone[4] <= 0:
                places.remove(gone)
    if any(p[0] == kind and p[4] < stack_max(kind) for p in places):
        return True
    return first_spot(places, kind) is not None


def tidy(game):
    """The "정리" button: everything laid again from the top left, the biggest first, so the free
    room comes together. False (and nothing moved) when it would not all fit that way."""
    places = sync(game)
    order = sorted(places, key=lambda p: (-(shape(p[0])[0] * shape(p[0])[1]), p[0]))
    old = [list(p[1:4]) for p in places]
    laid = []
    for p in order:
        spot = first_spot(laid, p[0])
        if spot is None:
            for p2, o in zip(places, old):
                p2[1:4] = o
            return False
        p[1:4] = list(spot)
        laid.append(p)
    places.sort(key=lambda p: (p[2], p[1]))
    return True


def used_cells(game):
    return sum(len(cells(p)) for p in sync(game))
