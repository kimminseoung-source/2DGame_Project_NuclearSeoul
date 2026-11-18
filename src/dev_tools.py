"""Developer tools (2026-11-18 "디버그용 박스가 필요함", "개발용 설정창 테스트를 할 수 있게").

- F1: debug boxes over the world, only what decides hits (no numbers): walls and wrecks, the
  hero's blow toward the cursor, each infected's body parts (head / torso / legs) and its claw.
- F4: the dev settings panel (top right). Up/Down choose a row, Left/Right change it, Enter does it;
  or click a row (left = up / do, right = down). The game keeps running behind it.

Every setting is a row in ROWS, so a new one is one line. Values that live in other modules
(speeds, bleeding) are changed there, so the game uses them at once; R keeps them.
"""

from math import atan2, cos, hypot, sin

import pico2d
import sdl2

import area
import condition
import hero as hero_rules
import infected
import pixel_ui as px
import weapons
from settings import CHEST, DOT, HERO_HP, ZOMBIE_ARC

SPEEDS = (0.25, 0.5, 1.0, 2.0)
PANEL = (440, 34, 632)              # canvas px: left, top, right (the rows set the bottom)
ROW_H = 13
PANEL_EDGE, PANEL_BG = (196, 170, 92), (18, 18, 20, 225)
CHOSEN, LIGHT, GREY = (60, 58, 50, 255), (222, 216, 198), (140, 138, 130)


class Dev:
    def __init__(self):
        self.open = False            # F4: the panel
        self.boxes = False           # F1: debug boxes
        self.god = False             # blows do nothing, no bleeding
        self.speed = 1.0             # the whole game's time
        self.freeze = False          # the infected stand still
        self.no_spawn = False        # no new infected come in
        self.row = 0
        self.ate_press = False       # a click went to the panel: its release is not a blow


def _flip(attr):
    def change(game, step):
        setattr(game.dev, attr, not getattr(game.dev, attr))
    return change


def _on(value):
    return "켬" if value else "끔"


def _speed(game, step):
    i = SPEEDS.index(game.dev.speed) if game.dev.speed in SPEEDS else 2
    game.dev.speed = SPEEDS[max(0, min(len(SPEEDS) - 1, i + step))]


def _number(module, name, step, low, high):
    def change(game, s):
        setattr(module, name, round(max(low, min(high, getattr(module, name) + step * s)), 2))
    return change


def _senses(game, step):
    game.toggle_senses()


def _real(game, step):
    game.toggle_real()


def _heal(game, step):
    game.hero.hp = HERO_HP
    game.condition.bleeding = False


def _give(kind, n):
    def change(game, step):
        game.bag[kind] = game.bag.get(kind, 0) + n
        game.message = f"[개발] {kind} +{n}"
    return change


def _ammo(game, step):
    pistol = weapons.WEAPONS.get("pistol", {})
    game.ammo = pistol.get("shot", {}).get("rounds", 6)


def _spawn(crawler):
    def change(game, step):
        if game.aim[0] is None:
            x, y = game.hero.x + 120, game.hero.y
        else:
            x, y = game.mouse_world(*game.aim)
        game.zombies.append(infected.Zombie(game.zombie_look, x, y, crawler=crawler))
    return change


def _clear(game, step):
    for z in game.zombies:
        z.state, z.timer = "dead", 9


def _restart(game, step):
    game.reset()


