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
from settings import DOT, EXPOSURE_ON, HEIGHT, HERO_HP, UI_SCALE, WIDTH
import weapons
from supplies import BAG_CAPACITY, KINDS, bag_weight, item_name, item_text, weight_of

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
    return [(kind, n) for kind, n in game.bag.items() if n and kind in KINDS and (EXPOSURE_ON or kind != "pill")]


NOTE_PAPER = (200, 192, 168)       # note.png's paper
FOLD_SHADE = (150, 142, 120)       # the paper turned over


def note_rect(game):
    """The goal note on the pixel canvas (l, t, r, b): whole, or folded to a tab."""
    if game.note_folded:
        return 6, 7, 6 + px.width("목표", True) + 18, 7 + 15
    return 6, 7, 6 + 172, 7 + 46


def fold_mark(x, y, right):
    """The fold mark (2026-11-16, the user's sketch): a small filled triangle, no hatching ("빗금
    ㄴㄴ"), its point to the right on the folded tab (opens) and to the left on the open note
    (folds). 6 x 11 px at (x, y); each row one pixel longer than the last, so both slanted edges
    are clean 45-degree steps ("삼각형 똑바로": rows that grew by two left gaps in the edge)."""
    for j in range(11):
        reach = 5 - abs(j - 5)                                 # 0, 1, .. 5 (the point) .. 1, 0
        for i in range(reach + 1):
            edge = i == 0 or i == reach
            col = x + (i if right else 5 - i)
            px.rect(col, y + j, col, y + j, INK_C if edge else FOLD_SHADE)


def draw_hud(game):
    """The HUD of UI v2 on the pixel canvas (2026-11-16, "AI 티가 안 나게" -> v2, now in the game):
    the goal on a taped note, health and the statuses that ask for something, quick slots, the
    latest message. No boxes, no rounded chips; Galmuri with a 1 px outline."""
    hero = game.hero
    # the screen edge goes red, dithered: while bleeding, and for a moment when hit (2026-11-16 C:
    # the "긁힘! 체력 -12%" line is gone, the hit is felt instead)
    if (game.condition.bleeding or game.hurt_flash > 0) and not hero.dead:
        px.blit("bleed_edge.png", 0, 0)
    # goal: a taped, torn note; a click folds it to a small tab and opens it again
    # (2026-11-16 "쪽지를 접고 펼 수 있게": open, it hid what was drawn over the hero in a corner)
    if game.note_folded:
        l, t, r, b = note_rect(game)
        px.rect(l, t, r, b, NOTE_PAPER)
        px.rect(l, b, r, b, FOLD_SHADE)                               # the fold's shadow
        px.text(l + 4, t + 1, "목표", INK_C, bold=True, outline=False)
        fold_mark(r - 10, t + 2, right=True)
    else:
        px.blit("note.png", 6, 7)
        goal = f"{EXIT_NAME}로"
        px.text(20, 15, goal, INK_C, bold=True, outline=False)
        px.rect(20, 29, 20 + px.width(goal, True), 29, BLOOD)             # a pen underline
        px.text(20, 32, "붕대·통조림 있으면 챙기기", PENCIL, outline=False)
        fold_mark(162, 12, right=False)
    if EXPOSURE_ON:
        px.text(180, 15, f"피폭 {game.exposure:.0f}%", LIGHT)
    draw_status(game)
    # quick slots: plain squares with a bevel like the wrecks' metal
    items = bag_items(game)
    n = max(3, len(items))
    left = 320 - (n * 26 + (n - 1) * 4) // 2
    for i in range(n):
        l, t = left + i * 30, 326
        if i < len(items):
            px.rect(l, t, l + 25, t + 25, (20, 22, 26))
        px.frame(l, t, l + 25, t + 25, (64, 66, 70))
        px.rect(l + 1, t + 1, l + 24, t + 1, (84, 86, 90))
        if i < len(items):
            kind, count = items[i]
            px.blit(f"bag/icon_{kind}.png", l + 5, t + 4)
            px.text(l + 24, t + 13, str(count), LIGHT, anchor="r")
            key = {"bandage": "1", "pill": "2"}.get(kind)
            if key:
                px.text(l + 1, t - 13, key, GREY_C)
    px.text(left + n * 30 + 2, 336, "Tab", GREY_C)
    # the latest message, a hard outline, gone after a while
    age = game.clock - game.message_at
    if game.message and (age < MESSAGE_TIME or game.left):
        px.text(320, 286, game.message, (236, 214, 150), bold=True, anchor="m")


def health_shares(game):
    """(shown, trail) health shares: the red part follows the real health quickly; a pale part
    shows what was just lost and drains after it (damage trail)."""
    share = max(0.0, min(1.0, game.hero.hp / HERO_HP))
    shown = getattr(game, "hud_health", share)
    trail = getattr(game, "hud_trail", share)
    shown += (share - shown) * 0.35
    trail = share if share > trail else max(share, trail - 0.012)
    game.hud_health, game.hud_trail = shown, trail
    return shown, trail


