"""F1 debug boxes, F4 dev settings panel."""
import sys, ctypes; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dev_tools, condition, hero as hero_rules, pixel_ui as px
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game()
for _ in range(3): g.update(1 / 60, keys)


def grab():
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    return Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB")


g.key_down(sdl2.SDLK_F1, keys); g.key_down(sdl2.SDLK_F4, keys)
print("boxes", g.dev.boxes, "panel", g.dev.open)
# spawn one at the cursor via the panel (row by name), two crawl
g.aim = (760, 360)
row = lambda name: next(i for i, r in enumerate(dev_tools.ROWS) if r[0].startswith(name))
g.dev.row = row("피폭체 소환"); n = len(g.zombies); g.key_down(sdl2.SDLK_RETURN, keys)
print("spawned:", len(g.zombies) - n, "at", round(g.zombies[-1].x), round(g.zombies[-1].y))
g.dev.row = row("주인공 속도"); g.key_down(sdl2.SDLK_RIGHT, keys); print("run speed", hero_rules.RUN_SPEED)
g.dev.row = row("출혈 확률"); g.key_down(sdl2.SDLK_LEFT, keys); print("bleed chance", condition.BLEED_CHANCE)
# a mouse click on the 무적 row
i = row("무적"); l, t, r = dev_tools.PANEL
g.dev.row = i; dev_tools.keep_in_view(g.dev)
sx, sy = (l + 20) * px.K, (t + 17 + (i - g.dev.scroll) * dev_tools.ROW_H + 5) * px.K
print("click on panel:", dev_tools.click(g, sx, sy, False), "god", g.dev.god, "| outside:", dev_tools.click(g, 100, 600, False))
# god: put an infected on the hero and let it strike
z = g.zombies[-1]; z.x, z.y = g.hero.x + 20, g.hero.y; z.state = "chase"; z.seen_time = 9
for _ in range(300): g.update(1 / 60, keys)
print("god after 5 s next to one: hp", g.hero.hp, "bleeding", g.condition.bleeding)
g.dev.row = row("피폭체 멈춤"); g.key_down(sdl2.SDLK_RETURN, keys)
x0 = z.x; z.x += 60
for _ in range(30): g.update(1 / 60, keys)
print("freeze: moved", round(abs(z.x - x0 - 60), 1))
g.dev.open = False; g.aim = (300, 330)
grab().save("docs/planning/dev_tools.png")
g.hero.hp = 50; g.bag["can"] = 1; g.key_down(sdl2.SDLK_2, keys); print("can:", g.message, "| hp", g.hero.hp, "| cans", g.bag["can"])
g.key_down(sdl2.SDLK_2, keys); print("no can:", g.message)
g.bag["can"] = 1; g.hero.hp = 100; g.key_down(sdl2.SDLK_2, keys); print("full:", g.message, g.bag["can"])
g.key_down(sdl2.SDLK_F4, keys); g.key_down(sdl2.SDLK_F1, keys)
print("closed:", g.dev.open, g.dev.boxes)
pico2d.close_canvas(); print("ok")

