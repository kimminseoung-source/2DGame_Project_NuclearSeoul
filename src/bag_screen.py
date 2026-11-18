"""What the keys and the mouse do while the bag (Tab) is open (2026-11-16, bag B v4).

The cursor is a cell on one of two grids: the bag's ground sheet or the ground nearby
(hud.bag_layout). WASD / arrows move it; D past the sheet's right edge goes to the ground, A past
the ground's left edge comes back (패드식 칸 이동, GROUND_INVENTORY_UI_RESEARCH.md 2-7).
- Enter / right click: use the chosen thing (bag) or pick it up (ground)
- X: put the chosen thing down on the ground
- F: pick up every nearby thing of the chosen kind; Shift+F: everything nearby (as much as fits)
- mouse: hovering chooses; dragging moves a thing to another spot on the sheet (it stays where it
  is put, 2026-11-18 "커서로 정리할 수 있게") or between the sheet and the ground. While it is
  carried, its landing cells show green (fits) or red; R or a right click turns it a quarter.
- R on a thing in the bag turns it where it lies, if it fits turned
- (2026-11-18 bag step 2) a stack let go on a stack of the same kind joins it; a weapon let go on
  the hand slot is taken in hand; a stack dragged out to the ground is put down whole; a double
  click uses a thing (or picks it up); the "정리" button (or T) lays everything again from the top.
The world waits while the bag is open (play.update).
"""

import time

import sdl2

import bag_grid
import hud
import pixel_ui as px
import supplies as supply_rules
import weapons
from supplies import KINDS, Supply

MOVES = {sdl2.SDLK_LEFT: (-1, 0), sdl2.SDLK_RIGHT: (1, 0), sdl2.SDLK_UP: (0, -1), sdl2.SDLK_DOWN: (0, 1),
         sdl2.SDLK_a: (-1, 0), sdl2.SDLK_d: (1, 0), sdl2.SDLK_w: (0, -1), sdl2.SDLK_s: (0, 1)}
GRIDS = {"bag": bag_grid.BAG_GRID, "near": bag_grid.NEAR_GRID}


def reset(game):
    game.bag_side, game.bag_cell = "bag", (0, 0)
    game.bag_drag = None             # (side, placed thing) carried by the mouse
    game.bag_grab = (0, 0)           # the cell of the thing the mouse took it by
    game.bag_turned = False          # the carried thing is turned a quarter
    game.bag_target = None           # (col, row, turned, fits, stack it joins): where it would land
    game.bag_click = (0.0, None)     # when and on what the last left click was (double click)
    game.bag_mouse = (0.0, 0.0)      # canvas px
    game.bag_note_from = None        # the message showing when the bag opened (not repeated in it)


def move(game, dc, dr):
    """Step cell by cell until the cursor leaves the thing it was on (a 2x2 can is one stop)."""
    layout = hud.bag_layout(game)
    side, (c, r) = game.bag_side, game.bag_cell
    start = bag_grid.at(layout[side], c, r)
    while True:
        cols, rows = GRIDS[side]
        c, r = c + dc, r + dr
        if side == "bag" and c >= cols:                       # off the sheet's right: the ground
            side, c, r = "near", 0, min(r, GRIDS["near"][1] - 1)
            break
        if side == "near" and c < 0:                          # off the ground's left: the sheet
            side, c, r = "bag", GRIDS["bag"][0] - 1, min(r, GRIDS["bag"][1] - 1)
            break
        if not (0 <= c < cols and 0 <= r < rows):
            c, r = max(0, min(cols - 1, c)), max(0, min(rows - 1, r))
            break
        if start is None or bag_grid.at(layout[side], c, r) is not start:
            break
    game.bag_side, game.bag_cell = side, (c, r)


def take(game, supply):
    """Pick one thing up off the ground into the bag; False when it does not fit."""
    if not hud.fits(game, supply.kind):
        return False
    supply.taken = True
    game.bag[supply.kind] += 1
    return True


def drop(game, kind):
    """Put one thing from the bag down at the hero's feet (a weapon lies there to be taken again)."""
    game.bag[kind] -= 1
    wkey = weapons.key_of(kind)
    if wkey:
        game.ground_weapons.append([game.hero.x + 10, game.hero.y - 4, wkey])
    else:
        game.supplies.append(Supply(game.hero.x + 10, game.hero.y - 4, kind))
    game.message = f"{supply_rules.with_object_particle(supply_rules.item_name(kind))} 내려놓았다"


