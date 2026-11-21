"""AI director: outside build/peak/relax, defense phases; F7 graph."""
import sys, ctypes, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2)
g = play.Game()
d = g.director
g.to_spawn = 99
log, last, arrivals = [], None, []
n0 = len(g.zombies)
for f in range(150 * 60):                      # 2.5 min outside, the hero stands where he starts
    g.hero.hp = 100; g.condition.bleeding = False  # healed every frame: hits still count
    g.update(1 / 60, keys)
    if d.state != last:
        log.append(f"{f / 60:5.1f}s {d.state:5s} intensity {d.intensity:.2f} alive {sum(z.alive for z in g.zombies)}")
        last = d.state
    if len(g.zombies) > n0:
        arrivals.append(round(f / 60, 1)); n0 = len(g.zombies)
print("outside states:"); print("\n".join(log))
print("arrivals:", arrivals)
# the defense
l, b, r, t = area.EXIT
g.hero.x, g.hero.y = (l + r) / 2, t + 10
g.key_down(sdl2.SDLK_e, keys)
log, last, msgs, n0, arrivals = [], None, [], len(g.zombies), []
for f in range(62 * 60):
    g.hero.hp = 100; g.condition.bleeding = False
    g.update(1 / 60, keys)
    if g.defense is None:
        break
    if (d.state, d.most) != last:
        log.append(f"{60 - g.defense:5.1f}s {d.state:5s} most {d.most}")
        last = (d.state, d.most)
    if g.message and (not msgs or msgs[-1] != g.message):
        msgs.append(g.message)
    if len(g.zombies) > n0:
        arrivals.append(round(60 - g.defense, 1)); n0 = len(g.zombies)
    if f == 55 * 60:
        g.dev.director = True
        pico2d.clear_canvas(); g.draw()
        s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
        sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
        raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
        pico2d.update_canvas()
        Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/director_f7.png")
print("defense phases:"); print("\n".join(log))
print("messages:", msgs)
print("defense arrivals:", arrivals)
pico2d.close_canvas(); print("ok")
