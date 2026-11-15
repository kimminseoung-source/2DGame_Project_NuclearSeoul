"""What the keys and the mouse do while the bag (Tab) is open (2026-11-16, bag B v4).

The cursor is a cell on one of two grids: the bag's ground sheet or the ground nearby
(hud.bag_layout). WASD / arrows move it; D past the sheet's right edge goes to the ground, A past
the ground's left edge comes back (패드식 칸 이동, GROUND_INVENTORY_UI_RESEARCH.md 2-7).
- Enter / right click: use the chosen thing (bag) or pick it up (ground)
- X: put the chosen thing down on the ground
- F: pick up every nearby thing of the chosen kind; Shift+F: everything nearby (as much as fits)
- mouse: hovering chooses, dragging a thing from one grid to the other moves it
The world waits while the bag is open (play.update).
"""

import sdl2

import bag_grid
import hud
import pixel_ui as px
import supplies as supply_rules
from supplies import KINDS, Supply

MOVES = {sdl2.SDLK_LEFT: (-1, 0), sdl2.SDLK_RIGHT: (1, 0), sdl2.SDLK_UP: (0, -1), sdl2.SDLK_DOWN: (0, 1),
         sdl2.SDLK_a: (-1, 0), sdl2.SDLK_d: (1, 0), sdl2.SDLK_w: (0, -1), sdl2.SDLK_s: (0, 1)}
GRIDS = {"bag": bag_grid.BAG_GRID, "near": bag_grid.NEAR_GRID}


def reset(game):
    game.bag_side, game.bag_cell = "bag", (0, 0)
    game.bag_drag = None             # (side, placed thing) carried by the mouse
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
    """Put one thing from the bag down at the hero's feet."""
    game.bag[kind] -= 1
    game.supplies.append(Supply(game.hero.x + 10, game.hero.y - 4, kind))
    game.message = f"{supply_rules.with_object_particle(KINDS[kind][0])} 내려놓았다"


def took(game, count):
    """Sound and message after picking things up from the bag screen (rummaging is heard)."""
    if count:
        game.message = f"물건 {count}개를 챙겼다"
        game.sounds.play("pickup", 0.8)
        if game.senses:
            game.make_noise(supply_rules.PICK_NOISE)
    else:
        game.message = "배낭이 무겁다 · 더 넣을 수 없다"


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


def mouse_move(game, sx, sy):
    game.bag_mouse = px.to_canvas(sx, sy)
    spot = hud.cell_at(*game.bag_mouse)
    if spot is not None and game.bag_drag is None:
        game.bag_side, game.bag_cell = spot[0], spot[1:]


def mouse_down(game, sx, sy, button):
    mouse_move(game, sx, sy)
    spot = hud.cell_at(*game.bag_mouse)
    if spot is None:
        return
    game.bag_side, game.bag_cell = spot[0], spot[1:]
    thing = hud.chosen(game)
    if button == "right":
        act(game, thing, spot[0])
    elif thing is not None:
        game.bag_drag = (spot[0], thing)


def mouse_up(game, sx, sy):
    """Drop what the mouse carries: onto the other grid it moves there, anywhere else it stays."""
    if game.bag_drag is None:
        return
    side, thing = game.bag_drag
    game.bag_drag = None
    spot = hud.cell_at(*px.to_canvas(sx, sy))
    if spot is None or spot[0] == side:
        return
    if side == "bag":
        drop(game, thing[0])
    else:
        took(game, 1 if take(game, thing[1]) else 0)
