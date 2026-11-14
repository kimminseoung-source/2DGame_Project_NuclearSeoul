"""Horizontal camera shared by every object that draws in the street."""

from tile_map import WIDTH


x = 0


def reset():
    global x
    x = 0


def follow(target_x, map_width):
    """Keep the target centred without showing past either end of the map."""
    global x
    x = max(0, min(round(target_x) - WIDTH // 2, map_width - WIDTH))