# (label, value shown or None for an action, change(game, step))
ROWS = (
    ("공격 범위·히트박스 (F1)", lambda g: _on(g.dev.boxes), _flip("boxes")),
    ("무적", lambda g: _on(g.dev.god), _flip("god")),
    ("게임 속도", lambda g: f"x{g.dev.speed:g}", _speed),
    ("피폭체 멈춤", lambda g: _on(g.dev.freeze), _flip("freeze")),
    ("새 피폭체 안 옴", lambda g: _on(g.dev.no_spawn), _flip("no_spawn")),
    ("피폭체 감각 (F2)", lambda g: _on(g.senses), _senses),
    ("사실적 연출 (F3)", lambda g: _on(g.real), _real),
    ("주인공 속도", lambda g: f"{hero_rules.RUN_SPEED:g}", _number(hero_rules, "RUN_SPEED", 10, 30, 300)),
    ("피폭체 속도", lambda g: f"{infected.ZOMBIE_SPEED:g}", _number(infected, "ZOMBIE_SPEED", 10, 0, 300)),
    ("출혈 확률", lambda g: f"{condition.BLEED_CHANCE * 100:.0f}%", _number(condition, "BLEED_CHANCE", 0.1, 0, 1)),
    ("맞을 때 체력", lambda g: f"-{condition.BLOW_DAMAGE:g}%", _number(condition, "BLOW_DAMAGE", 1, 0, 100)),
    ("체력 채우기·출혈 멈춤", None, _heal),
    ("붕대 +3", None, _give("bandage", 3)),
    ("통조림 +3", None, _give("can", 3)),
    ("탄약 채우기", None, _ammo),
    ("피폭체 소환 (커서)", None, _spawn(False)),
    ("기어가는 피폭체 소환", None, _spawn(True)),
    ("피폭체 모두 없애기", None, _clear),
    ("다시 시작", None, _restart),
)


# ---------------------------------------------------------------------- input
def key(game, k):
    """True if the key was the dev tools' own (the game does not see it)."""
    dev = game.dev
    if k == sdl2.SDLK_F1:
        dev.boxes = not dev.boxes
        return True
    if k == sdl2.SDLK_F4:
        dev.open = not dev.open
        return True
    if not dev.open:
        return False
    if k in (sdl2.SDLK_UP, sdl2.SDLK_DOWN):
        dev.row = (dev.row + (1 if k == sdl2.SDLK_DOWN else -1)) % len(ROWS)
    elif k in (sdl2.SDLK_LEFT, sdl2.SDLK_RIGHT, sdl2.SDLK_RETURN):
        ROWS[dev.row][2](game, -1 if k == sdl2.SDLK_LEFT else 1)
    else:
        return False
    return True


