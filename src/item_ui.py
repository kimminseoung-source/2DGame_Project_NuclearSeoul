"""Visuals shared by the field pickup and its HUD slot."""

import pico2d


def draw_filter_icon(x, y):
    pico2d.draw_rectangle(x - 9, y - 11, x + 9, y + 7, 215, 167, 74, filled=True)
    pico2d.draw_rectangle(x - 6, y + 8, x + 6, y + 11, 144, 157, 160, filled=True)
    pico2d.draw_rectangle(x - 6, y - 4, x + 6, y + 1, 66, 53, 40, filled=True)


def draw_filter_slot(x, y, count, font):
    pico2d.draw_rectangle(x, y, x + 147, y + 48, 33, 46, 56, filled=True)
    pico2d.draw_rectangle(x, y, x + 147, y + 48, 76, 98, 108)
    draw_filter_icon(x + 20, y + 24)
    font.draw(x + 39, y + 34, "Spare filter", (203, 219, 228))
    font.draw(x + 39, y + 14, f"x{count}", (250, 219, 146))
