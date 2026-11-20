"""Developer tools (2026-11-18 "디버그용 박스가 필요함", "개발용 설정창 테스트를 할 수 있게").

- F1: debug boxes over the world, only what decides hits (no numbers): walls and wrecks, the
  hero's blow toward the cursor, each infected's body parts (head / torso / legs) and its claw.
- F5: sight - each infected's cone out to where it spots the hero at once ("!").
- F6: sound - every noise the hero makes as a ring as far as it carries ("?"), and the entrances
  a loud one calls new infected through (2026-11-18 "F5, F6 나눠 주세요, 디버그와 동일하게").
- F7: the AI director (director.py) - its intensity over the last minute, coloured by state
  (build / peak / relax), and when the next infected comes in.
- F4: the dev settings panel (top right). Up/Down choose a row, Left/Right change it, Enter does it;
  or click a row (left = up / do, right = down). The game keeps running behind it.
  Number rows are sliders with an icon (2026-11-18 "윈도우 밝기처럼 조절", "숫자로도 가능하고"):
  drag or click the bar, or click the number box and type a value (Enter sets it, Esc cancels).

Every setting is a row in ROWS, so a new one is one line. Values that live in other modules
(speeds, bleeding) are changed there, so the game uses them at once; R keeps them.
"""

from math import atan2, cos, hypot, sin

import pico2d
import sdl2

import area
import character_look
import slash_fx
import daylight
import vision_cone
import condition
import hero as hero_rules
import infected
import pixel_ui as px
import weapons
from settings import CHEST, DOT, HERO_HP, ZOMBIE_ARC
from weapons import BODY_CONTACT

PANEL = (368, 30, 632)              # canvas px: left, top, right (the rows set the bottom)
ROW_H = 14
PANEL_EDGE, PANEL_BG = (196, 170, 92), (18, 18, 20, 230)
CHOSEN, LIGHT, GREY = (60, 58, 50, 255), (222, 216, 198), (140, 138, 130)
TRACK = (PANEL[0] + 122, PANEL[2] - 48)    # a slider's bar, canvas x
BOX = (PANEL[2] - 42, PANEL[2] - 4)        # a slider's number box, canvas x
FILL, KNOB = (78, 140, 220), (232, 236, 240)

# 7 x 7 pixel icons for the slider rows ('#' = a pixel)
ICONS = {
    "clock": (" ##### ", "#  #  #", "#  #  #", "#  ## #", "#     #", "#     #", " ##### "),
    "run":   ("   ##  ", "   ##  ", " ####  ", "#  # # ", "  ##   ", " #  #  ", "#    # "),
    "zed":   (" ##### ", "#######", "# # # #", "#######", " # # # ", " ##### ", "  # #  "),
    "eye":   ("       ", "  ###  ", " #   # ", "#  #  #", " #   # ", "  ###  ", "       "),
    "drop":  ("   #   ", "  ###  ", "  ###  ", " ##### ", " ##### ", " ##### ", "  ###  "),
    "heart": (" ## ## ", "#######", "#######", "#######", " ##### ", "  ###  ", "   #   "),
}


class Dev:
    def __init__(self):
        self.open = False            # F4: the panel
        self.boxes = False           # F1: debug boxes
        self.sight = False           # F5: the infected's sight
        self.sounds = False          # F6: the hero's noises and the entrances they call through
        self.director = False        # F7: the AI director's intensity graph
        self.tells = True            # where a winding-up claw will land, faintly on the ground (attack_tells)
        self.noises = []             # [x, y, radius, age] of noises the hero made (F6 rings)
        self.god = False             # blows do nothing, no bleeding
        self.speed = 1.0             # the whole game's time
        self.freeze = False          # the infected stand still
        self.no_spawn = False        # no new infected come in
        self.ate_press = False       # a click went to the panel: its release is not a blow
        self.drag = None             # the slider row being dragged
        self.editing = None          # the slider row whose number is being typed
        self.text = ""
        self.scroll = 0              # the first row shown (the panel scrolls)
        self.row = 1                 # (row 0 is a heading)


def _flip(attr):
    def change(game, step):
        setattr(game.dev, attr, not getattr(game.dev, attr))
    return change


def _on(value):
    return "켬" if value else "끔"


