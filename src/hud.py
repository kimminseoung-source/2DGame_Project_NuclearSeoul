"""Screen UI over the world (2026-11-15 "UI적인 측면을 많이 개선해 보자, 인벤토리 등등").

- bottom left: health as a segmented bar
- bottom middle: quick slots (bag contents with their keys)
- top left: the goal and how many infected are left
- above the slots: the latest message, fading away
- Tab: the bag (inventory) panel - item grid, the selected item's description, use it
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
BAG_ROWS = 7                  # rows shown in the bag list


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
    # health (bottom left)
    l, b = size(16), size(16)
    panel(l, b, l + size(200), b + size(46))
    ui.text(l + size(10), b + size(32), "체력", TEXT, size(13))
    seg_w = size(150) / HERO_HP
    for i in range(HERO_HP):
        x0 = l + size(40) + i * seg_w
        colour = (176, 54, 48) if i < hero.hp else (46, 30, 30)
        pico2d.draw_rectangle(x0 + size(2), b + size(12), x0 + seg_w - size(2), b + size(24), *colour, filled=True)
    # quick slots (bottom middle)
    items = bag_items(game)
    slot = size(52)
    total = max(3, len(items))
    x0 = WIDTH / 2 - total * (slot + size(6)) / 2
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
    if hero.sneaking:
        ui.text(l + size(10), b + size(56), "살금살금", (150, 190, 220), size(12))
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


def weight_bar(l, b, w, used, cap):
    pico2d.draw_rectangle(l, b, l + w, b + size(10), 30, 32, 36, filled=True)
    share = min(1.0, used / cap)
    colour = (120, 170, 110) if share < 0.75 else (200, 170, 80) if share < 1.0 else (190, 70, 60)
    pico2d.draw_rectangle(l, b, l + w * share, b + size(10), *colour, filled=True)
    ui.text(l + w + size(8), b + size(5), f"{used:.1f} / {cap:.1f}", TEXT, size(12))


def draw_inventory(game):
    """The bag as a list (Zomboid style): picture, name, count, weight; the weight bar on top;
    the selected row described. Up/Down select, Enter uses, X drops one, Tab closes."""
    w, h = size(600), size(330)
    l, b = WIDTH / 2 - w / 2, HEIGHT / 2 - h / 2
    pico2d.draw_rectangle(0, 0, WIDTH, HEIGHT, 0, 0, 0, 110, filled=True)
    panel(l, b, l + w, b + h, 235)
    ui.text(l + size(18), b + h - size(22), "배낭", TEXT, size(16))
    ui.text(l + size(80), b + h - size(22), "무게", DIM, size(12))
    weight_bar(l + size(120), b + h - size(27), size(150), bag_weight(game.bag), BAG_CAPACITY)
    ui.text(l + w - size(250), b + h - size(22), "W·S 또는 위·아래 선택 · Enter 사용 · X 버리기 · Tab 닫기", DIM, size(11))
    items = bag_items(game)
    list_w = size(330)
    lx, top = l + size(14), b + h - size(52)
    row = size(30)
    ui.text(lx + size(40), top + size(4), "물건", DIM, size(11))
    ui.text(lx + size(220), top + size(4), "개수", DIM, size(11))
    ui.text(lx + size(275), top + size(4), "무게", DIM, size(11))
    for i in range(7):
        rt = top - size(12) - i * row
        if i < len(items):
            kind, n = items[i]
            if i == game.bag_cursor:
                pico2d.draw_rectangle(lx, rt - row + size(3), lx + list_w, rt, 60, 54, 40, filled=True)
            draw_icon(kind, lx + size(18), rt - row / 2 + size(1), size(10))
            ui.text(lx + size(40), rt - row / 2, KINDS[kind][0], TEXT, size(13))
            ui.text(lx + size(225), rt - row / 2, str(n), TEXT, size(13))
            ui.text(lx + size(275), rt - row / 2, f"{weight_of(kind) * n:.1f}", DIM, size(12))
        pico2d.draw_line(lx, rt - row + size(2), lx + list_w, rt - row + size(2), 40, 42, 46)
    dl = lx + list_w + size(22)
    if game.bag_cursor < len(items):
        kind, n = items[game.bag_cursor]
        ui.text(dl, top - size(16), f"{KINDS[kind][0]} ×{n}", TEXT, size(15))
        for k, line in enumerate(KINDS[kind][3].split("\n")):
            ui.text(dl, top - size(46) - k * size(22), line, DIM, size(12))
        ui.text(dl, top - size(110), f"하나 무게 {weight_of(kind):.1f}", DIM, size(11))
        if kind == "bandage" or (kind == "pill" and EXPOSURE_ON):
            ui.text(dl, b + size(24), "Enter: 사용", (236, 214, 150), size(13))
    else:
        ui.text(dl, top - size(16), "비어 있음", DIM, size(14))


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
