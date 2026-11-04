"""The starting shelter's background and furniture collision."""

from tile_map import HEIGHT, WIDTH


SHELTER_SPAWN = (154, 138)
SHELTER_SUPPLY = (350, 277)
SHELTER_EXIT = (702, 229)
FURNITURE = ((36, 346, 257, 437), (586, 344, 729, 437))


class ShelterMap:
    def __init__(self, background):
        self.background = background

    def can_stand(self, x, y, half_size):
        left, right = x - half_size, x + half_size
        bottom, top = y - half_size, y + half_size
        if left < 27 or right > 714 or bottom < 27 or top > 379:
            return False
        return not any(
            left < x2 and right > x1 and bottom < y2 and top > y1
            for x1, y1, x2, y2 in FURNITURE
        )

    def draw(self):
        self.background.draw(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT)
