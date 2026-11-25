"""Screen UI over the world (2026-11-15 "UI적인 측면을 많이 개선해 보자, 인벤토리 등등").

- bottom left: the status panel - the health bar and the status icons (bleeding, slowed, sneaking: condition.py)
- bottom middle: quick slots (bag contents with their keys)
- top left: the goal and how many infected are left
- above the slots: the latest message, fading away
- Tab: the bag laid out on a ground sheet (2026-11-16, bag B v4; 2026-11-18 cells, not weight):
  each thing has a shape and keeps the spot it was put in (bag_grid), dragged with a green / red
  landing preview, a bar of taken cells, the ground nearby on the same grid, the body with its
  wounds and the gear in hand. Pixel canvas + Galmuri (pixel_ui), not smooth shapes
- the area summary once the hero has left

Everything scales with the window (settings.UI_SCALE). Item icons are drawn here from simple
shapes so any new supply kind only needs an entry in supplies.KINDS.
"""

import pico2d

import bag_grid
import pixel_ui as px
import ui
from area import CREDIT, EXIT_NAME
from settings import DOT, EXPOSURE_ON, HEIGHT, HERO_HP, UI_SCALE, WIDTH
import weapons
import supplies as supply_rules
from supplies import KINDS, item_name, item_text

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
    # the old "긁힘! 체력 -12%" line is gone, the hit is felt instead)
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
        defending = game.defense is not None
        goal = "기차가 올 때까지 버티기" if defending else f"{EXIT_NAME}로"
        px.text(20, 15, goal, INK_C, bold=True, outline=False)
        px.rect(20, 29, 20 + px.width(goal, True), 29, BLOOD)             # a pen underline
        px.text(20, 32, "군인·시민을 지키기" if defending else "E로 기차 기다리기", PENCIL, outline=False)
        fold_mark(162, 12, right=False)
    day = game.daylight                             # the hour, under the goal note
    px.text(22, 50 if not game.note_folded else 30, f"{day.clock} {day.name}", LIGHT if day.light > 0.5 else (150, 170, 220))
    if game.defense is not None:                   # the station: time left until the train
        left = max(0, int(game.defense + 0.99))
        people = sum(1 for s in game.people if s.alive)
        px.text(320, 10, f"기차 도착까지 {left}초", ORANGE if left > 10 else (236, 214, 150), bold=True, anchor="m", scale=2)
        px.text(320, 40, f"군인·시민 {people}/{len(game.people)}", LIGHT, anchor="m")
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
            key = supply_rules.QUICK_KEYS.get(kind)
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


# ART_BIBLE.md (2026-11-25) UI pieces: things the hero carries - a dark blue-grey metal plate with a
# rusty edge and rivets, bars cut into ticks, paper-coloured figures. F4 "HUD 아트 바이블" compares.
BIBLE_HUD = True
PLATE, PLATE_EDGE, PLATE_LIT, RIVET = (38, 45, 53), (82, 92, 102), (110, 119, 128), (140, 148, 155)
PAPER, BIBLE_RED, BIBLE_RED_DARK, BIBLE_AMBER = (230, 224, 210), (184, 57, 44), (142, 42, 34), (217, 130, 43)


def metal_plate(l, t, r, b):
    """A riveted plate: dark fill, a 1 px rusty edge, a lit top line, a rivet in each corner."""
    px.rect(l, t, r, b, PLATE)
    px.frame(l, t, r, b, PLATE_EDGE)
    px.rect(l + 1, t + 1, r - 1, t + 1, PLATE_LIT)
    for cx, cy in ((l + 2, t + 2), (r - 3, t + 2), (l + 2, b - 3), (r - 3, b - 3)):
        px.rect(cx, cy, cx + 1, cy + 1, RIVET)


