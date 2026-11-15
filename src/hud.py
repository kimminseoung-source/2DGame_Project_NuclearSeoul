"""Screen UI over the world (2026-11-15 "UI적인 측면을 많이 개선해 보자, 인벤토리 등등").

- bottom left: the status panel - health, a heartbeat line (its speed follows tension) and the
  status icons (tension/panic, bleeding, wounds, slowed, sneaking: condition.py)
- bottom middle: quick slots (bag contents with their keys)
- top left: the goal and how many infected are left
- above the slots: the latest message, fading away
- Tab: the inventory (2026-11-15, after the user's reference picture): the bag as a grid of
  item tiles with a weight bar, the body with its wounds and the gear in hand, and the items
  lying nearby with "take all"
- the area summary once the hero has left

Everything scales with the window (settings.UI_SCALE). Item icons are drawn here from simple
shapes so any new supply kind only needs an entry in supplies.KINDS.
"""

import pico2d

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
BAG_COLS, BAG_ROWS = 5, 3      # the bag grid


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
        ui.text_center(WIDTH / 2, size(92), game.message, (236, 214, 150), size(14))


def draw_status(game):
    """Bottom left: health segments, a heartbeat line moving at the heart rate, status icons."""
    hero, cond = game.hero, game.condition
    l, b, w, h = size(16), size(16), size(330), size(78)
    panel(l, b, l + w, b + h)
    ui.text(l + size(10), b + h - size(14), "체력", TEXT, size(12))
    seg_w = size(110) / HERO_HP
    for i in range(HERO_HP):
        x0 = l + size(46) + i * seg_w
        colour = (176, 54, 48) if i < hero.hp else (46, 30, 30)
        pico2d.draw_rectangle(x0 + size(2), b + h - size(20), x0 + seg_w - size(2), b + h - size(9), *colour, filled=True)
    bpm = cond.heart_rate()
    colour = (110, 200, 120) if cond.tension < 0.33 else (220, 170, 80) if cond.tension < 0.66 else (220, 80, 70)
    ui.text(l + size(176), b + h - size(14), f"{bpm} bpm", colour, size(12))
    # the heartbeat line: a flat trace with a spike every beat, scrolling with the clock
    gx, gy, gw = l + size(10), b + size(30), size(150)
    beat = 60.0 / bpm
    prev = None
    for k in range(61):
        t = game.clock - (60 - k) * 0.025
        phase = (t % beat) / beat
        bump = 0.0
        if phase < 0.06:
            bump = phase / 0.06
        elif phase < 0.12:
            bump = 1 - (phase - 0.06) / 0.06 * 1.6
        elif phase < 0.18:
            bump = -0.6 + (phase - 0.12) / 0.06 * 0.6
        point = (gx + gw * k / 60, gy + bump * size(12))
        if prev:
            pico2d.draw_line(*prev, *point, *colour)
        prev = point
    # status icons: a coloured tile with a short word, the stronger the brighter
    x = l + size(170)
    for label, tint, level in cond.moodles(hero)[:4]:
        tile = size(24)
        if x + tile * 1.45 > l + w - size(4):
            break
        pico2d.draw_rectangle(x, b + size(18), x + tile * 1.45, b + size(18) + tile,
                              *(round(c * (0.55 + 0.15 * level)) for c in tint), filled=True)
        ui.text_center(x + tile * 0.72, b + size(18) + tile / 2, label, (245, 240, 230), size(10))
        x += tile * 1.45 + size(3)


def weight_bar(l, b, w, used, cap):
    pico2d.draw_rectangle(l, b, l + w, b + size(10), 30, 32, 36, filled=True)
    share = min(1.0, used / cap)
    colour = (120, 170, 110) if share < 0.75 else (200, 170, 80) if share < 1.0 else (190, 70, 60)
    pico2d.draw_rectangle(l, b, l + w * share, b + size(10), *colour, filled=True)
    ui.text(l + w + size(8), b + size(5), f"{used:.1f} / {cap:.1f}", TEXT, size(12))


def draw_gear_icon(kind, x, y, s):
    """Gear in hand: the machete, the bag."""
    if kind == "machete":
        pico2d.draw_rectangle(x - s * 0.9, y - s * 0.12, x + s * 0.45, y + s * 0.12, 190, 196, 200, filled=True)
        pico2d.draw_rectangle(x + s * 0.45, y - s * 0.1, x + s * 0.9, y + s * 0.1, 80, 52, 34, filled=True)
    else:
        pico2d.draw_rectangle(x - s * 0.6, y - s * 0.7, x + s * 0.6, y + s * 0.5, 96, 84, 62, filled=True)
        pico2d.draw_rectangle(x - s * 0.35, y + s * 0.5, x + s * 0.35, y + s * 0.75, 70, 60, 44, filled=True)


def tile(l, t, size_px, selected=False):
    panel(l, t - size_px, l + size_px, t, 255)
    if selected:
        pico2d.draw_rectangle(l - 2, t - size_px - 2, l + size_px + 2, t + 2, 220, 190, 110)


