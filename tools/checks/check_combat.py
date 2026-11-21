"""Tempo, reach, the infected's claw arc, the hit reaction (no blink) and the auto chop."""
import sys, random
from math import atan2, hypot, pi
sys.path.insert(0, sys.argv[1])
import pico2d, sdl2, play, settings, ui, infected
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
S = settings.SCALE
def screen(g, wx, wy):
    return (wx - g.cam[0]) * S, settings.HEIGHT - 1 - (wy - g.cam[1]) * S
def fresh():
    random.seed(1)
    g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    g.update(1 / 60, keys)
    return g, g.hero, z
# 1. slash timing
g, h, z = fresh(); z.x, z.y = 900, 600
g.click(*screen(g, h.x + 50, h.y + settings.CHEST))
t = 0; hit_t = None
while h.slash and t < 2:
    g.update(1 / 60, keys); t += 1 / 60
    if hit_t is None and h.slash and h.slash["hit"]: hit_t = t
print(f"slash lasts {t:.2f}s (was 0.26), hits at {hit_t:.2f}s (was 0.06)")
# 2. reach: an idle infected 66 px ahead (old reach 70 hit it), 50 px ahead hits
for gap in (100, 90, 80):
    g, h, z = fresh(); z.state = "idle"
    z.x, z.y = h.x + gap + settings.SLASH_LUNGE * 0.0, h.y
    h.slash_cooldown = 0
    g.click(*screen(g, z.x, z.y + settings.CHEST))
    lunge_x0, hp0 = h.x, z.health
    for _ in range(40): g.update(1 / 60, keys)
    print(f"infected {gap + 0}px ahead -> {'hit' if (not z.alive or z.health < hp0) else 'missed'} (hero lunged {h.x - lunge_x0:.0f}px)")
# 3. claw arc: windup, hero steps round behind it -> miss; stays in front -> hit
for where in ("front", "behind"):
    g, h, z = fresh()
    z.x, z.y = h.x + 26, h.y; z.state, z.timer, z.windup = "windup", settings.ZOMBIE_WINDUP, settings.ZOMBIE_WINDUP
    z.heading = pi
    if where == "behind":
        h.x = z.x + 26
    hp = h.hp
    for _ in range(60): g.update(1 / 60, keys)
    print(f"claw with hero {where}: hp {hp:.0f} -> {h.hp:.0f}")
# 4. hit reaction: reeling pose, no blink, no slash while reeling
g, h, z = fresh()
z.x, z.y = h.x + 26, h.y; z.state, z.timer, z.windup = "windup", 0.01, 0.01; z.heading = pi
for _ in range(3): g.update(1 / 60, keys)
print("after a blow: reeling", round(h.reeling, 2), "safe", round(h.hurt, 2))
before = h.slash; h.start_slash(h.x + 50, h.y); print("slash while reeling started:", h.slash is not before)
drawn = []
orig = h.look.draw
h.look.draw = lambda pose, *a, **k: drawn.append(pose)
for _ in range(10): h.draw(*g.cam); g.update(1 / 60, keys)
h.look.draw = orig
print("drawn poses while hurt:", sorted(set(drawn)), "frames drawn", len(drawn), "/ 10")
# 5. a crawler gets the stomp, a standing one the slash
for crawler in (True, False):
    g, h, z = fresh()
    z.prone = crawler; z.x, z.y, z.state = h.x + 40, h.y, "chase"
    g.click(*screen(g, z.x, z.y + settings.CHEST))
    pose = h.slash and h.slash["pose"]
    for _ in range(50): g.update(1 / 60, keys)
    print(f"crawler {crawler}: pose {pose}, killed {not z.alive}")
