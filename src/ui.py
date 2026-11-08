"""Shared colours, fonts and drawing helpers so every panel looks the same."""

from math import cos, pi, radians, sin
from pathlib import Path

import pico2d
import sdl2
from pico2d import pico2d as canvas


FONT_PATH = Path(pico2d.__file__).parent / "data" / "ConsolaMalgun.ttf"

# Palette ------------------------------------------------------------------
PANEL = (14, 20, 27)
PANEL_RAISED = (30, 42, 52)
PANEL_ALPHA = 225
BORDER = (64, 80, 92)
BORDER_LIGHT = (135, 170, 157)
TEXT = (232, 230, 220)
MUTED = (150, 165, 175)
DIM = (92, 100, 106)
ACCENT = (252, 218, 143)
PARTY = (97, 197, 156)
ENEMY = (214, 92, 76)
DANGER = (255, 140, 92)
MISS = (181, 197, 209)
CRITICAL = (255, 214, 127)
# Turn resources use BG3's shape language: action circle, bonus triangle,
# reaction star, plus a bar for movement.
ACTION = (96, 200, 118)
BONUS = (240, 152, 64)
REACTION = (186, 132, 236)
MOVE = (112, 168, 214)

_fonts = {}


def enable_blending():
    """Let panels use alpha so the street stays visible behind them."""
    sdl2.SDL_SetRenderDrawBlendMode(canvas.renderer, sdl2.SDL_BLENDMODE_BLEND)


def font(size=16):
    if size not in _fonts:
        _fonts[size] = pico2d.load_font(str(FONT_PATH), size)
    return _fonts[size]


def text_width(text, size=16):
    return sum(size * 0.95 if ord(ch) > 127 else size * 0.55 for ch in text)


def text(x, y, value, color=TEXT, size=16):
    font(size).draw(x, y, value, color)


def text_center(x, y, value, color=TEXT, size=16):
    font(size).draw(x - text_width(value, size) / 2, y, value, color)


def panel(left, bottom, right, top, border=BORDER, fill=PANEL, alpha=PANEL_ALPHA):
    pico2d.draw_rectangle(left, bottom, right, top, *fill, alpha, filled=True)
    pico2d.draw_rectangle(left, bottom, right, top, *border)
    # A faint top highlight gives the flat boxes a little depth.
    pico2d.draw_line(left + 1, top - 1, right - 1, top - 1, *[min(255, c + 24) for c in fill])


def bar(left, bottom, width, height, ratio, color, back=(38, 46, 54)):
    pico2d.draw_rectangle(left, bottom, left + width, bottom + height, *back, filled=True)
    ratio = max(0.0, min(1.0, ratio))
    if ratio:
        pico2d.draw_rectangle(left, bottom, left + width * ratio, bottom + height, *color, filled=True)


def action_icon(x, y, radius, available):
    color = ACTION if available else DIM
    pico2d.draw_circle(x, y, radius, *color, filled=available)
    pico2d.draw_circle(x, y, radius, *color)


def bonus_icon(x, y, radius, available):
    color = BONUS if available else DIM
    points = [(x + radius * cos(radians(90 + 120 * i)), y + radius * sin(radians(90 + 120 * i)))
              for i in range(3)]
    if available:
        # Fill by sweeping horizontal lines between the two sides.
        top, left, right = points
        steps = int(top[1] - left[1])
        for step in range(steps + 1):
            t = step / max(1, steps)
            yy = top[1] - step
            pico2d.draw_line(top[0] + (left[0] - top[0]) * t, yy, top[0] + (right[0] - top[0]) * t, yy, *color)
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        pico2d.draw_line(x1, y1, x2, y2, *color)


def reaction_icon(x, y, radius, available):
    color = REACTION if available else DIM
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else radius * 0.45
        angle = pi / 2 + i * pi / 5
        points.append((x + r * cos(angle), y + r * sin(angle)))
    if available:
        for px, py in points:
            pico2d.draw_line(x, y, px, py, *color)
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        pico2d.draw_line(x1, y1, x2, y2, *color)


def d20_icon(x, y, radius, face, color, size=16):
    hexagon = [(x + radius * cos(radians(90 + 60 * i)), y + radius * sin(radians(90 + 60 * i)))
               for i in range(6)]
    for (x1, y1), (x2, y2) in zip(hexagon, hexagon[1:] + hexagon[:1]):
        pico2d.draw_line(x1, y1, x2, y2, *color)
    text_center(x, y, str(face), color, size)


# Screen regions -------------------------------------------------------------
# The window is the exploration canvas (world + top HUD strip) with a hotbar
# strip added underneath. Each region is drawn with its own viewport so the
# existing world code keeps its coordinates and the bar starts at y = 0.
WORLD_HEIGHT = 480 + 64
BOTTOM_HEIGHT = 104
SCREEN_WIDTH = 768
SCREEN_HEIGHT = WORLD_HEIGHT + BOTTOM_HEIGHT


def _region(top, height):
    sdl2.SDL_RenderSetViewport(canvas.renderer, sdl2.SDL_Rect(0, top, SCREEN_WIDTH, height))
    canvas.canvas_height = height


def begin_world():
    _region(0, WORLD_HEIGHT)


def begin_bottom():
    _region(WORLD_HEIGHT, BOTTOM_HEIGHT)


def end_regions():
    sdl2.SDL_RenderSetViewport(canvas.renderer, None)
    canvas.canvas_height = SCREEN_HEIGHT


def split_mouse(sdl_x, sdl_y):
    """Map an SDL mouse position to ("world", x, y) or ("bottom", x, y)."""
    if sdl_y < WORLD_HEIGHT:
        return "world", sdl_x, WORLD_HEIGHT - 1 - sdl_y
    return "bottom", sdl_x, SCREEN_HEIGHT - 1 - sdl_y


def ring(x, y, radius, color, thickness=3):
    for offset in range(thickness):
        pico2d.draw_circle(x, y, radius - offset, *color)

def ellipse(x, y, rx, ry, color, segments=28, dashed=False):
    points = [(x + rx * cos(2 * pi * i / segments), y + ry * sin(2 * pi * i / segments))
              for i in range(segments)]
    for index, ((x1, y1), (x2, y2)) in enumerate(zip(points, points[1:] + points[:1])):
        if dashed and index % 2:
            continue
        pico2d.draw_line(x1, y1, x2, y2, *color)