def took(game, count):
    """Sound and message after picking things up from the bag screen (rummaging is heard)."""
    if count:
        game.message = f"물건 {count}개를 챙겼다"
        game.sounds.play("pickup", 0.8)
        if game.senses:
            game.make_noise(supply_rules.PICK_NOISE)
    else:
        game.message = "배낭에 자리가 없다"


def act(game, thing, side):
    """Enter / right click on a thing: use it from the bag, or pick it up from the ground."""
    if thing is None:
        return
    if side == "bag":
        game.use(thing[0])
    else:
        took(game, 1 if take(game, thing[1]) else 0)


def take_many(game, kind=None):
    """F: every nearby thing of `kind`; Shift+F (kind None): everything nearby, as much as fits."""
    wanted = [s for s in hud.nearby_items(game) if kind is None or s.kind == kind]
    if not wanted:
        game.message = ("근처에 주울 것이 없다" if kind is None
                        else f"근처에 {supply_rules.with_subject_particle(KINDS[kind][0])} 없다 · Shift+F로 모두 줍기")
        return
    took(game, sum(1 for supply in wanted if take(game, supply)))


def key(game, k, shift=False):
    thing = hud.chosen(game)
    if k in (sdl2.SDLK_TAB, sdl2.SDLK_ESCAPE):
        game.bag_open = False
        game.bag_drag = None
    elif k in MOVES:
        move(game, *MOVES[k])
    elif k in (sdl2.SDLK_RETURN, sdl2.SDLK_KP_ENTER):
        act(game, thing, game.bag_side)
    elif k == sdl2.SDLK_x and thing is not None and game.bag_side == "bag":
        drop(game, thing[0])
    elif k == sdl2.SDLK_f:
        take_many(game, None if shift or thing is None else thing[0])
    elif k == sdl2.SDLK_r:
        turn(game, thing)
    elif k == sdl2.SDLK_t:
        tidy(game)


def tidy(game):
    """The "정리" button: lay everything again from the top left."""
    if bag_grid.tidy(game):
        game.message = "배낭을 정리했다"
        game.sounds.play("pickup", 0.6)
    else:
        game.message = "더 정리할 수 없다"


def turn(game, thing):
    """R: turn the carried thing, or the chosen thing in the bag where it lies (if it fits)."""
    if game.bag_drag is not None:
        game.bag_turned = not game.bag_turned
        game.bag_grab = (game.bag_grab[1], game.bag_grab[0])
        aim(game)
        return
    if thing is None or game.bag_side != "bag":
        return
    place = thing[1]
    if bag_grid.free(bag_grid.sync(game), place[0], place[1], place[2], not place[3], ignore=place):
        place[3] = not place[3]
        game.sounds.play("pickup", 0.4)


def aim(game):
    """Where the carried thing would land on the sheet (its grab cell under the mouse)."""
    game.bag_target = None
    spot = hud.cell_at(*game.bag_mouse)
    if game.bag_drag is None or spot is None or spot[0] != "bag":
        return
    side, thing = game.bag_drag
    kind = thing[0]
    mine = thing[1] if side == "bag" else None
    under = bag_grid.at(bag_grid.placed(game), spot[1], spot[2])
    if under is not None and under[1] is not mine and under[0] == kind \
            and under[1][4] < bag_grid.stack_max(kind):                # onto a stack of its kind: join it
        p = under[1]
        game.bag_target = (p[1], p[2], p[3], True, p)
        return
    c, r = spot[1] - game.bag_grab[0], spot[2] - game.bag_grab[1]
    ok = bag_grid.free(bag_grid.sync(game), kind, c, r, game.bag_turned, ignore=mine)
    game.bag_target = (c, r, game.bag_turned, ok, None)


def mouse_move(game, sx, sy):
    game.bag_mouse = px.to_canvas(sx, sy)
    spot = hud.cell_at(*game.bag_mouse)
    if spot is not None and game.bag_drag is None:
        game.bag_side, game.bag_cell = spot[0], spot[1:]
    aim(game)


