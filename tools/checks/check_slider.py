"""F4 sliders: click/drag the bar, type a number in the box, Esc cancels."""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dev_tools, hero as hero_rules, infected, condition, pixel_ui as px
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True
for _ in range(5): g.update(1 / 60, keys)
g.key_down(sdl2.SDLK_F4, keys)
row = lambda name: next(i for i, r in enumerate(dev_tools.ROWS) if r[0] == name)
l, t, r = dev_tools.PANEL
def at(i, cx):                       # screen point on row i at canvas x
    g.dev.row = i; dev_tools.keep_in_view(g.dev)
    return cx * px.K, (t + 17 + (i - g.dev.scroll) * dev_tools.ROW_H + 6) * px.K

# click the bar at its middle: 주인공 속도 30..300 -> 165 -> snapped 170 (step 10)
i = row("주인공 속도"); tl, tr = dev_tools.TRACK
print("click middle:", dev_tools.click(g, *at(i, (tl + tr) / 2), False), "->", hero_rules.RUN_SPEED)
dev_tools.drag(g, *at(i, tr + 30)); print("drag past the end ->", hero_rules.RUN_SPEED)
dev_tools.release(g); dev_tools.drag(g, *at(i, tl)); print("after release, move does nothing ->", hero_rules.RUN_SPEED)
# type into the box: 발견 거리 = 175 -> snapped 180? (step 10)
i = row("피폭체 시야·발견 거리"); bl, br = dev_tools.BOX
dev_tools.click(g, *at(i, (bl + br) / 2), False); dev_tools.release(g)
for k in (sdl2.SDLK_1, sdl2.SDLK_7, sdl2.SDLK_5): g.key_down(k, keys)
print("typing:", repr(g.dev.text), "| quick slot not used:", g.message == "")
pico2d.clear_canvas(); g.draw()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
pico2d.update_canvas()
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").crop((720, 40, 1280, 700)).save("docs/planning/dev_sliders.png")
g.key_down(sdl2.SDLK_RETURN, keys); print("Enter ->", infected.SIGHT_RANGE)
# percent row: type 35 -> bleed chance 0.35
i = row("출혈 확률"); dev_tools.click(g, *at(i, (bl + br) / 2), False); dev_tools.release(g)
for k in (sdl2.SDLK_3, sdl2.SDLK_5): g.key_down(k, keys)
g.key_down(sdl2.SDLK_RETURN, keys); print("bleed 35 ->", condition.BLEED_CHANCE)
# Esc cancels
dev_tools.click(g, *at(i, (bl + br) / 2), False); dev_tools.release(g)
g.key_down(sdl2.SDLK_9, keys); print("Esc cancels:", dev_tools.cancel_typing(g), condition.BLEED_CHANCE, g.dev.editing)
# keyboard still steps
g.dev.row = row("게임 속도"); g.key_down(sdl2.SDLK_LEFT, keys); print("game speed ← ->", g.dev.speed)
# scrolling: down arrow to the end skips headings and scrolls; view sliders change vision_cone
import vision_cone
g.dev.row = 1; g.dev.scroll = 0
for _ in range(60): g.key_down(sdl2.SDLK_DOWN, keys)
print("after 60 downs: row", g.dev.row, dev_tools.ROWS[g.dev.row][0], "| scroll", g.dev.scroll, "| on a heading:", dev_tools.heading(g.dev.row))
i = row("낮 시야 길이"); dev_tools.click(g, *at(i, (dev_tools.TRACK[0] + dev_tools.TRACK[1]) / 2), False); dev_tools.release(g)
print("view length middle ->", vision_cone.CONE_RANGE)
g.dev.scroll = 0; pico2d.clear_canvas(); g.draw()
s2 = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s2.contents.pixels, s2.contents.pitch)
raw2 = ctypes.string_at(s2.contents.pixels, s2.contents.pitch * settings.HEIGHT)
pico2d.update_canvas()
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw2, "raw", "BGRA", s2.contents.pitch, 1).convert("RGB").crop((720, 40, 1280, 700)).save("docs/planning/dev_sliders.png")
pico2d.close_canvas(); print("ok")
