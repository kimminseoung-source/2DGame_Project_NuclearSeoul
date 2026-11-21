"""Stamina costs, tired actions, regen; the quiet takedown."""
import sys, random
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, stamina
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
def fresh(seed=1):
    random.seed(seed); g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]; g.hero.x, g.hero.y = 420, 240; z.x, z.y = 900, 600; z.state = "idle"
    for _ in range(60): g.update(1 / 60, keys)
    return g, g.hero, z
def scr(g, wx, wy): return (wx - g.cam[0]) * (g.zoom * settings.DOT), settings.HEIGHT - 1 - (wy - g.cam[1]) * (g.zoom * settings.DOT)
g, h, z = fresh()
swings, times = 0, []
for i in range(12):
    h.slash_cooldown = 0
    g.click(*scr(g, h.x + 60, h.y + settings.CHEST))
    if h.slash: times.append(round(h.slash["whole"], 2)); swings += 1
    while h.slash: g.update(1 / 60, keys)
print("air swings in a row:", swings, "| stamina", round(h.stamina.value), "| swing lengths", times)
ok = h.start_roll(1, 0); print("roll when out of breath:", ok, "| message after Space:", end=" ")
g.key_down(sdl2.SDLK_SPACE, keys); print(g.message)
t = 0
while h.stamina.value < stamina.MAX and t < 10:
    g.update(1 / 60, keys); t += 1 / 60
print(f"back to full after {t:.1f}s standing")
h.stamina.value = 0
z.x, z.y, z.state = h.x + 30, h.y, "chase"
for _ in range(3): g.update(1/60, keys)
g.right_click(*scr(g, z.x, z.y + settings.CHEST)); print("tired shove ->", z.state, "| weak", h.shove_weak, "|", g.message)
# no takedown any more (2026-11-16 "기습 성공하는 건 빼죠"): an unaware one gets the quiet slash
g, h, z = fresh(2); z.prone = False
z.x, z.y, z.state, z.heading = h.x + 50, h.y, "idle", 0.0
g.click(*scr(g, z.x, z.y + settings.CHEST)); q = h.slash and h.slash.get("quiet")
for _ in range(40): g.update(1 / 60, keys)
print("unaware: quiet slash", q, "| killed", not z.alive)
# a close infected that has seen him: normal slash, no takedown
g, h, z = fresh(3)
z.x, z.y, z.state = h.x + 30, h.y, "chase"
g.click(*scr(g, z.x, z.y + settings.CHEST)); print("aware one: slash", h.slash and h.slash["pose"])
g.draw(); print("draw ok")