def _slider(label, icon, get, put, low, high, step, show):
    """A number row: (label, shown value, change by a step, the slider's spec)."""
    spec = {"icon": icon, "get": get, "put": put, "low": low, "high": high, "step": step}

    def change(game, s):
        set_value(game, spec, get(game) + step * s)
    return (label, lambda g: show(get(g)), change, spec)


def set_value(game, spec, v, snap=True):
    """Keep inside the range (snapped to the step when dragged or stepped; a typed number stays
    as typed) and put it where the game reads it."""
    low, high, step = spec["low"], spec["high"], spec["step"]
    if snap:
        v = low + round((v - low) / step) * step
    spec["put"](game, round(max(low, min(high, v)), 4))


def _module_value(module, name, scale=1.0):
    return (lambda g: getattr(module, name) * scale,
            lambda g, v: setattr(module, name, v / scale))


def _fast(game, step):
    """Experiment "빠르게": the hero's actions at 1.3x (undoes TEMPO for the hero only)."""
    hero_rules.Hero.action_speed = 1.0 if hero_rules.Hero.action_speed > 1.0 else 1.3


def _new_look(game, step):
    """The 8-direction PixelLab hero on/off, to compare with the old side sheets."""
    character_look.DirLook.on = not character_look.DirLook.on


def _jolt():
    import play
    return play.JOLTS["heavy"]


def _set_jolt(v):
    import play
    play.JOLTS["heavy"] = (v, *play.JOLTS["heavy"][1:])


def _fx_sprites(game, step):
    slash_fx.SpriteFx.on = not slash_fx.SpriteFx.on


def _key_poses(game, step):
    """Key-pose attacks (2 pictures + trail) on/off, to compare with the turning weapon."""
    character_look.DirLook.key_poses = not character_look.DirLook.key_poses


VARIANT_NAMES = {None: "기본 (그림 폴더가 정한 것)", "downward": "도끼 내려치기", "heavy": "양손 휘두르기",
                 "bash": "머리 위 내려치기", "baseball": "방망이 휘두르기",
                 "greatsword": "양손 검 내려 베기", "samurai": "사무라이 (방망이 준비 + 검 베기)"}
COUNT_NAMES = {2: "2장 (준비·치기)", 3: "3장 (+회복)", 0: "전체 10장"}


def _variants(game):
    look = game.hero_look
    return [None] + (look.variants() if hasattr(look, "variants") else [])


def _next_variant(game, step):
    """Try another attack motion in the game (3D hero, keyframes.json "variants")."""
    names = _variants(game)
    i = names.index(character_look.DirLook.variant) if character_look.DirLook.variant in names else 0
    character_look.DirLook.variant = names[(i + step) % len(names)]


def _next_count(game, step):
    order = [2, 3, 0]
    i = order.index(character_look.DirLook.key_count)
    character_look.DirLook.key_count = order[(i + step) % len(order)]


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


