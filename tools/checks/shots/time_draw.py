import sys, random, time; sys.path.insert(0, "src")
import pico2d, sdl2, play, settings, ui, character_look
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
random.seed(1); g = play.Game(); g.dev.freeze = True; g.dev.no_spawn = True
for _ in range(5): g.update(1/60, keys)
def t(label):
    for _ in range(20): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    t0 = time.perf_counter()
    for _ in range(120): pico2d.clear_canvas(); g.draw(); pico2d.update_canvas()
    print(label, round(1000 * (time.perf_counter() - t0) / 120, 1), "ms")
t("new look, key poses"); character_look.DirLook.key_poses = False; t("key poses off")
character_look.DirLook.on = False; t("old look"); character_look.DirLook.on = True; t("new look again")
pico2d.close_canvas()
