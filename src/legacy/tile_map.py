"""Side-scrolling street and its walkable floor boundaries."""


WIDTH = 768
HEIGHT = 480
# The street's road is about 10 m deep (16 px per metre of depth, see nav.py).
STREET_FLOOR_BOTTOM = 28
STREET_FLOOR_TOP = 188
SPAWN = (120, 108)
EXIT = (1416, 134)
WRECK_LEFT = 610
WRECK_RIGHT = 694
WRECK_Y = 108
WRECK_HALF_DEPTH = 8


class TileMap:
    """A map's picture and where one can stand on it. Each map sets its own floor band."""

    width = WIDTH * 2
    left_edge = 0
    right_edge = width
    floor_bottom = STREET_FLOOR_BOTTOM
    floor_top = STREET_FLOOR_TOP
    has_wreck = True

    def __init__(self, background):
        self.background = background

    def can_stand(self, x, y, half_size):
        return (
            self.left_edge + half_size <= x <= self.right_edge - half_size
            and self.floor_bottom + half_size <= y <= self.floor_top - half_size
            and not (
                self.has_wreck
                and WRECK_LEFT - half_size < x < WRECK_RIGHT + half_size
                and abs(y - WRECK_Y) < WRECK_HALF_DEPTH + half_size
            )
        )

    def draw(self, camera_x=0):
        self.background.clip_draw(camera_x, 0, WIDTH, HEIGHT, WIDTH // 2, HEIGHT // 2)
