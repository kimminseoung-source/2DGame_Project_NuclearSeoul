"""F5 sight / F6 sound split; a loud noise calls new infected only through entrances in its ring."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import hypot
import pico2d, sdl2, play, settings, ui, infected, weapons, area
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(1)
g = play.Game()
g.zoom = g.zoom_shown = settings.ZOOM_STEPS[0]
for _ in range(3): g.update(1 / 60, keys)
print("gun noise:", weapons.WEAPONS["pistol"]["shot"]["noise"])
g.key_down(sdl2.SDLK_F5, keys); g.key_down(sdl2.SDLK_F6, keys); print("F5 sight", g.dev.sight, "F6 sounds", g.dev.sounds)
g.dev.freeze = True
ents = [p for p, _ in area.ENTRANCES]
h = g.hero
print("hero", round(h.x), round(h.y), "| entrances:", [(p, round(hypot(p[0] - h.x, p[1] - h.y))) for p in ents])
# a slash (230): no entrance far enough inside it -> nothing called
g.director.spawn_in = 7.0; g.make_noise(infected.NOISE_SLASH)
print("slash: pulled", g.pulled_entrances(), "spawn_in", round(g.director.spawn_in, 2))
# a shot (400) from where an entrance is 240..400 away
spots = [(x, y) for x in range(40, area.ROOM_W - 40, 20) for y in range(40, area.ROOM_H - 40, 20)
         if not area.blocked(x, y) and any(260 <= hypot(p[0] - x, p[1] - y) <= 380 for p in ents)
         and sum(hypot(p[0] - x, p[1] - y) <= 400 for p in ents) < len(ents)]
h.x, h.y = spots[len(spots) // 2]
g.loud = None; g.director.spawn_in = 7.0; g.make_noise(400)
pulled = g.pulled_entrances()
print("shot: pulled", pulled, "spawn_in", round(g.director.spawn_in, 2))
n = len(g.zombies); g.spawn()
z = g.zombies[-1]
print("spawned at", (round(z.x), round(z.y)), "in pulled:", (round(z.x), round(z.y)) in [tuple(map(round, p)) for p in pulled], "goes to", z.target)
g.cam = [h.x - g.view_w / 2, h.y - g.view_h / 2]; g.clamp_camera()
for _ in range(10): g.update(1 / 60, keys)
pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
raw = ctypes.string_at(s.contents.pixels, s.contents.pitch * settings.HEIGHT)
Image.frombuffer("RGBA", (settings.WIDTH, settings.HEIGHT), raw, "raw", "BGRA", s.contents.pitch, 1).convert("RGB").save("docs/planning/dev_sounds.png")
# after NOISE_PULL the pull ends
g.clock += play.NOISE_PULL + 0.1
print("after pull time:", g.pulled_entrances())
pico2d.close_canvas(); print("ok")