def inside(rect, x, y):
    l, t, r, b = rect
    return l <= x <= r and t <= y <= b


def mouse_down(game, sx, sy, button):
    mouse_move(game, sx, sy)
    if button == "left" and inside(hud.TIDY_RECT, *game.bag_mouse):
        tidy(game)
        return
    spot = hud.cell_at(*game.bag_mouse)
    if spot is None:
        return
    game.bag_side, game.bag_cell = spot[0], spot[1:]
    thing = hud.chosen(game)
    if button == "right" and game.bag_drag is not None:
        turn(game, thing)                                      # a right click while carrying: turn it
    elif button == "right":
        act(game, thing, spot[0])
    elif thing is not None:
        now, last = time.monotonic(), game.bag_click
        if last[1] is thing[1] and now - last[0] < 0.35:       # a double click: use it / pick it up
            game.bag_click = (0.0, None)
            act(game, thing, spot[0])
            return
        game.bag_click = (now, thing[1])
        game.bag_drag = (spot[0], thing)
        game.bag_grab = (spot[1] - thing[2], spot[2] - thing[3])
        game.bag_turned = bool(thing[1][3]) if spot[0] == "bag" else False
        aim(game)


def drop_stack(game, place):
    """A whole stack dragged out of the bag: every one of it down at the hero's feet."""
    kind, n = place[0], place[4]
    bag_grid.sync(game).remove(place)
    for _ in range(n):
        drop(game, kind)
    if n > 1:
        game.message = f"{supply_rules.with_object_particle(supply_rules.item_name(kind))} {n}개 내려놓았다"


def land(game, kind, target, before):
    """After one `kind` came into the bag: move it from wherever sync() put it to the target - the
    stack it was let go on, or the empty spot under the mouse. `before`: counts by place, earlier."""
    places = bag_grid.sync(game)
    came = next((p for p in places if p[0] == kind and p[4] > before.get(id(p), 0)), None)
    if came is None or target is None:
        return
    c, r, turned, ok, into = target
    if into is not None and into is not came:
        came[4] -= 1
        into[4] += 1
        if came[4] == 0:
            places.remove(came)
    elif into is None and ok:
        if id(came) not in before:                             # it got a spot of its own: move it there
            came[1], came[2], came[3] = c, r, turned
        else:                                                  # it joined a stack elsewhere: take it out
            came[4] -= 1
            places.append([kind, c, r, turned, 1])


def mouse_up(game, sx, sy):
    """Drop what the mouse carries: onto the other grid it moves there, anywhere else it stays."""
    if game.bag_drag is None:
        return
    side, thing = game.bag_drag
    game.bag_mouse = px.to_canvas(sx, sy)
    aim(game)
    target = game.bag_target
    game.bag_drag, game.bag_target = None, None
    kind = thing[0]
    if side == "bag" and inside(hud.HAND_RECT, *game.bag_mouse):      # onto the hand slot
        if weapons.key_of(kind):
            game.equip(weapons.key_of(kind))
        else:
            game.message = "손에는 무기만 들 수 있다"
        return
    spot = hud.cell_at(*game.bag_mouse)
    if spot is None:
        return
    if side == "bag" and spot[0] == "bag":                       # moved on the sheet
        place = thing[1]
        if target is None or not target[3]:
            return
        into = target[4]
        if into is not None:                                     # joins the stack it was let go on
            n = min(bag_grid.stack_max(kind) - into[4], place[4])
            into[4] += n
            place[4] -= n
            if place[4] == 0:
                bag_grid.sync(game).remove(place)
        else:
            place[1], place[2], place[3] = target[0], target[1], target[2]
        game.bag_side, game.bag_cell = "bag", (target[0], target[1])
        game.sounds.play("pickup", 0.4)
        return
    if side == "bag":
        drop_stack(game, thing[1])
        return
    if spot[0] == "near":
        return
    if target is not None and not target[3]:                      # no room where it was let go
        game.message = "거기에는 들어가지 않는다"
        return
    before = {id(p): p[4] for p in bag_grid.sync(game)}
    if take(game, thing[1]):
        took(game, 1)
        land(game, kind, target, before)
    else:
        took(game, 0)