def tick_bar(l, t, ticks, shown, trail, colour=BIBLE_RED, width=4, gap=1, height=6):
    """A bar of separate ticks (ART_BIBLE 6): full ticks in colour, the just-lost part pale, the rest dark."""
    for i in range(ticks):
        x = l + i * (width + gap)
        edge = (i + 1) / ticks
        if shown >= edge - 0.5 / ticks:
            fill, top = colour, (220, 96, 76)
        elif trail >= edge - 0.5 / ticks:
            fill, top = (150, 120, 112), (170, 140, 132)
        else:
            fill, top = (26, 32, 38), (26, 32, 38)
        px.rect(x, t, x + width - 1, t + height - 1, fill)
        px.rect(x, t, x + width - 1, t, top)


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
    if "shot" in w:                                     # a gun: its rounds, red when empty
        px.text(wx + img.w * 2 + 8 + px.width(w["name"]), y + 2, f"{game.ammo}발", BLOOD if game.ammo <= 0 else ORANGE, bold=True)
    px.text(wx + img.w * 2 + 4, y + 16, "Q 바꾸기", GREY_C)
    pct = max(0, round(hero.hp / HERO_HP * 100))
    shown, trail = health_shares(game)
    if BIBLE_HUD:                                       # ART_BIBLE 6: a metal plate, a ticked bar
        metal_plate(x - 6, y - 5, x + 134, y + 25)
        px.text(x, y, f"{pct}", PAPER if pct > 50 else BIBLE_AMBER if pct > 25 else BIBLE_RED, bold=True, scale=2)
        tick_bar(x + px.width(f"{pct}", True) * 2 + 6, y + 8, 16, shown, trail)
    else:
        px.text(x, y, f"{pct}", LIGHT if pct > 50 else ORANGE if pct > 25 else BLOOD, bold=True, scale=2)
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
    from settings import STAMINA_ON
    if not STAMINA_ON:
        draw_roll_dots(game)
        return
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


def draw_roll_dots(game):
    """Rolls stored (stamina.Charges, 2026-11-21) as small dots under the hero's feet, only while one
    is used or coming back. Juice: a dot that comes back pops bigger and brighter for a moment; Space
    with none left flashes the dots red; the one coming back fills from the left."""
    import stamina
    hero, ch = game.hero, game.hero.rolls
    if hero.dead or (ch.full and ch.pop <= 0 and ch.empty <= 0):
        return
    k = game.zoom * DOT
    sx = (hero.x - game.cam[0]) * k / px.K
    sy = (HEIGHT - (hero.y - game.cam[1]) * k) / px.K + 4
    n, w, gap = int(round(stamina.ROLL_CHARGES)), 4, 3
    left = round(sx) - (n * w + (n - 1) * gap) // 2
    t = round(sy)
    for i in range(n):
        l = left + i * (w + gap)
        edge = BLOOD if ch.empty > 0 else INK_C
        if i == ch.left - 1 and ch.pop > 0:            # just came back: bigger, brighter
            px.rect(l - 2, t - 2, l + w + 1, t + 3, edge)
            px.rect(l - 1, t - 1, l + w, t + 2, LIGHT)
            continue
        px.rect(l - 1, t - 1, l + w, t + 2, edge)
        px.rect(l, t, l + w - 1, t + 1, (40, 40, 38))
        if i < ch.left:
            px.rect(l, t, l + w - 1, t + 1, ROAD)
        elif i == ch.left and ch.coming > 0:           # the one coming back fills from the left
            fill = int(w * ch.coming)
            if fill:
                px.rect(l, t, l + fill - 1, t + 1, GREY_C)


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
# where blows leave marks on the body outline (canvas px from its top-left), in order
WOUND_SPOTS = [(26, 30), (3, 28), (37, 38), (14, 70), (36, 46), (10, 80), (20, 8)]


def nearby_items(game):
    from supplies import PICK_RANGE
    return [s for s in game.supplies if not s.taken
            and (s.x - game.hero.x) ** 2 + (s.y - game.hero.y) ** 2 <= (PICK_RANGE * 2.5) ** 2]


def bag_layout(game):
    """{"bag": placed, "near": placed, "near_left": count} - placed as bag_grid.pack gives."""
    near, left = bag_grid.pack([(s.kind, s) for s in nearby_items(game)], bag_grid.NEAR_GRID)
    return {"bag": bag_grid.placed(game), "near": near, "near_left": len(left)}


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
    return bag_grid.room_for(game, kind)


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
        draw_item(kind, l, t, w, h, turned=side == "bag" and ref[3])
        count = ref[4] if side == "bag" else 1
        if count > 1:                                                   # a stack: how many
            px.text(rr - 4, bb - 15, f"{count}", LIGHT, bold=True, anchor="r")
        if p == pick:
            heavy = side == "near" and not fits(game, kind)          # it would not fit: red corners
            corners(l, t, rr, bb, BLOOD if heavy else ROAD)
    if pick is None and game.bag_side == side:                         # an empty cell is chosen
        c, r = game.bag_cell
        corners(gx + c * CELL, gy + r * CELL, gx + (c + 1) * CELL, gy + (r + 1) * CELL, GREY_C)


