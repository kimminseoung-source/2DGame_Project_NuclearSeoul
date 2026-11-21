"""Does the drawn darkness match the computed one? Draw only the vision mesh on white, read it back,
compare every 4th canvas pixel with VisionCone.darkness at that ground point. Several eyes around
wrecks and the house; reports how many points disagree by more than a little."""
import sys, ctypes, random; sys.path.insert(0, "src")
from math import atan2, pi
import pico2d, sdl2, play, settings, ui, area, vision_cone
from pico2d import pico2d as canvas
from PIL import Image
keys = (sdl2.Uint8 * sdl2.SDL_NUM_SCANCODES)()
pico2d.open_canvas(settings.WIDTH, settings.HEIGHT, sync=False); ui.enable_blending()
g = play.Game(); g.dev.freeze = True
for _ in range(3): g.update(1 / 60, keys)
DOT = settings.DOT
cw, ch = g.canvas_size
view_w, view_h = cw / DOT, ch / DOT
target = sdl2.SDL_CreateTexture(canvas.renderer, sdl2.SDL_PIXELFORMAT_RGBA8888, sdl2.SDL_TEXTUREACCESS_TARGET, cw, ch)
cases = []
for look_name in ("wreck_0", "wreck_1"):
    j = area.BLOCK_LOOKS.index(look_name); l, b, r, t = area.BLOCKS[j]
    cases += [((l - 150, (b + t) / 2 - 22), atan2(22, 150 + (r - l) / 2)), ((l - 120, b - 60), 0.4), (((l + r) / 2, b - 90), pi / 2)]
random.seed(1)
bad_total = n_total = 0
worst_img = None
for eye, look in cases:
    cam = (eye[0] - view_w / 2, eye[1] - view_h / 2)
    sdl2.SDL_SetRenderTarget(canvas.renderer, target)
    sdl2.SDL_RenderSetScale(canvas.renderer, DOT, DOT)
    sdl2.SDL_SetRenderDrawColor(canvas.renderer, 255, 255, 255, 255)
    sdl2.SDL_RenderClear(canvas.renderer)
    canvas.canvas_height = view_h
    g.vision.draw(eye, look, (eye[0] - cam[0], eye[1] - cam[1]), view_w, view_h)
    sdl2.SDL_RenderSetScale(canvas.renderer, 1, 1)
    s = sdl2.SDL_CreateRGBSurfaceWithFormat(0, cw, ch, 32, sdl2.SDL_PIXELFORMAT_ARGB8888)
    sdl2.SDL_RenderReadPixels(canvas.renderer, None, sdl2.SDL_PIXELFORMAT_ARGB8888, s.contents.pixels, s.contents.pitch)
    im = Image.frombuffer("RGBA", (cw, ch), ctypes.string_at(s.contents.pixels, s.contents.pitch * ch), "raw", "BGRA", s.contents.pitch, 1).convert("L")
    sdl2.SDL_SetRenderTarget(canvas.renderer, None)
    px = im.load()
    bad = n = 0
    for y in range(0, ch, 4):
        for x in range(0, cw, 4):
            wx, wy = cam[0] + (x + 0.5) / DOT, cam[1] + (ch - y - 0.5) / DOT
            want = g.vision.darkness(eye, look, wx, wy, drawn=True)   # 0..fog alpha of near-black over white
            got = 255 - px[x, y]                                   # how much the white was darkened
            n += 1
            if abs(got - want) > 45:
                bad += 1
    bad_total += bad; n_total += n
    print(f"eye ({eye[0]:.0f},{eye[1]:.0f}) look {look:.2f}: {bad} of {n} points off by >45 ({100 * bad / n:.1f}%)")
print(f"all: {100 * bad_total / n_total:.2f}% off")
pico2d.close_canvas(); print("ok")
