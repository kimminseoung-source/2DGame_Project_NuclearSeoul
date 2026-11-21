"""Chained rolls (2026-11-21 "연속 2번 구르기가 안 되지 않나"): Space pressed during a roll starts the
next one right after it ends (ROLL_COOLDOWN), each roll puts its own dust; a third with no charge left
does not go."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, dodge_fx, hero as hero_rules
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(2)
g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.zombies[:] = []
for _ in range(5): g.update(1 / 60, keys)
h = g.hero; x0 = h.x
keys[sdl2.SDL_SCANCODE_D] = 1
g.key_down(sdl2.SDLK_SPACE, keys)                       # first roll
t, starts, ends, dusts, prev = 0.0, [0.0], [], 0, True
for f in range(150):
    if f in (5, 25, 45):                                # Space again while rolling (2nd), and a 3rd
        g.key_down(sdl2.SDLK_SPACE, keys)
    n_before = sum(isinstance(e, dodge_fx.Dust) for e in g.effects)
    g.update(1 / 60, keys); t += 1 / 60
    dusts += sum(isinstance(e, dodge_fx.Dust) for e in g.effects) > n_before
    rolling = h.roll > 0
    if prev and not rolling: ends.append(round(t, 3))
    if not prev and rolling: starts.append(round(t, 3))
    prev = rolling
keys[sdl2.SDL_SCANCODE_D] = 0
print("ROLL_COOLDOWN", hero_rules.ROLL_COOLDOWN, "roll time", round(settings.ROLL_TIME, 3))
print("starts", starts, "ends", ends)
gaps = [round(s - e, 3) for e, s in zip(ends, starts[1:])]
print("gap between rolls (s):", gaps, "| rolls:", len(starts), "| dust puffs at starts:", dusts,
      "| moved", round(h.x - x0), "px (walking adds the rest)")
