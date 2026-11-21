"""Station defense: E at the exit -> 60 s with a soldier and two civilians -> the train."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
g = play.Game()
for _ in range(3): g.update(1 / 60, keys)
print("people:", [(s.kind, round(s.x), round(s.y)) for s in g.people], "| exit", area.EXIT)


def grab(name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
    Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save(name)


h = g.hero
l, b, r, t = area.EXIT
h.x, h.y = (l + r) / 2, t + 10
g.dev.god = True; g.aim = (560, 250)                                   # the hero stands by; see what the people do
for _ in range(30): g.update(1 / 60, keys)
grab("docs/planning/station_before.png")
g.key_down(sdl2.SDLK_e, keys)
print("after E:", g.message, "| defense", g.defense)
shots = falls = 0
for f in range(int(62 * 60)):
    before = sum(1 for s in g.people if s.alive)
    rounds = g.people[0].gun["rounds"]
    g.update(1 / 60, keys)
    shots += rounds - g.people[0].gun["rounds"]
    falls += before - sum(1 for s in g.people if s.alive)
    from math import hypot as _h
    if not getattr(g, "_shot", False) and any(z.alive and z.state in ("windup", "strike") and getattr(z, "prey", h) is not h for z in g.zombies):
        g._shot = True
        grab("docs/planning/station_defense.png")
        print(f"{f / 60:.1f} s:", "alive infected", sum(z.alive for z in g.zombies), "| on people:",
              sum(1 for z in g.zombies if z.alive and getattr(z, "prey", h) is not h), "| defense left", g.defense, g.left, g.message)
    if f % (10 * 60) == 0 and g.defense is not None:
        from math import hypot
        print(f"{f // 60}s", [(z.state, round(min(hypot(z.x - q.x, z.y - q.y) for q in [h] + g.people))) for z in g.zombies if z.alive], "loud", g.loud and [round(v) for v in g.loud[:2]])
    if g.left:
        break
print("train:", g.left, "|", g.message, "| soldier shots", shots, "| people fell", falls,
      "| killed by people", getattr(g, "kills_by_people", 0), "| infected now", sum(z.alive for z in g.zombies))
grab("docs/planning/station_train.png")
pico2d.close_canvas(); print("ok")