# (label, value shown or None for an action, change(game, step)[, slider spec]); a 1-tuple is a
# section heading (2026-11-18 "개발 설정창을 좀 다듬어 줘, 스크롤도")
ROWS = (
    ("보기",),
    ("공격 범위·히트박스 (F1)", lambda g: _on(g.dev.boxes), _flip("boxes")),
    ("시야 범위 (F5)", lambda g: _on(g.dev.sight), _flip("sight")),
    ("소리 범위 (F6)", lambda g: _on(g.dev.sounds), _flip("sounds")),
    ("AI 디렉터 (F7)", lambda g: _on(g.dev.director), _flip("director")),
    ("시야와 빛",),
    _slider("낮 시야 길이", "eye", *_module_value(daylight, "DAY_RANGE"), 150, 900, 10, lambda v: f"{v:g}"),
    _slider("밤 시야 길이", "eye", *_module_value(daylight, "NIGHT_RANGE"), 100, 700, 10, lambda v: f"{v:g}"),
    _slider("몸 주변 원", "eye", *_module_value(vision_cone, "NEAR_GLOW"), 40, 300, 10, lambda v: f"{v:g}"),
    _slider("주변 어둡기", "eye", *_module_value(vision_cone, "GLOW_DARK", 100), 0, 100, 5, lambda v: f"{v:.0f}%"),
    _slider("낮 화면 어둡기", "clock", *_module_value(daylight, "FOG_DAY"), 0, 255, 5, lambda v: f"{v:g}"),
    _slider("밤 화면 어둡기", "clock", *_module_value(daylight, "FOG_NIGHT"), 0, 255, 5, lambda v: f"{v:g}"),
    _slider("시각", "clock", lambda g: g.daylight.hour, lambda g, v: setattr(g.daylight, "hour", v % 24), 0, 23.5, 0.5,
            lambda v: f"{int(v):02d}:{int(v % 1 * 60):02d}"),
    ("주인공",),
    ("무적", lambda g: _on(g.dev.god), _flip("god")),
    ("새 주인공 그림 (8방향)", lambda g: _on(character_look.DirLook.on), _new_look),
    ("핵심 자세 공격", lambda g: _on(character_look.DirLook.key_poses), _key_poses),
    ("공격 동작 (3D 주인공)", lambda g: VARIANT_NAMES.get(character_look.DirLook.variant, character_look.DirLook.variant),
     _next_variant),
    ("공격 장수 (3D 주인공)", lambda g: COUNT_NAMES[character_look.DirLook.key_count], _next_count),
    ("타격 효과 그림", lambda g: _on(slash_fx.SpriteFx.on), _fx_sprites),
    ("실험: 빠르게 (주인공 동작 1.3배)", lambda g: _on(hero_rules.Hero.action_speed > 1.0), _fast),
    _slider("주인공 속도", "run", *_module_value(hero_rules, "RUN_SPEED"), 30, 300, 10, lambda v: f"{v:g}"),
    _slider("강한 타격 멈춤", "clock", lambda g: _jolt()[0], lambda g, v: _set_jolt(v), 0, 0.3, 0.01, lambda v: f"{v:.2f}s"),
    _slider("공격 뒤 걸어 나가기", "run", *_module_value(hero_rules, "CANCEL_MOVE"), 0, 0.5, 0.02, lambda v: f"{v:.2f}s"),
    _slider("연속 공격 시점", "clock", *_module_value(hero_rules, "CANCEL_BLOW", 100), 0, 100, 5, lambda v: f"{v:.0f}%"),
    _slider("클릭 공격 준비 줄이기", "clock", *_module_value(weapons, "QUICK_SKIP", 100), 0, 90, 5, lambda v: f"{v:.0f}%"),
    _slider("출혈 확률", "drop", *_module_value(condition, "BLEED_CHANCE", 100), 0, 100, 5, lambda v: f"{v:.0f}%"),
    _slider("맞을 때 체력", "heart", *_module_value(condition, "BLOW_DAMAGE"), 0, 100, 1, lambda v: f"-{v:g}%"),
    ("체력 채우기·출혈 멈춤", None, _heal),
    ("붕대 +3", None, _give("bandage", 3)),
    ("통조림 +3", None, _give("can", 3)),
    ("탄약 채우기", None, _ammo),
    ("피폭체",),
    ("피폭체 멈춤", lambda g: _on(g.dev.freeze), _flip("freeze")),
    ("새 피폭체 안 옴", lambda g: _on(g.dev.no_spawn), _flip("no_spawn")),
    ("피폭체 공격 예고 (빨간 범위)", lambda g: _on(g.dev.tells), _flip("tells")),
    ("피폭체 감각 (F2)", lambda g: _on(g.senses), _senses),
    _slider("피폭체 속도", "zed", *_module_value(infected, "ZOMBIE_SPEED"), 0, 300, 10, lambda v: f"{v:g}"),
    _slider("피폭체 발견 거리", "eye", *_module_value(infected, "SPOT_DIST"), 30, 400, 10, lambda v: f"{v:g}"),
    ("피폭체 소환 (커서)", None, _spawn(False)),
    ("기어가는 피폭체 소환", None, _spawn(True)),
    ("피폭체 모두 없애기", None, _clear),
    ("게임",),
    _slider("게임 속도", "clock", lambda g: g.dev.speed, lambda g, v: setattr(g.dev, "speed", v), 0.25, 2.0, 0.25,
            lambda v: f"x{v:g}"),
    ("사실적 연출 (F3)", lambda g: _on(g.real), _real),
    ("다시 시작", None, _restart),
)
VISIBLE = 20                        # rows shown at once; the mouse wheel / arrows scroll the rest


