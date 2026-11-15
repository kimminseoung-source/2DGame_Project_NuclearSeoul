"""Screen UI over the world (2026-11-15 "UI적인 측면을 많이 개선해 보자, 인벤토리 등등").

- bottom left: the status panel - the health bar and the status icons (bleeding, wounds, slowed, sneaking: condition.py)
- bottom middle: quick slots (bag contents with their keys)
- top left: the goal and how many infected are left
- above the slots: the latest message, fading away
- Tab: the bag laid out on a ground sheet (2026-11-16, bag B v4): things take as many 0.1
  cells as they weigh, a 20-segment weight bar, the ground nearby on the same grid, the body
  with its wounds and the gear in hand. Pixel canvas + Galmuri (pixel_ui), not smooth shapes
- the area summary once the hero has left

Everything scales with the window (settings.UI_SCALE). Item icons are drawn here from simple
shapes so any new supply kind only needs an entry in supplies.KINDS.
"""

import pico2d

import bag_grid
import pixel_ui as px
import ui
from area import EXIT_NAME
from settings import EXPOSURE_ON, HEIGHT, HERO_HP, UI_SCALE, WIDTH
from supplies import BAG_CAPACITY, KINDS, bag_weight, weight_of

U = UI_SCALE
PANEL = (14, 16, 20)
EDGE = (70, 74, 80)
TEXT = (226, 222, 210)
DIM = (150, 150, 150)
MESSAGE_TIME = 4.0


def size(px):
    return round(px * U)


def panel(l, b, r, t, alpha=210):
    pico2d.draw_rectangle(l, b, r, t, *PANEL, alpha, filled=True)
    pico2d.draw_rectangle(l, b, r, t, *EDGE)


def draw_icon(kind, x, y, s):
    """A small picture of a supply centred at (x, y), s = half size in screen px."""
    _, body, band = KINDS[kind][:3]
    if kind == "can":                                       # tin can: body, rim, label
        pico2d.draw_rectangle(x - s * 0.6, y - s * 0.8, x + s * 0.6, y + s * 0.8, *body, filled=True)
        pico2d.draw_rectangle(x - s * 0.6, y - s * 0.25, x + s * 0.6, y + s * 0.35, *band, filled=True)
        pico2d.draw_rectangle(x - s * 0.6, y + s * 0.65, x + s * 0.6, y + s * 0.8, 200, 200, 205, filled=True)
    elif kind == "bandage":                                 # rolled bandage with a loose end
        pico2d.draw_rectangle(x - s * 0.7, y - s * 0.5, x + s * 0.4, y + s * 0.5, *body, filled=True)
        pico2d.draw_rectangle(x + s * 0.4, y - s * 0.5, x + s * 0.8, y - s * 0.2, *body, filled=True)
        pico2d.draw_rectangle(x - s * 0.7, y - s * 0.1, x + s * 0.4, y + s * 0.1, *band, filled=True)
    else:                                                   # pill bottle
        pico2d.draw_rectangle(x - s * 0.45, y - s * 0.8, x + s * 0.45, y + s * 0.5, *body, filled=True)
        pico2d.draw_rectangle(x - s * 0.5, y + s * 0.5, x + s * 0.5, y + s * 0.8, *band, filled=True)


def bag_items(game):
    """(kind, count) for every kind the hero carries, in the order supplies.KINDS lists them."""
    return [(kind, n) for kind, n in game.bag.items() if n and (EXPOSURE_ON or kind != "pill")]


