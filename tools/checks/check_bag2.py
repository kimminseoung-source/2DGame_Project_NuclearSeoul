"""The bag by cells: spots are remembered, dragging moves a thing (green / red preview), R turns it,
a full sheet takes nothing more, taking a weapon in hand swaps spots. Shots of a drag."""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, bag_grid, bag_screen, hud, pixel_ui as px
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game()
for _ in range(3): g.update(1 / 60, keys)
g.bag["can"], g.bag["bandage"], g.bag["w:knife"], g.bag["w:pistol"] = 1, 3, 1, 1
g.key_down(sdl2.SDLK_TAB, keys)
places = bag_grid.sync(g)
print("spots:", [(p[0], p[1], p[2], p[3]) for p in places], "| cells", bag_grid.used_cells(g))


def screen_of(c, r, side="bag"):                 # the middle of a cell, in window px
    gx, gy = hud.grid_origin(side)
    return (gx + c * hud.CELL + hud.CELL / 2) * px.K, (gy + r * hud.CELL + hud.CELL / 2) * px.K


def grab():
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


shots = [("처음: 들어온 순서대로 놓임", grab())]
can = next(p for p in places if p[0] == "can")
# drag the can from its spot to the bottom right corner
bag_screen.mouse_move(g, *screen_of(can[1], can[2]))
bag_screen.mouse_down(g, *screen_of(can[1], can[2]), "left")
bag_screen.mouse_move(g, *screen_of(3, 2))
print("over (3,2):", g.bag_target)
shots.append(("끄는 중: 들어갈 자리는 초록", grab()))
other = next(p for p in places if p[0] == "w:knife")
bag_screen.mouse_move(g, *screen_of(other[1], other[2]))
print("over the knife:", g.bag_target)
shots.append(("다른 물건 위: 빨강", grab()))
bag_screen.mouse_move(g, *screen_of(3, 2))
bag_screen.mouse_up(g, *screen_of(3, 2))
print("can now at:", can[1:], "| spots kept after sync:", [(p[0], p[1], p[2]) for p in bag_grid.sync(g)])
# turn the knife where it lies (R)
knife = next(p for p in bag_grid.sync(g) if p[0] == "w:pistol")
g.bag_side, g.bag_cell = "bag", (knife[1], knife[2])
before = knife[3]
bag_screen.key(g, sdl2.SDLK_r)
print("pistol turned:", before, "->", knife[3])
shots.append(("놓은 뒤 + R로 권총 세우기", grab()))
# fill it up: room for more?
print("room for a can:", bag_grid.room_for(g, "can"), "| for a bandage:", bag_grid.room_for(g, "bandage"))
while bag_grid.room_for(g, "bandage"):
    g.bag["bandage"] += 1
print("full: cells", bag_grid.used_cells(g), "| room for a bandage:", bag_grid.room_for(g, "bandage"))
# full: the machete cannot go in for the pistol; with room it can
g.equip("pistol")
print("full, take the pistol:", g.hero.weapon["name"], "|", g.message)
g.bag["bandage"] -= 6
g.equip("pistol")
print("with room:", g.hero.weapon["name"], "| machete in bag:", any(p[0] == "w:machete" for p in bag_grid.sync(g)))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 18)
sheet = Image.new("RGB", (1280, 760), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t, im) in enumerate(shots):
    x, y = (i % 2) * 640, (i // 2) * 380
    sheet.paste(im.crop((380, 120, 1080, 520)).resize((640, 350)), (x, y + 30)); d.text((x + 8, y + 6), t, font=f, fill=(196, 170, 92))
sheet.save("docs/planning/bag_drag.png"); print("ok")
