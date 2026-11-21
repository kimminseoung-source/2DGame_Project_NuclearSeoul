"""Shove off, counter moved to the blow: right click does nothing; a blow at the end of the claw wind-up
reels it for COUNTER_STAGGER (pushed further); a blow earlier gives the normal reaction. Hero is hero_3d."""
import sys, random
from math import pi
sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, infected
from infected import COUNTER_WINDOW, COUNTER_STAGGER
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
S = settings.SCALE
print("SHOVE_ON", settings.SHOVE_ON, "| hero folder", play.HERO_PX, "| DirLook", type(play.Game().hero_look).__name__)
def screen(g, wx, wy):
    return (wx - g.cam[0]) * S, settings.HEIGHT - 1 - (wy - g.cam[1]) * S
def fresh():
    random.seed(1)
    g = play.Game(); g.to_spawn = 0
    z = g.zombies[0]; z.prone = False; g.zombies[:] = [z]
    g.hero.x, g.hero.y = 420, 240
    g.update(1 / 60, keys)
    z.health = 99                                   # survives the blow
    return g, g.hero, z
# 1. right click in play: nothing moves
g, h, z = fresh(); z.x, z.y = h.x + 22, h.y; z.state, z.timer, z.windup = "windup", 0.1, 0.5; z.heading = pi
x0 = z.x; g.right_click(*screen(g, z.x, z.y + settings.CHEST))
print(f"우클릭: 피폭체 상태 {z.state}, 움직임 {z.x - x0:.1f}, 밀치기 기록 {'shove' in g.used}")
# 2. blow during the counter window vs early in the wind-up
for name, left in (("받아치기 때", COUNTER_WINDOW * 0.5), ("준비 초반", 0.45)):
    g, h, z = fresh()
    z.x, z.y = h.x + 40, h.y; z.state, z.timer, z.windup = "windup", left, 0.5; z.heading = pi
    z.attack_cool = 9
    h.slash_cooldown = 0
    ready = None; x0 = z.x; worst_state = None; t_hit = None
    g.click(*screen(g, z.x, z.y + settings.CHEST))
    for i in range(30):
        if ready is None and h.slash and h.slash["hit"]:
            pass
        before = z.health
        if z.state == "windup": ready = z.counter_ready()
        g.update(1 / 60, keys)
        if z.health < before and t_hit is None:
            t_hit = i; worst_state = (z.state, round(z.timer, 2), round(getattr(z, "stagger_time", 0), 2))
            hit_ready = ready
    print(f"{name}: 맞은 순간 받아치기={hit_ready if t_hit is not None else '-'}, 맞은 뒤 (상태, 남은 시간, 휘청 길이)={worst_state}, 밀린 거리 {z.x - x0:.1f}")
print("COUNTER_STAGGER", COUNTER_STAGGER)