def draw_hud(game):
    hero = game.hero
    draw_status(game)
    # quick slots (bottom middle)
    items = bag_items(game)
    slot = size(52)
    total = max(3, len(items))
    x0 = size(16) + size(330) + size(14)                 # right of the status panel
    for i in range(total):
        sl, sb = x0 + i * (slot + size(6)), size(16)
        panel(sl, sb, sl + slot, sb + slot)
        if i < len(items):
            kind, n = items[i]
            draw_icon(kind, sl + slot / 2, sb + slot / 2 + size(2), slot * 0.32)
            ui.text(sl + slot - size(16), sb + size(8), str(n), TEXT, size(12))
            key = {"bandage": "1", "pill": "2"}.get(kind)
            if key:
                ui.text(sl + size(4), sb + slot - size(10), key, DIM, size(11))
    ui.text(x0 + total * (slot + size(6)) + size(4), size(44), "Tab 배낭", DIM, size(12))
    ui.text(x0 + total * (slot + size(6)) + size(4), size(24), f"무게 {bag_weight(game.bag):.1f}/{BAG_CAPACITY:.1f}", DIM, size(11))
    # goal (top left)
    left = game.to_spawn + sum(z.alive for z in game.zombies)
    panel(size(12), HEIGHT - size(62), size(380), HEIGHT - size(12), 170)
    ui.text(size(22), HEIGHT - size(28), f"목표: 물자를 챙겨 {EXIT_NAME}로", TEXT, size(13))
    extra = f" · 피폭 {game.exposure:.0f}%" if EXPOSURE_ON else ""
    ui.text(size(22), HEIGHT - size(50), f"남은 피폭체 {left} · 쓰러진 횟수 {game.deaths}{extra}", DIM, size(12))
    # message (fades away)
    age = game.clock - game.message_at
    if game.message and (age < MESSAGE_TIME or game.left):
        ui.text_center(WIDTH / 2, size(112), game.message, (236, 214, 150), size(14))


def health_bar(game, l, b, w, h):
    """Health as one bar (2026-11-15 "칸으로 말고 바 형식으로"). The red part follows the real
    health quickly; a pale part shows what was just lost and drains after it (damage trail)."""
    share = max(0.0, min(1.0, game.hero.hp / HERO_HP))
    shown = getattr(game, "hud_health", share)
    trail = getattr(game, "hud_trail", share)
    shown += (share - shown) * 0.35                          # eased toward the real value
    trail = share if share > trail else max(share, trail - 0.012)
    game.hud_health, game.hud_trail = shown, trail
    pico2d.draw_rectangle(l, b, l + w, b + h, 40, 22, 22, filled=True)
    pico2d.draw_rectangle(l, b, l + w * trail, b + h, 210, 170, 150, filled=True)
    colour = (176, 54, 48) if share > 0.5 else (206, 60, 44)
    pico2d.draw_rectangle(l, b, l + w * shown, b + h, *colour, filled=True)
    pico2d.draw_rectangle(l, b, l + w, b + h, 90, 60, 58)


def draw_status(game):
    """Bottom left: the health bar and, under it, the status icons (no heart rate: 2026-11-16
    "심장 박동 수는 전혀 필요 없어 보이는데")."""
    hero, cond = game.hero, game.condition
    l, b, w, h = size(16), size(16), size(330), size(78)
    panel(l, b, l + w, b + h)
    ui.text(l + size(10), b + h - size(14), "체력", TEXT, size(12))
    health_bar(game, l + size(46), b + h - size(20), size(220), size(11))
    pct = max(0, round(hero.hp / HERO_HP * 100))
    colour = TEXT if pct > 50 else (230, 170, 90) if pct > 25 else (230, 90, 80)
    ui.text(l + size(274), b + h - size(14), f"{pct}%", colour, size(13))
    # status icons: a coloured tile with a short word, the stronger the brighter
    x = l + size(10)
    for label, tint, level in cond.moodles(hero)[:7]:
        tile = size(24)
        if x + tile * 1.45 > l + w - size(4):
            break
        pico2d.draw_rectangle(x, b + size(18), x + tile * 1.45, b + size(18) + tile,
                              *(round(c * (0.55 + 0.15 * level)) for c in tint), filled=True)
        ui.text_center(x + tile * 0.72, b + size(18) + tile / 2, label, (245, 240, 230), size(10))
        x += tile * 1.45 + size(3)


