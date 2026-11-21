"""Bag step 2: stacks, joining a stack by drag, the tooltip, the hand slot, double click, tidy."""
import sys, ctypes, time; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, bag_grid, bag_screen, hud, pixel_ui as px
from pico2d import pico2d as canvas
from PIL import Image, ImageDraw, ImageFont
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game()
for _ in range(3): g.update(1 / 60, keys)
g.bag["bandage"], g.bag["can"], g.bag["w:knife"], g.bag["w:pistol"] = 7, 2, 1, 1
g.key_down(sdl2.SDLK_TAB, keys)
places = bag_grid.sync(g)
print("stacks:", [(p[0], p[1], p[2], p[4]) for p in places], "| cells", bag_grid.used_cells(g))


def at_cell(c, r, side="bag"):
    gx, gy = hud.grid_origin(side)
    return (gx + c * hud.CELL + hud.CELL / 2) * px.K, (gy + r * hud.CELL + hud.CELL / 2) * px.K


def grab():
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


shots = []
small = next(p for p in places if p[0] == "bandage" and p[4] == 2)
big = next(p for p in places if p[0] == "bandage" and p[4] == 5)
big[4] = 3; small[4] = 4                                     # two stacks with room: 3 and 4
bag_screen.mouse_move(g, *at_cell(small[1], small[2]))
shots.append(("마우스를 올리면 이름·설명", grab()))
bag_screen.mouse_down(g, *at_cell(small[1], small[2]), "left")
bag_screen.mouse_move(g, *at_cell(big[1], big[2]))
print("over the other stack:", g.bag_target[:4], "joins:", g.bag_target[4] is big)
shots.append(("같은 물건 위로 끌면 합쳐짐", grab()))
bag_screen.mouse_up(g, *at_cell(big[1], big[2]))
print("after join:", [(p[0], p[4]) for p in bag_grid.sync(g) if p[0] == "bandage"], "| bag count", g.bag["bandage"])
# drag the pistol onto the hand slot
pistol = next(p for p in bag_grid.sync(g) if p[0] == "w:pistol")
time.sleep(0.4)
bag_screen.mouse_move(g, *at_cell(pistol[1], pistol[2]))
bag_screen.mouse_down(g, *at_cell(pistol[1], pistol[2]), "left")
hx, hy = (hud.HAND_RECT[0] + 40) * px.K, (hud.HAND_RECT[1] + 15) * px.K
bag_screen.mouse_move(g, hx, hy)
shots.append(("손 칸으로 끌어 무기 들기", grab()))
bag_screen.mouse_up(g, hx, hy)
print("in hand:", g.hero.weapon["name"], "| machete in bag:", g.bag.get("w:machete"))
# double click a bandage: use it (the hero is hurt first)
g.hero.hp = 60
b = next(p for p in bag_grid.sync(g) if p[0] == "bandage")
time.sleep(0.4)
for _ in range(2):
    bag_screen.mouse_down(g, *at_cell(b[1], b[2]), "left")
    bag_screen.mouse_up(g, *at_cell(b[1], b[2]))
print("double click: hp", g.hero.hp, "| bandages", g.bag["bandage"])
# scatter, then tidy
for i, p in enumerate(bag_grid.sync(g)):
    pass
can = next(p for p in bag_grid.sync(g) if p[0] == "can")
can[1], can[2] = 4, 3
shots.append(("흩어진 상태", grab()))
time.sleep(0.4)
tl, tt, tr, tb = hud.TIDY_RECT
bag_screen.mouse_down(g, (tl + tr) / 2 * px.K, (tt + tb) / 2 * px.K, "left")
print("tidy:", g.message, [(p[0], p[1], p[2], p[4]) for p in bag_grid.sync(g)])
shots.append(("'정리' 버튼 뒤", grab()))
f = ImageFont.truetype("assets/fonts/galmuri/Galmuri11-Bold.ttf", 18)
sheet = Image.new("RGB", (1280, 1140), (20, 20, 22)); d = ImageDraw.Draw(sheet); d.fontmode = "1"
for i, (t, im) in enumerate(shots[:6]):
    x, y = (i % 2) * 640, (i // 2) * 380
    sheet.paste(im.crop((0, 60, 1280, 760)).resize((640, 350)), (x, y + 30)); d.text((x + 8, y + 6), t, font=f, fill=(196, 170, 92))
sheet.save("docs/planning/bag_step2.png"); print("ok")