def row_at(sx, sy):
    cx, cy = px.to_canvas(sx, sy)
    l, t, r = PANEL
    i = int((cy - t - 16) // ROW_H)
    return i if l <= cx <= r and 0 <= i < len(ROWS) and cy >= t + 16 else None


def click(game, sx, sy, right):
    """A mouse press: True if it landed on the panel."""
    dev = game.dev
    if not dev.open:
        return False
    cx, cy = px.to_canvas(sx, sy)
    l, t, r = PANEL
    if not (l <= cx <= r and t <= cy <= t + 18 + len(ROWS) * ROW_H):
        return False
    i = row_at(sx, sy)
    if i is not None:
        dev.row = i
        ROWS[i][2](game, -1 if right else 1)
    dev.ate_press = True
    return True


# ---------------------------------------------------------------------- drawing
def draw_panel(game):
    dev = game.dev
    if not dev.open:
        return
    l, t, r = PANEL
    b = t + 18 + len(ROWS) * ROW_H
    px.rect(l, t, r, b, PANEL_BG)
    px.frame(l, t, r, b, PANEL_EDGE)
    px.text(l + 6, t + 3, "개발 설정 (F4)", PANEL_EDGE, bold=True)
    px.text(r - 6, t + 3, "↑↓ ←→ Enter", GREY, anchor="r")
    for i, (label, value, _) in enumerate(ROWS):
        y = t + 17 + i * ROW_H
        if i == dev.row:
            px.rect(l + 2, y - 1, r - 2, y + ROW_H - 2, CHOSEN)
        px.text(l + 6, y, label, LIGHT if value else (196, 196, 170))
        if value:
            v = value(game)
            px.text(r - 6, y, v, (120, 200, 120) if v == "켬" else GREY if v == "끔" else PANEL_EDGE, anchor="r")


# The world canvas has DOT canvas px per world unit (< 1), so a 1-unit line falls between pixels and
# parts of it vanish: every mark is made of whole canvas pixels instead.
PIXEL = 1 / DOT


def _dot(x, y, colour):
    qx, qy = round(x * DOT) / DOT, round(y * DOT) / DOT
    pico2d.draw_rectangle(qx, qy, qx + PIXEL * 0.99, qy + PIXEL * 0.99, *colour, filled=True)


def _line(x0, y0, x1, y1, colour, gap=1):
    n = max(1, int(hypot(x1 - x0, y1 - y0) * DOT / gap))
    for i in range(n + 1):
        _dot(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, colour)


def _arc(x, y, radius, a0, a1, colour, gap=1):
    n = max(2, int(radius * abs(a1 - a0) * DOT / gap))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        _dot(x + cos(a) * radius, y + sin(a) * radius, colour)


def _wedge(x, y, radius, ang, half, colour, gap=1):
    """The area a blow covers: radius out from (x, y), half radians either side of ang."""
    _arc(x, y, radius, ang - half, ang + half, colour, gap)
    for a in (ang - half, ang + half):
        _line(x, y, x + cos(a) * radius, y + sin(a) * radius, colour, gap)


def _box(l, b, r, t, colour):
    _line(l, b, r, b, colour)
    _line(l, t, r, t, colour)
    _line(l, b, l, t, colour)
    _line(r, b, r, t, colour)


PART_COLOURS = {"head": (226, 70, 56), "torso": (196, 170, 92), "legs": (120, 160, 210)}


def draw_boxes(game, cx, cy):
    """F1: only what decides hits, no numbers (2026-11-18 "숫자는 빼고 공격 범위, 히트박스"):
    walls bodies bump into, the hero's blow, each infected's body parts and its claw."""
    if not game.dev.boxes:
        return
    for bl, bb, br, bt in area.near_blocks(cx, cy, cx + game.view_w, cy + game.view_h):
        _box(bl - cx, bb - cy, br - cx, bt - cy, (240, 150, 40))                  # walls, wrecks
    h = game.hero
    hx, hy = h.x - cx, h.y - cy
    _line(hx - 6, hy, hx + 6, hy, (255, 255, 255))                                # where claws aim
    _line(hx, hy - 6, hx, hy + 6, (255, 255, 255))
    w = h.weapon
    length = weapons.attack_range(w)
    if game.aim[0] is not None:                                                   # the blow toward the cursor
        tx, ty = game.mouse_world(*game.aim)
        ang = atan2(ty - (h.y + CHEST), tx - h.x)
        if w.get("shot"):                                                         # a gun: the bullet's lane
            half = w["shot"]["width"] / 2
            nx, ny = -sin(ang) * half, cos(ang) * half
            ex, ey = hx + cos(ang) * length, hy + CHEST + sin(ang) * length
            for sgn in (1, -1):
                _line(hx + nx * sgn, hy + CHEST + ny * sgn, ex + nx * sgn, ey + ny * sgn, (240, 220, 80), 2)
        else:
            half = w["cells"] * weapons.CELL_WORLD / 2 / length                   # as wide as the hit (draw_aim)
            _wedge(hx, hy + CHEST, length, ang, half, (240, 220, 80))
    for z in game.zombies:
        if not z.alive:
            continue
        zx, zy = z.x - cx, z.y - cy
        if z.prone:                                                               # a crawler: all of it is "밟기"
            hw = weapons.PART_HALF_WIDTH * 2
            _box(zx - hw, zy - 4, zx + hw, zy + 14, (214, 128, 52))
        else:
            hw = weapons.PART_HALF_WIDTH
            for part, low, high in weapons.PARTS:
                _box(zx - hw, zy + low, zx + hw, zy + high, PART_COLOURS[part])
        striking = z.state in ("windup", "strike")
        _wedge(zx, zy, z.reach + 8, z.heading, ZOMBIE_ARC,
               (255, 60, 50) if striking else (150, 60, 56), 1 if striking else 3)                     # its claw (bright when it comes)
