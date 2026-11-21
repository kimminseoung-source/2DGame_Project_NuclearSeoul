"""How long a frame's darkness takes to build and draw, near the house (many walls) and on the road."""
import sys, time; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, area
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True
for _ in range(3): g.update(1 / 60, keys)
spots = {"road": (area.BLOCKS[area.BLOCK_LOOKS.index("wreck_1")][0] - 150, 650)}
if area.BUILDINGS:
    l, b, r, t = area.BUILDINGS[0]["box"]
    spots["house"] = ((l + r) / 2, (b + t) / 2)
for name, (x, y) in spots.items():
    g.hero.x, g.hero.y = x, y
    for _ in range(5): g.update(1 / 60, keys)
    t0 = time.perf_counter()
    for _ in range(60):
        pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    whole = (time.perf_counter() - t0) / 60 * 1000
    t0 = time.perf_counter()
    for _ in range(60):
        g.vision.draw((g.hero.x, g.hero.y), g.look, (100, 100), g.view_w, g.view_h)
    print(f"{name}: whole frame {whole:.1f} ms, darkness {((time.perf_counter() - t0) / 60 * 1000):.1f} ms")
pico2d.close_canvas(); print("ok")