def item_picture(kind, turned=False):
    """The picture of a bag item: a weapon's sprite (turned upright when it lies turned), or the
    supply's big icon."""
    wkey = weapons.key_of(kind)
    if wkey:
        sprite = weapons.WEAPONS[wkey]["sprite"]
        return f"../weapons/{sprite}{'_r' if turned else ''}.png", 2
    return f"bag/big_{kind}.png", 1


def draw_item(kind, l, t, w, h, turned=False):
    """A bag item's picture in the middle of its w x h cells at (l, t)."""
    name, scale = item_picture(kind, turned)
    img = px.image(name)
    px.blit(name, l + (w * CELL - img.w * scale) // 2, t + (h * CELL - img.h * scale) // 2, scale)


# The hand slot in the body column (a weapon dropped here is taken in hand) and the "정리" button.
HAND_RECT = (14, 180, 150, 214)
TIDY_RECT = (0, 0, 0, 0)                 # set where the bag is drawn (draw_inventory)


def draw_ghost(game):
    """While a thing is carried over the bag's sheet: where it would land - its cells green when it
    fits there, red when it does not (2026-11-18 "커서로 정리할 수 있게")."""
    target = game.bag_target
    if game.bag_drag is None or target is None:
        return
    kind = game.bag_drag[1][0]
    c, r, turned, ok, into = target
    w, h = bag_grid.shape(kind, turned)
    gx, gy = SHEET_GRID
    l, t = gx + c * CELL, gy + r * CELL
    colour = (96, 168, 92) if ok else BLOOD
    for i in range(w):
        for j in range(h):
            cl, ct = l + i * CELL, t + j * CELL
            if c + i < bag_grid.BAG_GRID[0] and r + j < bag_grid.BAG_GRID[1]:
                px.frame(cl + 3, ct + 3, cl + CELL - 3, ct + CELL - 3, colour)
    corners(l, t, l + w * CELL, t + h * CELL, colour)


def draw_body_column(game):
    l, t = 22, 42
    hp = max(0, round(100 * game.hero.hp / HERO_HP))
    px.text(l, t, "몸", LIGHT, bold=True)
    px.text(l + 112, t, f"{hp}%", BLOOD if hp < 60 else LIGHT, bold=True, anchor="r")
    bx, by = l + 10, t + 26
    px.blit("bag/body.png", bx, by)
    cond = game.condition
    for sx, sy in WOUND_SPOTS[:cond.blows]:
        colour = BLOOD if cond.bleeding else (92, 40, 40)
        px.rect(bx + sx - 2, by + sy - 2, bx + sx + 2, by + sy + 2, colour)
    if cond.bleeding:
        px.text(l + 62, t + 40, "출혈", LIGHT)
        px.text(l + 62, t + 54, "피가 난다", BLOOD)
    elif cond.dressed:
        px.text(l + 62, t + 40, "붕대", LIGHT)
        px.text(l + 62, t + 54, "감았다", GREY_C)
    else:
        px.text(l + 62, t + 40, "다친 곳 없음", GREY_C)
    # the hand slot: a weapon dragged here from the bag is taken in hand (2026-11-18 bag step 2)
    hl, ht, hr, hb = HAND_RECT
    carrying = game.bag_drag is not None and game.bag_drag[0] == "bag" and weapons.key_of(game.bag_drag[1][0])
    over = carrying and hl <= game.bag_mouse[0] <= hr and ht <= game.bag_mouse[1] <= hb
    px.frame(hl, ht, hr, hb, (96, 168, 92) if over else ROAD if carrying else (70, 72, 76))
    px.text(l, t + 146, "손", GREY_C)
    held = game.hero.weapon                                   # the weapon in hand (Q: the next one)
    img = px.image(f"../weapons/{held['sprite']}.png")
    px.blit(f"../weapons/{held['sprite']}.png", l + 18, t + 150 - img.h)
    px.text(l + 40, t + 146, held["name"], LIGHT)
    px.text(l + 40, t + 160, "끌어다 놓기 · Q", GREY_C)


def draw_room_bar(x, y, used, total):
    """One segment a cell: how much of the sheet is taken (orange when nearly full)."""
    colour = ORANGE if used > total - 3 else ROAD
    for i in range(total):
        sx = x + i * 9
        px.rect(sx, y, sx + 7, y + 5, INK_C)
        px.rect(sx + 1, y + 1, sx + 6, y + 4, colour if i < used else (40, 40, 38))


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
    used, total = bag_grid.used_cells(game), bag_grid.BAG_GRID[0] * bag_grid.BAG_GRID[1]
    px.blit("bag/icon_backpack.png", sl, st - 30)
    px.text(sl + 20, st - 27, "배낭", LIGHT, bold=True)
    px.text(sr, st - 27, f"{used} / {total}칸", LIGHT, anchor="r")
    global TIDY_RECT                                                    # the "정리" button
    bw = px.width("정리") + 12
    TIDY_RECT = (sr - px.width(f"{used} / {total}칸") - bw - 10, st - 30, sr - px.width(f"{used} / {total}칸") - 10, st - 13)
    tl, tt, tr, tb = TIDY_RECT
    hover = tl <= game.bag_mouse[0] <= tr and tt <= game.bag_mouse[1] <= tb
    px.rect(tl, tt, tr, tb, (64, 66, 58) if hover else (44, 46, 42))
    px.frame(tl, tt, tr, tb, ROAD if hover else GREY_C)
    px.text((tl + tr) // 2, tt + 2, "정리", LIGHT, anchor="m")
    px.blit("bag/sheet.png", sl, st)
    draw_things(game, "bag", layout["bag"], pick if game.bag_side == "bag" else None)
    draw_ghost(game)
    draw_room_bar(sl + 8, sb + 6, used, total)
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
        px.text(px.CW - 22, y, f"{pick[4]}×{pick[5]}칸", GREY_C, anchor="r")
    else:
        px.text(150, y, "빈 칸", GREY_C)
    use_word = "줍기" if game.bag_side == "near" else "들기" if pick and weapons.key_of(pick[0]) else "쓰기"
    rows = ((("Enter", use_word), ("X", "내려놓기"),
             ("F", "같은 것 줍기"), ("Shift+F", "모두 줍기")),
            (("끌어 놓기", "옮기기·합치기"), ("두 번 클릭", "쓰기"), ("R", "돌리기"), ("T", "정리"), ("Tab", "닫기")))
    for row, keys in enumerate(rows):
        kx = 150
        for key, label in keys:
            kx = px.key_cap(kx, y + 16 + row * 16, key, label, LIGHT, INK_C, LIGHT)
    if game.bag_drag is not None:                                      # carried by the mouse
        kind = game.bag_drag[1][0]
        turned = game.bag_turned
        w, h = bag_grid.shape(kind, turned)
        gc, gr = game.bag_grab
        mx, my = game.bag_mouse
        draw_item(kind, round(mx) - gc * CELL - CELL // 2, round(my) - gr * CELL - CELL // 2, w, h, turned)
    else:
        draw_tooltip(game, layout)


def draw_tooltip(game, layout):
    """The thing under the mouse: its name, what it does, and how many (2026-11-18 bag step 2)."""
    spot = cell_at(*game.bag_mouse)
    if spot is None:
        return
    thing = bag_grid.at(layout[spot[0]], *spot[1:])
    if thing is None:
        return
    kind = thing[0]
    count = thing[1][4] if spot[0] == "bag" else 1
    name = item_name(kind) + (f" ×{count}" if count > 1 else "")
    line = item_text(kind)
    w = max(px.width(name, True), px.width(line)) + 14
    mx, my = round(game.bag_mouse[0]) + 12, round(game.bag_mouse[1]) + 14
    mx, my = min(mx, px.CW - w - 4), min(my, px.CH - 40)
    px.rect(mx, my, mx + w, my + 34, (24, 24, 26))
    px.frame(mx, my, mx + w, my + 34, ROAD)
    px.text(mx + 7, my + 3, name, ROAD, bold=True)
    px.text(mx + 7, my + 18, line, LIGHT)


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
    people = sum(1 for s in game.people if s.alive)
    lines = [(f"기차를 탔다 · 함께 탄 사람 {people}/{len(game.people)}", (236, 214, 150), 17),
             (f"챙긴 물자: {carried}", TEXT, 14),
             (f"쓰러뜨린 피폭체 {game.kills}" + (f" · 피폭 {game.exposure:.0f}%" if EXPOSURE_ON else ""), TEXT, 14),
             ("다음 구역은 아직 · R 다시", DIM, 13)]
    for i, (line, colour, px) in enumerate(lines):
        ui.text_center(WIDTH / 2, b + h - size(34) - i * size(36), line, colour, size(px))
    if CREDIT:                                      # a real-map area: the map data's licence asks for it
        ui.text_center(WIDTH / 2, b - size(16), CREDIT, DIM, size(11))
