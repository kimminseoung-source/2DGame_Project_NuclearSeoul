"""Marks drawn on the ground in whole canvas pixels: dots, lines, arcs, wedges, boxes.

Shared by the F1 hit boxes (dev_tools) and the in-game attack tells (attack_tells), 2026-11-20.
Coordinates are world units relative to the camera (what draw_world uses).
"""

from math import cos, hypot, sin

import pico2d

from settings import DOT

# The world canvas has DOT canvas px per world unit (< 1), so a 1-unit line falls between pixels and
# parts of it vanish: every mark is made of whole canvas pixels instead.
PIXEL = 1 / DOT


def dot(x, y, colour):
    qx, qy = round(x * DOT) / DOT, round(y * DOT) / DOT
    pico2d.draw_rectangle(qx, qy, qx + PIXEL * 0.99, qy + PIXEL * 0.99, *colour, filled=True)


def line(x0, y0, x1, y1, colour, gap=1):
    n = max(1, int(hypot(x1 - x0, y1 - y0) * DOT / gap))
    for i in range(n + 1):
        dot(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, colour)


def arc(x, y, radius, a0, a1, colour, gap=1):
    n = max(2, int(radius * abs(a1 - a0) * DOT / gap))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        dot(x + cos(a) * radius, y + sin(a) * radius, colour)


def wedge(x, y, radius, ang, half, colour, gap=1):
    """The area a blow covers: radius out from (x, y), half radians either side of ang."""
    arc(x, y, radius, ang - half, ang + half, colour, gap)
    for a in (ang - half, ang + half):
        line(x, y, x + cos(a) * radius, y + sin(a) * radius, colour, gap)


def box(l, b, r, t, colour, gap=1):
    line(l, b, r, b, colour, gap)
    line(l, t, r, t, colour, gap)
    line(l, b, l, t, colour, gap)
    line(r, b, r, t, colour, gap)