# ---- Tab: the bag laid out on a ground sheet (2026-11-16, bag B v4, "이대로 구현") --------------
# Drawn on the 640x360 pixel canvas (pixel_ui) like docs/planning/ui_redesign/v4_bag_b_grid.png;
# the fixed art is exported by tools/ui/build_bag_art.py. Where things lie: bag_grid.
CELL = 34                                 # canvas px of one 0.1 cell
SHEET_GRID = (212, 96)                    # top-left of the sheet's grid
SHEET_MARGIN = 12
NEAR_ORIGIN = (SHEET_GRID[0] + bag_grid.BAG_GRID[0] * CELL + SHEET_MARGIN + 26, SHEET_GRID[1])
LIGHT, INK_C, GREY_C = (222, 216, 198), (34, 30, 28), (122, 122, 118)
ROAD, BLOOD, ORANGE = (196, 170, 92), (168, 34, 30), (214, 128, 52)
FOOT_BAG, FOOT_BAG_CHOSEN, FOOT_BAG_EDGE = (74, 80, 58), (108, 114, 86), (50, 54, 38)
FOOT_NEAR, FOOT_NEAR_CHOSEN, FOOT_NEAR_EDGE = (40, 42, 46), (62, 64, 68), (70, 72, 76)
# a wound's mark on the body outline (canvas px from its top-left), by kind
WOUND_SPOTS = {"scratch": [(3, 28), (36, 46), (14, 70)], "laceration": [(26, 30), (10, 80)],
               "bite": [(37, 38), (20, 8)]}


def nearby_items(game):
    from supplies import PICK_RANGE
    return [s for s in game.supplies if not s.taken
            and (s.x - game.hero.x) ** 2 + (s.y - game.hero.y) ** 2 <= (PICK_RANGE * 2.5) ** 2]


def bag_layout(game):
    """{"bag": placed, "near": placed, "near_left": count} - placed as bag_grid.pack gives."""
    shown = (lambda kind: EXPOSURE_ON or kind != "pill")
    bag, _ = bag_grid.pack(bag_grid.bag_things(game.bag, shown), bag_grid.BAG_GRID)
    near, left = bag_grid.pack([(s.kind, s) for s in nearby_items(game)], bag_grid.NEAR_GRID)
    return {"bag": bag, "near": near, "near_left": len(left)}


def grid_origin(side):
    return SHEET_GRID if side == "bag" else NEAR_ORIGIN


