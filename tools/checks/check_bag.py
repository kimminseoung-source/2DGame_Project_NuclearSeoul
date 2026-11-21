"""Bag screen B v4: layout, keys, take / drop, mouse drag, and a screenshot."""
import sys
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, hud, bag_grid, bag_screen
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(out + f"/{name}.png")
print("shapes", {k: bag_grid.shape(k) for k in ("bandage", "can", "pill")})
full, left = bag_grid.pack([("can", None)] * 4 + [("bandage", None)] * 4, bag_grid.BAG_GRID)
print("4 cans + 4 bandages (2.0) placed", len(full), "left", len(left))
full, left = bag_grid.pack([("can", None)] * 3 + [("bandage", None)] * 8, bag_grid.BAG_GRID)
print("3 cans + 8 bandages (2.0) placed", len(full), "left", len(left))
g = play.Game(); g.to_spawn = 0
g.bag["bandage"], g.bag["can"] = 2, 1
from supplies import Supply
g.supplies.append(Supply(g.hero.x + 8, g.hero.y, "can"))
g.supplies.append(Supply(g.hero.x - 8, g.hero.y, "bandage"))
g.condition.bleeding, g.condition.blows = True, 2
g.key_down(sdl2.SDLK_TAB, keys)
lay = hud.bag_layout(g)
print("bag placed", [(p[0], p[2:]) for p in lay["bag"]], "near", [(p[0], p[2:]) for p in lay["near"]])
shot("bag_open")
# keys: D from bandage(0,0) -> bandage(1,0) -> can(2,0) -> past can to (4,0) -> ground
seen = []
for _ in range(4):
    bag_screen.key(g, sdl2.SDLK_d); seen.append((g.bag_side, g.bag_cell))
print("D steps", seen)
bag_screen.key(g, sdl2.SDLK_a); print("A back ->", g.bag_side, g.bag_cell)
# take the ground can with Enter on the ground
g.bag_side, g.bag_cell = "near", (0, 0)
t = hud.chosen(g); print("chosen on ground", t and t[0])
bag_screen.key(g, sdl2.SDLK_RETURN); print("after Enter: bag", dict(g.bag), "msg", g.message)
# X drops the chosen bag can
g.bag_side, g.bag_cell = "bag", (2, 0)
bag_screen.key(g, sdl2.SDLK_x); print("after X: bag", dict(g.bag), "near", [s.kind for s in hud.nearby_items(g)])
# Shift+F takes everything nearby
bag_screen.key(g, sdl2.SDLK_f, shift=True); print("after Shift+F: bag", dict(g.bag), "weight", round(sum(v*{'bandage':0.1,'can':0.4,'pill':0.1}[k] for k,v in g.bag.items()),1))
# fill to the limit, then F must refuse
g.bag["can"] = 4; g.bag["bandage"] = 4
g.supplies.append(Supply(g.hero.x, g.hero.y + 5, "can"))
bag_screen.key(g, sdl2.SDLK_f, shift=True); print("full bag F ->", g.message)
g.bag["can"] = 1; g.bag["bandage"] = 1
# mouse: drag the bag bandage (cell 0,0) onto the ground grid
K = 2
def scr(cx, cy): return cx * K, cy * K
gx, gy = hud.SHEET_GRID; nx, ny = hud.NEAR_ORIGIN
before = g.bag["bandage"]
bag_screen.mouse_down(g, *scr(gx + 10, gy + 10), "left")
bag_screen.mouse_move(g, *scr(nx + 50, ny + 20))
shot("bag_drag")
shot("bag_after")
bag_screen.mouse_up(g, *scr(nx + 50, ny + 20))
print("drag bag->ground: bandage", before, "->", g.bag["bandage"])
# hover a can and right click uses nothing (can is not usable) but shows its line
bag_screen.mouse_move(g, *scr(gx + 10, gy + 10)); print("hover ->", g.bag_side, g.bag_cell)
bag_screen.key(g, sdl2.SDLK_TAB); print("Tab closes ->", g.bag_open)
for _ in range(30): g.update(1 / 60, keys)
print("game runs ok")