def draw_body(cx, base, height, injuries):
    """A plain standing figure; each wound a dark red mark at a fixed spot by its kind."""
    u = height / 100
    grey = (150, 150, 152)
    pico2d.draw_circle(cx, base + 90 * u, round(9 * u), *grey, filled=True)                 # head
    pico2d.draw_rectangle(cx - 13 * u, base + 46 * u, cx + 13 * u, base + 80 * u, *grey, filled=True)   # body
    for sx in (-1, 1):
        pico2d.draw_rectangle(cx + sx * 14 * u - 4 * u, base + 44 * u, cx + sx * 14 * u + 4 * u, base + 78 * u,
                              *grey, filled=True)                                           # arms
        pico2d.draw_rectangle(cx + sx * 6 * u - 5 * u, base, cx + sx * 6 * u + 5 * u, base + 46 * u,
                              *grey, filled=True)                                           # legs
    spots = {"scratch": [(-14, 62), (8, 30), (14, 70)], "laceration": [(-4, 64), (-6, 20)], "bite": [(14, 58), (0, 86)]}
    used = {}
    for wound in injuries:
        k = used.get(wound["kind"], 0)
        used[wound["kind"]] = k + 1
        dx, dy = spots[wound["kind"]][k % len(spots[wound["kind"]])]
        colour = (150, 20, 20) if wound.get("bleed", 0) > 0 else (90, 40, 40)
        pico2d.draw_rectangle(cx + dx * u - 3 * u, base + dy * u - 3 * u, cx + dx * u + 3 * u, base + dy * u + 3 * u,
                              *colour, filled=True)


def nearby_items(game):
    from supplies import PICK_RANGE
    return [s for s in game.supplies if not s.taken
            and (s.x - game.hero.x) ** 2 + (s.y - game.hero.y) ** 2 <= (PICK_RANGE * 2.5) ** 2]


def draw_inventory(game):
    """Inventory after the user's reference: bag grid + weight | body, wounds, gear | nearby."""
    pico2d.draw_rectangle(0, 0, WIDTH, HEIGHT, 0, 0, 0, 120, filled=True)
    top, bottom = HEIGHT - size(70), size(110)
    cols, rows = BAG_COLS, BAG_ROWS
    cell, gap = size(42), size(6)
    # ---- bag (left)
    bl = size(40)
    bw = cols * (cell + gap) + size(24)
    panel(bl, bottom, bl + bw, top, 235)
    ui.text(bl + size(12), top - size(18), "배낭", TEXT, size(15))
    weight_bar(bl + size(54), top - size(23), size(110), bag_weight(game.bag), BAG_CAPACITY)
    items = bag_items(game)
    gx, gy = bl + size(12), top - size(44)
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        tl, tt = gx + c * (cell + gap), gy - r * (cell + gap)
        tile(tl, tt, cell, i == game.bag_cursor)
        if i < len(items):
            kind, n = items[i]
            draw_icon(kind, tl + cell / 2, tt - cell / 2, cell * 0.3)
            ui.text(tl + cell - size(16), tt - cell + size(10), str(n), TEXT, size(11))
    # selected item, under the grid
    dy = gy - rows * (cell + gap) - size(8)
    if game.bag_cursor < len(items):
        kind, n = items[game.bag_cursor]
        ui.text(bl + size(12), dy, f"{KINDS[kind][0]} ×{n} · 하나 {weight_of(kind):.1f}", TEXT, size(13))
        ui.text(bl + size(12), dy - size(20), KINDS[kind][3].replace("\n", " "), DIM, size(11))
    ui.text(bl + size(12), bottom + size(14), "방향키/WASD 선택 · Enter 사용 · X 버리기", DIM, size(10))
    # ---- body and gear (middle)
    ml = bl + bw + size(14)
    mw = size(210)
    panel(ml, bottom, ml + mw, top, 235)
    ui.text(ml + size(12), top - size(18), "몸", TEXT, size(15))
    draw_body(ml + size(55), bottom + size(50), size(150), game.condition.injuries)
    sx = ml + size(110)
    ui.text(sx, top - size(52), f"체력 {game.hero.hp}/{HERO_HP}", TEXT, size(12))
    ui.text(sx, top - size(74), f"심박 {game.condition.heart_rate()}", DIM, size(12))
    ui.text(sx, top - size(96), f"긴장 {game.condition.tension * 100:.0f}%", DIM, size(12))
    wounds = game.condition.injuries
    for k, wound in enumerate(wounds[:3]):
        state = "출혈" if wound["bleed"] > 0 else ("치료됨" if wound.get("dressed") else "")
        ui.text(sx, top - size(126) - k * size(20), f"{wound['name']} {state}", (200, 120, 110), size(11))
    if not wounds:
        ui.text(sx, top - size(126), "부상 없음", DIM, size(11))
    for k, (label, gear) in enumerate((("손", "machete"), ("등", "bag"))):
        tl, tt = ml + size(110) + k * size(50), bottom + size(62)
        tile(tl, tt, size(44))
        draw_gear_icon(gear, tl + size(22), tt - size(22), size(16))
        ui.text_center(tl + size(22), tt + size(9), label, DIM, size(10))
    # ---- nearby (right)
    rl = ml + mw + size(14)
    rw = WIDTH - size(40) - rl
    panel(rl, bottom, rl + rw, top, 235)
    ui.text(rl + size(12), top - size(18), "근처 물건", TEXT, size(15))
    near = nearby_items(game)
    ncols = max(1, int((rw - size(24)) // (cell + gap)))
    for i, item in enumerate(near[:ncols * 4]):
        c, r = i % ncols, i // ncols
        tl, tt = rl + size(12) + c * (cell + gap), top - size(44) - r * (cell + gap)
        tile(tl, tt, cell)
        draw_icon(item.kind, tl + cell / 2, tt - cell / 2, cell * 0.3)
        ui.text_center(tl + cell / 2, tt - cell + size(9), item.name, DIM, size(9))
    if not near:
        ui.text(rl + size(12), top - size(50), "주변에 주울 것이 없다", DIM, size(12))
    ui.text(rl + size(12), bottom + size(14), "F 모두 수집 · Tab 닫기", (236, 214, 150), size(11))


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