def cell_at(cx, cy):
    """(side, col, row) under a canvas point, or None."""
    for side, (cols, rows) in (("bag", bag_grid.BAG_GRID), ("near", bag_grid.NEAR_GRID)):
        gx, gy = grid_origin(side)
        if cx < gx or cy < gy:
            continue
        col, row = int((cx - gx) // CELL), int((cy - gy) // CELL)
        if col < cols and row < rows:
            return side, col, row
    return None


def chosen(game, layout=None):
    layout = layout or bag_layout(game)
    return bag_grid.at(layout[game.bag_side], *game.bag_cell)


def fits(game, kind):
    return bag_weight(game.bag) + weight_of(kind) <= BAG_CAPACITY + 1e-6


def corners(l, t, r, b, colour):
    """The chosen cell: four square corner marks, not a rounded highlight or a side stripe."""
    for (cx, cy, sx, sy) in ((l, t, 1, 1), (r, t, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
        px.rect(min(cx, cx + 5 * sx), cy, max(cx, cx + 5 * sx), cy, colour)
        px.rect(cx, min(cy, cy + 5 * sy), cx, max(cy, cy + 5 * sy), colour)


def draw_things(game, side, placed, pick):
    gx, gy = grid_origin(side)
    fill, fill_chosen, edge = ((FOOT_BAG, FOOT_BAG_CHOSEN, FOOT_BAG_EDGE) if side == "bag"
                               else (FOOT_NEAR, FOOT_NEAR_CHOSEN, FOOT_NEAR_EDGE))
    for p in placed:
        kind, ref, c, r, w, h = p
        if game.bag_drag is not None and game.bag_drag[1] == p:
            continue                                                  # it is in the hand
        l, t = gx + c * CELL, gy + r * CELL
        rr, bb = l + w * CELL, t + h * CELL
        px.rect(l + 2, t + 2, rr - 2, bb - 2, fill_chosen if p == pick else fill)
        px.frame(l + 2, t + 2, rr - 2, bb - 2, edge)
        px.blit(f"bag/big_{kind}.png", l + (w * CELL - 32) // 2, t + (h * CELL - 32) // 2)
        if p == pick:
            heavy = side == "near" and not fits(game, kind)          # it would not fit: red corners
            corners(l, t, rr, bb, BLOOD if heavy else ROAD)
    if pick is None and game.bag_side == side:                         # an empty cell is chosen
        c, r = game.bag_cell
        corners(gx + c * CELL, gy + r * CELL, gx + (c + 1) * CELL, gy + (r + 1) * CELL, GREY_C)


def draw_body_column(game):
    l, t = 22, 42
    hp = max(0, round(100 * game.hero.hp / HERO_HP))
    px.text(l, t, "몸", LIGHT, bold=True)
    px.text(l + 112, t, f"{hp}%", BLOOD if hp < 60 else LIGHT, bold=True, anchor="r")
    bx, by = l + 10, t + 26
    px.blit("bag/body.png", bx, by)
    used = {}
    for wound in game.condition.injuries:
        k = used.get(wound["kind"], 0)
        used[wound["kind"]] = k + 1
        sx, sy = WOUND_SPOTS[wound["kind"]][k % len(WOUND_SPOTS[wound["kind"]])]
        colour = BLOOD if wound["bleed"] > 0 else (92, 40, 40)
        px.rect(bx + sx - 2, by + sy - 2, bx + sx + 2, by + sy + 2, colour)
    wounds = game.condition.injuries
    for k, wound in enumerate(wounds[:4]):
        y = t + 40 + k * 30
        px.text(l + 62, y, wound["name"], LIGHT)
        state = "피가 난다" if wound["bleed"] > 0 else "감았다" if wound.get("dressed") else ""
        px.text(l + 62, y + 14, state, BLOOD if wound["bleed"] > 0 else GREY_C)
    if not wounds:
        px.text(l + 62, t + 40, "다친 곳 없음", GREY_C)
    px.text(l, t + 146, "손", GREY_C)
    px.blit("bag/icon_machete.png", l + 18, t + 143)
    px.text(l + 44, t + 146, "마체테", LIGHT)


def draw_weight_bar(x, y, used):
    """20 segments of 0.1; orange past 1.6, red past the limit (Zomboid's heavy load)."""
    colour = BLOOD if used > BAG_CAPACITY + 1e-6 else ORANGE if used > 1.6 + 1e-6 else ROAD
    for i in range(round(BAG_CAPACITY / bag_grid.CELL_WEIGHT)):
        sx = x + i * 9
        px.rect(sx, y, sx + 7, y + 5, INK_C)
        px.rect(sx + 1, y + 1, sx + 6, y + 4, colour if i < round(used * 10 + 1e-6) else (40, 40, 38))


def draw_inventory(game):
    """The bag laid out on a ground sheet, the ground beside it, the body, the keys."""
    layout = bag_layout(game)
    pick = bag_grid.at(layout[game.bag_side], *game.bag_cell)
    px.blit("bag/dither.png", 0, 0)
    draw_body_column(game)
    gx, gy = SHEET_GRID
    sl, st = gx - SHEET_MARGIN, gy - SHEET_MARGIN
    sr = gx + bag_grid.BAG_GRID[0] * CELL + SHEET_MARGIN
    sb = gy + bag_grid.BAG_GRID[1] * CELL + SHEET_MARGIN
    used = bag_weight(game.bag)
    px.blit("bag/icon_backpack.png", sl, st - 30)
    px.text(sl + 20, st - 27, "배낭", LIGHT, bold=True)
    px.text(sr, st - 27, f"{used:.1f} / {BAG_CAPACITY:.1f}", LIGHT, anchor="r")
    px.blit("bag/sheet.png", sl, st)
    draw_things(game, "bag", layout["bag"], pick if game.bag_side == "bag" else None)
    draw_weight_bar(sl + 8, sb + 6, used)
    nx, ny = NEAR_ORIGIN
    px.text(nx, ny - 39, "근처", LIGHT, bold=True)
    px.text(nx, ny - 23, "< 바닥 >", GREY_C)
    px.blit("bag/ground.png", nx - 4, ny - 4)
    draw_things(game, "near", layout["near"], pick if game.bag_side == "near" else None)
    if not layout["near"]:
        px.text(nx + bag_grid.NEAR_GRID[0] * CELL // 2, ny + CELL - 6, "주울 것 없음", GREY_C, anchor="m")
    if layout["near_left"]:
        px.text(nx, ny + bag_grid.NEAR_GRID[1] * CELL + 8, f"그 밖에 {layout['near_left']}개", GREY_C)
    # what just happened in the bag, the chosen thing and the keys
    y = px.CH - 56
    if game.message and game.message != game.bag_note_from:
        px.text(150, y - 20, game.message, (236, 214, 150))
    if pick is not None:
        kind = pick[0]
        name = KINDS[kind][0]
        px.text(150, y, name, ROAD, bold=True)
        px.text(150 + px.width(name, True) + 8, y, KINDS[kind][3], LIGHT)
        px.text(px.CW - 22, y, f"칸 {pick[4] * pick[5]} · {weight_of(kind):.1f}", GREY_C, anchor="r")
    else:
        px.text(150, y, "빈 칸", GREY_C)
    rows = ((("Enter", "쓰기" if game.bag_side == "bag" else "줍기"), ("X", "내려놓기"),
             ("F", "같은 것 줍기"), ("Shift+F", "모두 줍기")),
            (("WASD", "고르기 (D: 근처로)"), ("끌어 놓기", "옮기기"), ("Tab", "닫기")))
    for row, keys in enumerate(rows):
        kx = 150
        for key, label in keys:
            kx = px.key_cap(kx, y + 16 + row * 16, key, label, LIGHT, INK_C, LIGHT)
    if game.bag_drag is not None:                                      # carried by the mouse
        mx, my = game.bag_mouse
        px.blit(f"bag/big_{game.bag_drag[1][0]}.png", round(mx) - 16, round(my) - 16)


def draw_death(game):
    """Zomboid's "this is how you died", short (the area still restarts at once, DESIGN_LOCK)."""
    w, hgt = size(360), size(120)
    l, b = WIDTH / 2 - w / 2, HEIGHT / 2 - hgt / 2
    panel(l, b, l + w, b + hgt, 235)
    secs = int(game.death_time)
    lines = [("이렇게 쓰러졌다", (220, 90, 80), 17),
             (game.death_cause or "피폭체에게 당했다", TEXT, 14),
             (f"버틴 시간 {secs // 60}분 {secs % 60:02d}초 · 쓰러뜨린 피폭체 {game.kills}", DIM, 12)]
    for i, (line, colour, px) in enumerate(lines):
        ui.text_center(WIDTH / 2, b + hgt - size(28) - i * size(32), line, colour, size(px))


def draw_summary(game):
    w, h = size(400), size(170)
    l, b = WIDTH / 2 - w / 2, HEIGHT / 2 - h / 2
    panel(l, b, l + w, b + h, 235)
    carried = " · ".join(f"{KINDS[k][0]} {n}" for k, n in bag_items(game)) or "없음"
    lines = [(f"{EXIT_NAME}로 빠져나왔다", (236, 214, 150), 17),
             (f"챙긴 물자: {carried}", TEXT, 14),
             (f"쓰러뜨린 피폭체 {game.kills}" + (f" · 피폭 {game.exposure:.0f}%" if EXPOSURE_ON else ""), TEXT, 14),
             ("다음 구역(지하철)은 3단계에서 · R 다시", DIM, 13)]
    for i, (line, colour, px) in enumerate(lines):
        ui.text_center(WIDTH / 2, b + h - size(34) - i * size(36), line, colour, size(px))
