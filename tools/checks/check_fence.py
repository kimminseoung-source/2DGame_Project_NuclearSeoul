"""The station stays fenced off until the hero starts the defense: the people are still alive."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area, infected
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()


def grab(g, name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save(name)


l, b, r, t = None, None, None, None
for seed in (1, 2, 3, 4):
    random.seed(seed)
    g = play.Game(); g.dev.god = True
    l, b, r, t = g.station_zone
    inside = lambda z: l <= z.x <= r and b <= z.y <= t
    worst = 0
    for f in range(90 * 60):                       # the hero idles far away; the infected wander
        g.update(1 / 60, keys)
        worst = max(worst, sum(1 for z in g.zombies if z.alive and inside(z)))
    print(f"seed {seed}: 90 s later people alive", sum(s.alive for s in g.people), "/", len(g.people),
          "| infected inside the fence at worst", worst, "| alive infected", sum(z.alive for z in g.zombies))
# go there: the hero can walk in through the fence
el, eb, er, et = area.EXIT
g.hero.x, g.hero.y = (el + er) / 2, t + 40
keys[sdl2.SDL_SCANCODE_S] = 1
for _ in range(75): g.update(1 / 60, keys)
keys[sdl2.SDL_SCANCODE_S] = 0
print("hero walked in:", round(g.hero.y), "near exit", g.near_exit())
g.aim = (560, 250)
grab(g, "docs/planning/station_fence.png")
g.key_down(sdl2.SDLK_e, keys)
print("after E: open", g.station_open, "| keep_out", infected.Zombie.keep_out, "|", g.message)
for _ in range(60 * 15): g.update(1 / 60, keys)
print("15 s into the defense: infected inside", sum(1 for z in g.zombies if z.alive and inside(z)))
pico2d.close_canvas(); print("ok")

