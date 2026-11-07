"""Side-scrolling street and its walkable floor boundaries."""


WIDTH = 768
HEIGHT = 480
FLOOR_BOTTOM = 28
FLOOR_TOP = 126
SPAWN = (120, 78)
SUPPLY = (312, 104)
EXIT = (1416, 104)


class TileMap:
    width = WIDTH * 2
    left_edge = 0
    right_edge = width

    def __init__(self, background):
        self.background = background

    def can_stand(self, x, y, half_size):
        return (
            self.left_edge + half_size <= x <= self.right_edge - half_size
            and FLOOR_BOTTOM + half_size <= y <= FLOOR_TOP - half_size
        )

    def draw(self, camera_x=0):
        self.background.clip_draw(camera_x, 0, WIDTH, HEIGHT, WIDTH // 2, HEIGHT // 2)
