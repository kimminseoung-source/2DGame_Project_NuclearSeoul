"""The area being fought in: its size, the wrecks that block movement and sight, and where the
infected start. Bodies slide along the wrecks one axis at a time."""

ROOM_W, ROOM_H = 1000, 640
# wrecked cars and rubble: (left, bottom, right, top) on the ground plane
BLOCKS = [(260, 300, 360, 340), (520, 120, 600, 160), (640, 420, 740, 460), (150, 500, 210, 560)]
ZOMBIE_STARTS = [(520, 380), (820, 200), (860, 540), (380, 560), (700, 80)]
HERO_START = (100.0, 300.0)


def blocked(x, y, pad=8):
    return (not (pad <= x <= ROOM_W - pad and pad <= y <= ROOM_H - pad)
            or any(l - pad <= x <= r + pad and b - pad / 2 <= y <= t + pad / 2 for l, b, r, t in BLOCKS))


def move_body(body, dx, dy):
    """Slide along obstacles one axis at a time."""
    if not blocked(body.x + dx, body.y):
        body.x += dx
    if not blocked(body.x, body.y + dy):
        body.y += dy