def draw_status(game):
    """Bottom left: health (number + a square pixel bar with the pale trail) and only the statuses
    that ask for something - bleeding (bandage), slowed - plus sneaking. Wounds are in the bag."""
    hero, cond = game.hero, game.condition
    x, y = 14, 312
    w = hero.weapon                                     # the weapon in hand, by the health
    img = px.image(f"../weapons/{w['sprite']}.png")
    wx = 160                                            # between the health bar and the quick slots
    px.blit(f"../weapons/{w['sprite']}.png", wx, y + 6, 2)
    px.text(wx + img.w * 2 + 4, y + 2, w["name"], LIGHT)
    px.text(wx + img.w * 2 + 4, y + 16, "Q 바꾸기", GREY_C)
    pct = max(0, round(hero.hp / HERO_HP * 100))
    px.text(x, y, f"{pct}", LIGHT if pct > 50 else ORANGE if pct > 25 else BLOOD, bold=True, scale=2)
    shown, trail = health_shares(game)
    bx, by, bw = x + px.width(f"{pct}", True) * 2 + 6, y + 11, 96          # the bar right after the number
    px.rect(bx - 1, by - 1, bx + bw, by + 5, (8, 8, 10))
    if trail > 0:
        px.rect(bx, by, bx + max(0, int(bw * trail) - 1), by + 4, (150, 120, 112))
    if shown > 0.005:
        px.rect(bx, by, bx + max(0, int(bw * shown) - 1), by + 4, BLOOD)
        px.rect(bx, by, bx + max(0, int(bw * shown) - 1), by, (210, 80, 64))    # 1 px highlight
    ix, sy = x - 2, y + 30                      # the status line under the number
    shown_states = []
    if cond.bleeding:
        shown_states.append(("drop", "출혈", (226, 120, 100)))
    if hero.slowed > 0.05:
        shown_states.append(("snail", "느림", (150, 170, 200)))
    if hero.sneaking:
        shown_states.append((None, "은신", (150, 190, 160)))
    for icon, label, colour in shown_states:
        if icon:
            px.blit(f"bag/icon_{icon}.png", ix, sy - 2)
            ix += 16
        px.text(ix, sy, label, colour)
        ix += px.width(label) + 8


def draw_stamina(game):
    """Breath (stamina.py) as a thin pixel bar under the hero's feet, only while it is not full:
    what to watch is where the fight is, not in a corner (2026-11-16 "기력을 넣자")."""
    from stamina import MAX
    hero, st = game.hero, game.hero.stamina
    if hero.dead or (st.value >= MAX - 0.5 and st.tired_flash <= 0):
        return
    k = game.zoom * DOT                               # screen px per world unit
    sx = (hero.x - game.cam[0]) * k / px.K
    sy = (HEIGHT - (hero.y - game.cam[1]) * k) / px.K + 4
    l, t, w = round(sx) - 11, round(sy), 22
    colour = BLOOD if st.tired_flash > 0 else ORANGE if st.winded else ROAD
    px.rect(l - 1, t - 1, l + w, t + 2, BLOOD if st.tired_flash > 0 else INK_C)   # out of breath: red edge
    px.rect(l, t, l + w - 1, t + 1, (40, 40, 38))
    filled = round(w * st.value / MAX)
    if filled:
        px.rect(l, t, l + filled - 1, t + 1, colour)


# ---- Tab: the bag laid out on a ground sheet (2026-11-16, bag B v4, "이대로 구현") --------------
# Drawn on the 640x360 pixel canvas (pixel_ui) like docs/planning/ui_redesign/v4_bag_b_grid.png;
# the fixed art is exported by tools/ui/build_bag_art.py. Where things lie: bag_grid.
CELL = 34                                 # canvas px of one 0.1 cell
SHEET_GRID = (212, 96)                    # top-left of the sheet's grid
SHEET_MARGIN = 12
NEAR_ORIGIN = (SHEET_GRID[0] + bag_grid.BAG_GRID[0] * CELL + SHEET_MARGIN + 26, SHEET_GRID[1])
LIGHT, INK_C, GREY_C = (222, 216, 198), (34, 30, 28), (122, 122, 118)
ROAD, BLOOD, ORANGE = (196, 170, 92), (168, 34, 30), (214, 128, 52)
PENCIL = (78, 74, 70)
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
        wkey = weapons.key_of(kind)
        if wkey:                                                        # a carried weapon: its sprite x2
            sprite = weapons.WEAPONS[wkey]["sprite"]
            img = px.image(f"../weapons/{sprite}.png")
            px.blit(f"../weapons/{sprite}.png", l + (w * CELL - img.w * 2) // 2, t + (h * CELL - img.h * 2) // 2, 2)
        else:
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
    held = game.hero.weapon                                   # the weapon in hand (Q: the next one)
    img = px.image(f"../weapons/{held['sprite']}.png")
    px.blit(f"../weapons/{held['sprite']}.png", l + 18, t + 150 - img.h)
    px.text(l + 40, t + 146, held["name"], LIGHT)
    px.text(l + 40, t + 160, "Q 바꾸기", GREY_C)


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
        name = item_name(kind)
        px.text(150, y, name, ROAD, bold=True)
        px.text(150 + px.width(name, True) + 8, y, item_text(kind), LIGHT)
        px.text(px.CW - 22, y, f"칸 {pick[4] * pick[5]} · {weight_of(kind):.1f}", GREY_C, anchor="r")
    else:
        px.text(150, y, "빈 칸", GREY_C)
    use_word = "줍기" if game.bag_side == "near" else "들기" if pick and weapons.key_of(pick[0]) else "쓰기"
    rows = ((("Enter", use_word), ("X", "내려놓기"),
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