def heading(i):
    return len(ROWS[i]) == 1


def keep_in_view(dev):
    """Scroll so the chosen row is on screen."""
    top = dev.row - 1 if dev.row > 0 and heading(dev.row - 1) else dev.row      # its heading too
    dev.scroll = max(min(dev.scroll, top), dev.row - VISIBLE + 1)
    dev.scroll = max(0, min(dev.scroll, len(ROWS) - VISIBLE))


def wheel(game, amount):
    """The mouse wheel over the open panel scrolls it. True if it did (the game does not zoom then)."""
    dev = game.dev
    if not dev.open:
        return False
    x, y = sdl2.c_int(), sdl2.c_int()
    sdl2.SDL_GetMouseState(x, y)
    cx, cy = px.to_canvas(x.value, y.value)
    l, t, r = PANEL
    if not (l <= cx <= r and t <= cy <= t + 18 + VISIBLE * ROW_H):
        return False
    dev.scroll = max(0, min(len(ROWS) - VISIBLE, dev.scroll - amount * 2))
    return True


# ---------------------------------------------------------------------- input
def key(game, k):
    """True if the key was the dev tools' own (the game does not see it)."""
    dev = game.dev
    if k == sdl2.SDLK_F1:
        dev.boxes = not dev.boxes
        return True
    if k == sdl2.SDLK_F5:
        dev.sight = not dev.sight
        return True
    if k == sdl2.SDLK_F6:
        dev.sounds = not dev.sounds
        return True
    if k == sdl2.SDLK_F7:
        dev.director = not dev.director
        return True
    if k == sdl2.SDLK_F4:
        dev.open = not dev.open
        return True
    if not dev.open:
        return False
    if dev.editing is not None:                        # typing a number: every key goes here
        typing(game, k)
        return True
    if k in (sdl2.SDLK_UP, sdl2.SDLK_DOWN):
        step = 1 if k == sdl2.SDLK_DOWN else -1
        dev.row = (dev.row + step) % len(ROWS)
        while heading(dev.row):                        # headings are skipped
            dev.row = (dev.row + step) % len(ROWS)
        keep_in_view(dev)
    elif k in (sdl2.SDLK_LEFT, sdl2.SDLK_RIGHT, sdl2.SDLK_RETURN):
        ROWS[dev.row][2](game, -1 if k == sdl2.SDLK_LEFT else 1)
    else:
        return False
    return True


DIGITS = {**{sdl2.SDLK_0 + n: str(n) for n in range(10)}, sdl2.SDLK_KP_0: "0",
          **{sdl2.SDLK_KP_1 + n: str(n + 1) for n in range(9)},
          sdl2.SDLK_PERIOD: ".", sdl2.SDLK_KP_PERIOD: ".", sdl2.SDLK_MINUS: "-", sdl2.SDLK_KP_MINUS: "-"}


def typing(game, k):
    dev = game.dev
    if k in DIGITS and len(dev.text) < 7:
        dev.text += DIGITS[k]
    elif k == sdl2.SDLK_BACKSPACE:
        dev.text = dev.text[:-1]
    elif k in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
        try:
            set_value(game, ROWS[dev.editing][3], float(dev.text), snap=False)
        except ValueError:
            pass                                       # nothing typed (or only "-"): keep the value
        dev.editing, dev.text = None, ""
    elif k == sdl2.SDLK_ESCAPE:
        dev.editing, dev.text = None, ""


def cancel_typing(game):
    """Esc while typing a number cancels it (main.py asks before Esc closes anything)."""
    if game.dev.open and game.dev.editing is not None:
        typing(game, sdl2.SDLK_ESCAPE)
        return True
    return False


def slide_to(game, i, cx):
    spec = ROWS[i][3]
    share = (cx - TRACK[0]) / (TRACK[1] - TRACK[0])
    set_value(game, spec, spec["low"] + max(0.0, min(1.0, share)) * (spec["high"] - spec["low"]))


def drag(game, sx, sy):
    """Mouse moves: while a slider is held it follows. True if it did."""
    if game.dev.drag is None:
        return False
    slide_to(game, game.dev.drag, px.to_canvas(sx, sy)[0])
    return True


