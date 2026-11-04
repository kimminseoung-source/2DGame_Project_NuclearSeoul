"""Visuals shared by the field pickup and its HUD slot."""

import pico2d


def draw_filter_icon(x, y, scale=1.0):
    pico2d.draw_rectangle(x - 9 * scale, y - 11 * scale, x + 9 * scale, y + 7 * scale, 215, 167, 74, filled=True)
    pico2d.draw_rectangle(x - 6 * scale, y + 8 * scale, x + 6 * scale, y + 11 * scale, 144, 157, 160, filled=True)
    pico2d.draw_rectangle(x - 6 * scale, y - 4 * scale, x + 6 * scale, y + 1 * scale, 66, 53, 40, filled=True)


def draw_filter_slot(x, y, count, font):
    pico2d.draw_rectangle(x, y, x + 147, y + 48, 33, 46, 56, filled=True)
    pico2d.draw_rectangle(x, y, x + 147, y + 48, 76, 98, 108)
    draw_filter_icon(x + 20, y + 24)
    font.draw(x + 39, y + 34, "Spare filter", (203, 219, 228))
    font.draw(x + 39, y + 14, f"x{count}", (250, 219, 146))
