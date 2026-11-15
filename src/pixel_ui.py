"""Drawing on the UI's pixel canvas (2026-11-16, UI v2 "AI 티가 안 나게").

The UI is laid out on a 640 x 360 canvas (top-left origin, like the mockups in tools/ui/) and
every canvas pixel is drawn as a K x K block, so the UI shares the game's chunky pixel grid:
no smoothing, no half-transparent glass. Text is Galmuri at its native 12 px rendered without
anti-aliasing (SDL_ttf "Solid") and scaled x K, with a 1-pixel dark outline instead of a soft
shadow. Rendered text is cached, so drawing it every frame costs nothing new.
"""

from pathlib import Path

import pico2d
import sdl2
from sdl2 import sdlttf

from settings import HEIGHT, WIDTH

CW, CH = 640, 360
K = WIDTH // CW                     # canvas pixel -> screen pixels (2 at 1280 x 720)
ROOT = Path(__file__).resolve().parents[1]
FONTS = {False: ROOT / "assets/fonts/galmuri/Galmuri11.ttf", True: ROOT / "assets/fonts/galmuri/Galmuri11-Bold.ttf"}
EDGE = (8, 8, 10)

_fonts, _texts, _images = {}, {}, {}


def rect(l, t, r, b, colour):
    """Fill canvas pixels l..r, t..b inclusive."""
    pico2d.draw_rectangle(l * K, HEIGHT - (b + 1) * K, (r + 1) * K - 1, HEIGHT - t * K - 1,
                          *colour[:3], colour[3] if len(colour) > 3 else 255, filled=True)


def frame(l, t, r, b, colour):
    """A 1-canvas-pixel outline."""
    rect(l, t, r, t, colour)
    rect(l, b, r, b, colour)
    rect(l, t, l, b, colour)
    rect(r, t, r, b, colour)


def image(name):
    if name not in _images:
        _images[name] = pico2d.load_image(str(ROOT / "assets" / "ui" / name))
    return _images[name]


def blit(name, x, y):
    """Draw a canvas-sized picture with its top-left corner at canvas (x, y)."""
    img = image(name)
    pico2d.Image.draw(img, (x + img.w / 2) * K, HEIGHT - (y + img.h / 2) * K, img.w * K, img.h * K)


def _font(bold):
    if bold not in _fonts:
        if not sdlttf.TTF_WasInit():
            sdlttf.TTF_Init()
        _fonts[bold] = sdlttf.TTF_OpenFont(str(FONTS[bold]).encode("utf-8"), 12)
    return _fonts[bold]


def _text_image(s, colour, bold):
    key = (s, tuple(colour[:3]), bold)
    if key not in _texts:
        surface = sdlttf.TTF_RenderUTF8_Solid(_font(bold), s.encode("utf-8"), sdl2.SDL_Color(*colour[:3]))
        texture = sdl2.SDL_CreateTextureFromSurface(pico2d.pico2d.renderer, surface)
        sdl2.SDL_FreeSurface(surface)
        _texts[key] = pico2d.Image(texture)
        if len(_texts) > 600:                       # many one-off messages: start over
            _texts.clear()
    return _texts[key]


def width(s, bold=False):
    return _text_image(s, (255, 255, 255), bold).w if s else 0


def text(x, y, s, colour, bold=False, anchor="l", outline=True):
    """Text with its top at canvas y; anchor l / m / r on x."""
    if not s:
        return
    img = _text_image(s, colour, bold)
    x = x - img.w if anchor == "r" else x - img.w // 2 if anchor == "m" else x
    cx, cy = (x + img.w / 2) * K, HEIGHT - (y + img.h / 2) * K
    if outline:
        edge = _text_image(s, EDGE, bold)
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
            edge.draw(cx + ox * K, cy - oy * K, img.w * K, img.h * K)
    img.draw(cx, cy, img.w * K, img.h * K)


def key_cap(x, y, key, label, light, ink, label_colour):
    """A square key cap and what it does; returns the x after it."""
    w = width(key) + 5
    rect(x, y, x + w, y + 12, light)
    frame(x, y, x + w, y + 12, ink)
    text(x + 3, y + 1, key, ink, outline=False)
    text(x + w + 4, y + 1, label, label_colour)
    return x + w + width(label) + 14


def to_canvas(sx, sy):
    """Screen (SDL, top-left origin) to canvas pixels."""
    return sx / K, sy / K