def row_at(game, sx, sy):
    cx, cy = px.to_canvas(sx, sy)
    l, t, r = PANEL
    k = int((cy - t - 16) // ROW_H)
    i = game.dev.scroll + k
    if not (l <= cx <= r and 0 <= k < VISIBLE and 0 <= i < len(ROWS) and cy >= t + 16) or heading(i):
        return None
    return i


def click(game, sx, sy, right):
    """A mouse press: True if it landed on the panel."""
    dev = game.dev
    if not dev.open:
        return False
    cx, cy = px.to_canvas(sx, sy)
    l, t, r = PANEL
    if not (l <= cx <= r and t <= cy <= t + 18 + VISIBLE * ROW_H):
        return False
    if cx >= r - 5:                                    # the scroll bar: jump there
        share = (cy - t - 16) / (VISIBLE * ROW_H)
        dev.scroll = max(0, min(len(ROWS) - VISIBLE, round(share * len(ROWS) - VISIBLE / 2)))
        dev.ate_press = True
        return True
    i = row_at(game, sx, sy)
    if dev.editing is not None and i != dev.editing:   # clicked elsewhere: typing is done
        typing(game, sdl2.SDLK_RETURN)
    if i is not None:
        dev.row = i
        if len(ROWS[i]) > 3 and not right:              # a slider: the bar, or the number box
            if TRACK[0] - 4 <= cx <= TRACK[1] + 4:
                dev.drag = i
                slide_to(game, i, cx)
            elif BOX[0] <= cx <= BOX[1]:
                dev.editing, dev.text = i, ""
        else:
            ROWS[i][2](game, -1 if right else 1)
    dev.ate_press = True
    return True


def release(game):
    game.dev.ate_press = False
    game.dev.drag = None


# ---------------------------------------------------------------------- drawing
def draw_panel(game):
    dev = game.dev
    if not dev.open:
        return
    l, t, r = PANEL
    b = t + 18 + VISIBLE * ROW_H
    px.rect(l, t, r, b, PANEL_BG)
    px.frame(l, t, r, b, PANEL_EDGE)
    px.text(l + 6, t + 3, "개발 설정 (F4)", PANEL_EDGE, bold=True)
    px.text(r - 8, t + 3, "휠 스크롤 · 끌기 · 숫자 입력", GREY, anchor="r")
    # the scroll bar on the right edge: where the shown rows are in the whole list
    bar_t, bar_b = t + 16, b - 2
    px.rect(r - 4, bar_t, r - 2, bar_b, (40, 42, 46))
    top = bar_t + round((bar_b - bar_t) * dev.scroll / len(ROWS))
    bot = bar_t + round((bar_b - bar_t) * min(len(ROWS), dev.scroll + VISIBLE) / len(ROWS))
    px.rect(r - 4, top, r - 2, bot, (150, 140, 110))
    for k in range(VISIBLE):
        i = dev.scroll + k
        if i >= len(ROWS):
            break
        row = ROWS[i]
        y = t + 17 + k * ROW_H
        if heading(i):                                 # a section heading
            px.text(l + 6, y, row[0], PANEL_EDGE, bold=True)
            px.rect(l + 8 + px.width(row[0], True), y + 6, r - 8, y + 6, (70, 66, 52))
            continue
        label, value = row[0], row[1]
        if i == dev.row:
            px.rect(l + 2, y - 1, r - 2, y + ROW_H - 2, CHOSEN)
        if len(row) > 3:
            draw_slider(game, i, row, y)
            continue
        px.text(l + 6, y, label, LIGHT if value else (196, 196, 170))
        if value:
            v = value(game)
            px.text(r - 6, y, v, (120, 200, 120) if v == "켬" else GREY if v == "끔" else PANEL_EDGE, anchor="r")


def draw_icon(name, x, y, colour):
    for j, line in enumerate(ICONS[name]):
        for k, ch in enumerate(line):
            if ch == "#":
                px.rect(x + k, y + j, x + k, y + j, colour)


def draw_slider(game, i, row, y):
    """[icon] label  ====o-----  [ 140 ]"""
    label, value, _, spec = row
    l = PANEL[0]
    draw_icon(spec["icon"], l + 6, y + 2, LIGHT)
    px.text(l + 17, y, label, LIGHT)
    tl, tr = TRACK
    share = (spec["get"](game) - spec["low"]) / (spec["high"] - spec["low"])
    kx = round(tl + max(0.0, min(1.0, share)) * (tr - tl))
    mid = y + 6
    px.rect(tl, mid, tr, mid + 1, (96, 98, 102))                  # the bar
    px.rect(tl, mid, kx, mid + 1, FILL)                           # filled up to the knob
    px.rect(kx - 2, mid - 3, kx + 2, mid + 4, (20, 22, 26))      # the knob, round-ish
    px.rect(kx - 1, mid - 3, kx + 1, mid + 4, KNOB)
    px.rect(kx - 2, mid - 2, kx + 2, mid + 3, KNOB)
    px.rect(kx - 1, mid - 1, kx + 1, mid + 2, FILL)
    bl, br = BOX
    editing = game.dev.editing == i
    px.rect(bl, y, br, y + 11, (44, 46, 50) if editing else (28, 30, 34))
    px.frame(bl, y, br, y + 11, FILL if editing else (70, 72, 76))
    shown = game.dev.text + ("_" if int(game.clock * 3) % 2 == 0 else " ") if editing else value(game)
    px.text(br - 3, y, shown, LIGHT if editing else PANEL_EDGE, anchor="r")


# Ground marks in whole canvas pixels (moved to ground_marks.py, shared with attack_tells.py)
from ground_marks import PIXEL, arc as _arc, box as _box, dot as _dot, line as _line, wedge as _wedge  # noqa: E402


PART_COLOURS = {"head": (226, 70, 56), "torso": (196, 170, 92), "legs": (120, 160, 210)}


def draw_boxes(game, cx, cy):
    """F1: only what decides hits, no numbers (2026-11-18 "숫자는 빼고 공격 범위, 히트박스"):
    walls bodies bump into, the hero's blow, each infected's body parts and its claw."""
    if not game.dev.boxes:
        return
    pad = area.BODY_PAD
    for bl, bb, br, bt in area.near_blocks(cx, cy, cx + game.view_w, cy + game.view_h):
        _box(bl - cx, bb - cy, br - cx, bt - cy, (240, 150, 40))                  # walls, wrecks
        # where a body's feet (the white +) stop: the rect grown by area.blocked's padding
        _box(bl - pad - cx, bb - pad / 2 - cy, br + pad - cx, bt + pad / 2 - cy, (240, 150, 40), 3)
    h = game.hero
    hx, hy = h.x - cx, h.y - cy
    _line(hx - 6, hy, hx + 6, hy, (255, 255, 255))                                # where claws aim
    _line(hx, hy - 6, hx, hy + 6, (255, 255, 255))
    hand = h.hand                             # where the weapon is held
    if hand:
        _box(hand[0] - 1.5, hand[1] - 1.5, hand[0] + 1.5, hand[1] + 1.5, (255, 70, 70))
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
            # exactly the melee hit (play.update): an infected whose chest point (white dot) is
            # inside this wedge - reach + lunge + half a body, +-arc - or touching the hero
            # (BODY_CONTACT ring) is hit; the part only counts on a full charge, else the torso
            span = length + weapons.BODY_MARGIN
            _wedge(hx, hy + CHEST, span, ang, w["arc"], (240, 220, 80))
            _arc(hx, hy + CHEST, BODY_CONTACT, -3.15, 3.15, (240, 220, 80), 2)
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
        _box(zx - 1.5 * PIXEL, zy + CHEST - 1.5 * PIXEL, zx + 1.5 * PIXEL, zy + CHEST + 1.5 * PIXEL, (255, 255, 255))   # the point a swing must reach
        striking = z.state in ("windup", "strike")
        _wedge(zx, zy, z.reach + 8, z.heading, ZOMBIE_ARC,
               (255, 60, 50) if striking else (150, 60, 56), 1 if striking else 3)                     # its claw (bright when it comes)


SIGHT, NEAR = (110, 150, 240), (150, 190, 255)
NOISE = (240, 200, 90)
NOISE_SHOW = 0.3                     # s a footstep ring stays after the steps stop
LOUD_SHOW = 0.8                      # s a loud one (roll, swing, shot) stays: one moment, easy to miss at 0.3


def heard(game, x, y, radius):
    """play.make_noise calls this: remember the noise for the F6 rings. Footsteps are made every
    frame, so a noise of the same size replaces the last one instead of piling up."""
    for n in game.dev.noises:
        if n[2] == radius:
            n[:] = [x, y, radius, 0.0]
            return
    game.dev.noises.append([x, y, radius, 0.0])


def ring_time(radius):
    return LOUD_SHOW if radius >= infected.NOISE_ROLL else NOISE_SHOW


def age_noises(game, dt):
    game.dev.noises = [n for n in game.dev.noises if n[3] + dt < ring_time(n[2])]
    for n in game.dev.noises:
        n[3] += dt


def draw_sight(game, cx, cy):
    """F5. The cone out to where the hero is spotted at once ("!") - SPOT_DIST, the same whatever
    he does - plus the all-round ring (NOTICE_NEAR);
    a wall in between hides him."""
    if not game.dev.sight:
        return
    spot = infected.SPOT_DIST
    for z in game.zombies:
        if not z.alive:
            continue
        zx, zy = z.x - cx, z.y - cy
        _wedge(zx, zy, spot, z.heading, infected.SIGHT_HALF, SIGHT, 2)
        _arc(zx, zy, infected.NOTICE_NEAR, -3.15, 3.15, NEAR, 2)


def draw_sounds(game, cx, cy):
    """F6. Every noise the hero makes, as a ring as far as it carries: an infected inside hears it
    ("?"). The entrances new infected come in by: lit while a loud noise reaches them (the next one
    comes soon, through one of those, toward the noise), dim otherwise."""
    if not game.dev.sounds:
        return
    for x, y, radius, age in game.dev.noises:
        fade = 1 - age / ring_time(radius)
        colour = tuple(round(c * (0.5 + 0.5 * fade)) for c in NOISE)
        for grow in (0, PIXEL):                                   # two canvas px thick, solid
            _arc(x - cx, y - cy, radius + grow, -3.15, 3.15, colour, 1)
    pulled = game.pulled_entrances()
    for (x, y), _ in area.ENTRANCES:
        colour = NOISE if (x, y) in pulled else (110, 100, 70)
        _box(x - 10 - cx, y - 10 - cy, x + 10 - cx, y + 10 - cy, colour)
        _line(x - 10 - cx, y - 10 - cy, x + 10 - cx, y + 10 - cy, colour)


STATE_NAMES = {"build": "쌓기", "peak": "절정", "relax": "쉬기"}
STATE_COLOURS = {"build": (214, 176, 80), "peak": (226, 80, 64), "relax": (96, 186, 120)}


def draw_director(game):
    """F7, on the screen canvas: intensity over the last minute (one bar per 0.25 s, coloured by
    the state then), the peak line, the state now and the next arrival."""
    if not game.dev.director:
        return
    d = game.director
    l, t, w, h = 200, 92, 240, 40                     # under the defense clock and the people count
    px.rect(l - 4, t - 30, l + w + 4, t + h + 4, (14, 15, 17, 215))
    px.frame(l - 4, t - 30, l + w + 4, t + h + 4, (70, 72, 76))
    name = STATE_NAMES.get(d.state, d.state)
    px.text(l, t - 29, f"AI 디렉터 · {name}", STATE_COLOURS.get(d.state, LIGHT), bold=True)
    nxt = "없음" if d.spawn_in > 900 else f"{max(0.0, d.spawn_in):.1f}초"
    px.text(l, t - 15, f"긴장 {d.intensity:.2f} · 다음 피폭체 {nxt} · 최대 {d.most}마리", GREY)
    import director as rules
    peak_y = t + h - round(rules.PEAK_AT * h)
    px.rect(l, peak_y, l + w, peak_y, (90, 50, 46))                 # the peak line (outside)
    hist = d.history[-w:]
    for k, (value, state) in enumerate(hist):
        x = l + w - len(hist) + k
        top = t + h - max(1, round(value * h))
        px.rect(x, top, x, t + h, STATE_COLOURS.get(state, LIGHT))

