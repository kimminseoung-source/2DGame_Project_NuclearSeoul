"""Attack gaps: from a pipe blow's start, when can the hero walk again and when can the next blow
start, with the follow-through cancels on (now) and off (before). Hit an infected so hit-stop counts."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, weapons, hero as hero_rules
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
DT = 1 / 60


def game():
    random.seed(3)
    g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True; g.dev.god = True
    g.hero.weapon = next(w for w in weapons.WEAPONS.values() if w["sprite"] == "pipe")
    z = g.zombies[0]
    for o in g.zombies[1:]: o.x, o.y = -5000, -5000
    g.hero.x, g.hero.y = 400, 500; z.x, z.y = 430, 470; z.hp = 999
    for _ in range(5): g.update(DT, keys)
    return g, z


def walk_again(cancel_on):
    if not cancel_on: hero_rules.CANCEL_MOVE, hero_rules.CANCEL_BLOW = 99, 99
    g, z = game(); h = g.hero
    h.start_slash(z.x, z.y); x0, y0 = h.x, h.y; t = 0.0
    keys[sdl2.SDL_SCANCODE_A] = 1                       # hold "walk left" from the start
    while t < 2:
        g.update(DT, keys); t += DT
        if h.slash is None and h.moving:
            break
    keys[sdl2.SDL_SCANCODE_A] = 0
    hit = h.weapon["hit"]
    return t, hit


def next_blow(cancel_on):
    if not cancel_on: hero_rules.CANCEL_MOVE, hero_rules.CANCEL_BLOW = 99, 99
    g, z = game(); h = g.hero
    h.start_slash(z.x, z.y); first = h.slash; t = 0.0
    while t < 3:
        g.update(DT, keys); t += DT
        h.start_slash(z.x, z.y)                          # mash the button
        if h.slash is not None and h.slash is not first:
            return t
    return None


saved = (hero_rules.CANCEL_MOVE, hero_rules.CANCEL_BLOW)
for on in (False, True):
    hero_rules.CANCEL_MOVE, hero_rules.CANCEL_BLOW = saved
    w, hit = walk_again(on)
    hero_rules.CANCEL_MOVE, hero_rules.CANCEL_BLOW = saved
    n = next_blow(on)
    print(f"{'after' if on else 'before'}: walk again {w:.2f}s, next blow {n:.2f}s  (blow lands at {hit:.2f}s, whole {weapons.WEAPONS['pipe']['time']:.2f}s + rest {weapons.WEAPONS['pipe']['cooldown']:.2f}s)")
print("heavy hit-stop", play.JOLTS["heavy"][0])
pico2d.close_canvas()
