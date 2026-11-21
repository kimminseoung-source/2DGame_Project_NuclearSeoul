import sys, random
from math import pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui
from pico2d import pico2d as canvas
from PIL import Image
out = sys.argv[2]
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def shot(g, name):
    pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, settings.WIDTH, settings.HEIGHT, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    sdl2.SDL_SaveBMP(s, (out + "/t.bmp").encode()); Image.open(out + "/t.bmp").convert("RGB").save(f"{out}/{name}.png")
def scr(g, wx, wy): return ((wx - g.cam[0]) * settings.SCALE, settings.HEIGHT - 1 - (wy + settings.CHEST - g.cam[1]) * settings.SCALE)
res = {"down": 0, "stagger": 0}
for seed in range(40):
    g = play.Game(); g.to_spawn = 0; random.seed(seed)
    for z in g.zombies[1:]: z.state = "dead"; z.timer = 9
    z = g.zombies[0]; z.prone = False; g.hero.x, g.hero.y = 470.0, 420.0; z.x, z.y = 500.0, 420.0; z.state, z.timer, z.windup = "windup", 0.3, 0.5
    g.right_click(*scr(g, 560, 420)); res[z.state] = res.get(z.state, 0) + 1
print("shove during a wind-up (40 tries):", res)
for _ in range(10): g.update(1 / 60, keys)
for _ in range(20): g.update(1 / 60, keys)   # the shove plays out (a slash cannot cut into it)
g.hero.shove_cooldown = 0
z.state, z.timer = "stagger", 1.5
g.click(*scr(g, 560, 420)); print("slash a staggered one: quiet", g.hero.slash.get("quiet"))
for _ in range(30): g.update(1 / 60, keys)
print("killed:", not z.alive)
# panic narrows the view
g = play.Game(); g.condition.tension = 1.0; g.update(1 / 60, keys)
print("view scale at full panic:", round(g.vision.scale, 2))
# death card
g = play.Game(); g.to_spawn = 0
for z in g.zombies: z.state = "dead"; z.timer = 9
for _ in range(90): g.update(1 / 60, keys)
g.hero.hp = 0; g.hero.dead = 0.001; g.death_cause = "피폭체에게 당했다"; g.death_time = g.clock; g.kills = 3
for _ in range(40): g.update(1 / 60, keys)
shot(g, "death_card")
for _ in range(120): g.update(1 / 60, keys)
print("restarted after the card:", g.hero.dead == 0, "| marks now:", g.marks_now())
pico2d.close_canvas(); print("ok")
