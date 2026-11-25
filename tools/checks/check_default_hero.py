"""Default game (src/main.py Game) = red-jacket hero (2026-11-25): pistol D look with FACE-R1 heads,
melee look after Q, moving shot hits and keeps the legs, death art, R restart. Numbers only."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
import pico2d
import sdl2
from pico2d import pico2d as p2


def main():
    create = p2.SDL_CreateWindow
    p2.SDL_CreateWindow = lambda t, x, y, w, h, f: create(t, x, y, w, h, (f | sdl2.SDL_WINDOW_HIDDEN) & ~sdl2.SDL_WINDOW_SHOWN)
    from settings import DOT, HEIGHT, WIDTH
    pico2d.open_canvas(WIDTH, HEIGHT, sync=False)
    import main as game_main
    import ui
    import weapons
    from infected import Zombie
    from pistol_hero import IDENTITY, MeleeLook, PistolLook, RedJacketGame
    ui.enable_blending()
    assert game_main.Game is RedJacketGame, game_main.Game
    g = RedJacketGame()
    keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
    g.zombies = []; g.to_spawn = 0; g.dev.no_spawn = True; g.dev.god = True
    g.used.update(a for a, _ in g.TEACH)

    def tick(n=1):
        for _ in range(n):
            g.update(1 / 60, keys)
            pico2d.clear_canvas(); g.draw()
    out = []
    hero = g.hero
    assert isinstance(hero.look, PistolLook) and hero.weapon is weapons.WEAPONS["pistol"]
    assert g.ammo == weapons.WEAPONS["pistol"]["shot"]["rounds"]
    assert g.bag.get(weapons.item(weapons.DEFAULT)) == 1
    out.append(f"start: pistol in hand, ammo {g.ammo}, {weapons.DEFAULT} in bag")
    # FACE-R1: every loaded state/walk key comes from identity/ (head shared)
    srcs = g.pistol_look.sources
    assert all(IDENTITY in p.parents for p in srcs.values()), srcs
    out.append(f"FACE-R1 sources: {len(srcs)} keys all under identity/")
    tick(3)
    keys[sdl2.SDL_SCANCODE_D] = 1
    seen = set()
    for _ in range(120):
        tick(); seen.add(g.pistol_look.sprite)
    walk = {s for s in seen if s.startswith("walk_")}
    assert len(walk) == 8, seen
    out.append(f"walk keys reached {len(walk)}/8, contacts {g.foot_contacts}")
    assert g.foot_contacts > 0
    keys[sdl2.SDL_SCANCODE_D] = 0
    tick(10)
    # moving shot
    hero.start_ready(); tick(15)
    keys[sdl2.SDL_SCANCODE_D] = 1; tick(10)
    z = Zombie(g.zombie_look, hero.x + 85, hero.y); g.zombies = [z]; hp = z.health
    scale = g.zoom * DOT
    sx = (z.x - g.cam[0]) * scale; sy = HEIGHT - 1 - (z.y + 22 - g.cam[1]) * scale
    g.aim = (sx, sy); ammo = g.ammo; g.release(sx, sy)
    during = []
    for _ in range(30):
        tick()
        if g.pistol_look.recoil > 0:
            during.append(g.pistol_look.sprite)
    keys[sdl2.SDL_SCANCODE_D] = 0
    assert g.ammo == ammo - 1 and z.health < hp, (g.ammo, ammo, z.health, hp)
    assert during and all(s.startswith("aim_walk_") for s in during), during
    out.append(f"moving shot: ammo {ammo}->{g.ammo}, hp {hp}->{z.health}, legs {len(during)} frames aim_walk")
    g.zombies = []; tick(20)
    # Q -> melee look
    g.next_weapon(); tick(2)
    assert weapons.key_of_weapon(hero.weapon) == weapons.DEFAULT and isinstance(hero.look, MeleeLook)
    keys[sdl2.SDL_SCANCODE_D] = 1; tick(60); keys[sdl2.SDL_SCANCODE_D] = 0
    assert g.melee_look.travel > 0 and g.melee_look.last_state[1].startswith(("walk_", "idle"))
    out.append(f"Q: {weapons.DEFAULT} in hand, melee look, travel {g.melee_look.travel:.0f}")
    g.next_weapon(); tick(2)
    assert isinstance(hero.look, PistolLook)
    out.append("Q again: pistol look back")
    # death art
    g.dev.god = False; hero.hp = 0; hero.dead = 0.01
    tick(2); a = g.pistol_look.sprite
    tick(40); b = g.pistol_look.sprite
    out.append(f"death sprites: {a} -> {b}")
    # R restart
    g.key_down(sdl2.SDLK_r, keys); tick(2)
    assert isinstance(g.hero.look, PistolLook) and g.ammo == weapons.WEAPONS["pistol"]["shot"]["rounds"]
    assert g.bag.get(weapons.item(weapons.DEFAULT)) == 1
    out.append("R restart: pistol + full rounds + 1 machete again")
    pico2d.close_canvas()
    print("\n".join(out))
    print("check_default_hero: PASS")


if __name__ == "__main__":
    main()
