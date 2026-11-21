"""Legs, crawlers and the stomp off (settings.LEGS_AND_CRAWLERS = False)."""
import sys, random; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, weapons, infected, dev_tools
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
prone = total = 0
for seed in range(8):                          # area starts, several times (was 30: ran out of picture memory with the 3D hero)
    random.seed(seed); g = play.Game()
    total += len(g.zombies); prone += sum(z.prone for z in g.zombies)
    for _ in range(40):                        # newcomers through the entrances
        g.spawn()
    total += len(g.zombies); prone += sum(z.prone for z in g.zombies)
print("infected made", total, "crawling", prone)
z = infected.Zombie(g.zombie_look, 0, 0, crawler=True)
print("asked for a crawler -> prone:", z.prone)
print("parts by height:", {up: weapons.path_part(z, up) for up in (2, 10, 17, 25, 34, 40)})
print("F4 rows with 기어가는:", [r[0] for r in dev_tools.ROWS if "기어가는" in r[0]])
pico2d.close_canvas(); print("ok")
