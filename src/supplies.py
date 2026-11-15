"""Supplies on the ground and the bag (1차 발표 단계 01 "탐색 기반": find supplies, reach the exit).

E picks up the nearest supply within reach - rummaging makes a little noise the infected can
hear. 1 uses a bandage (+1 health), 2 a suppressant (exposure -30). Cans are carried for the
journey (stage 03). Each kind is just data here, so new supplies need only a new entry.
"""

import pico2d

import ui

PICK_RANGE = 28            # px from the hero's feet
PICK_NOISE = 100           # px the rummaging carries

KINDS = {
    # kind: (name, body colour, band colour)
    "bandage": ("붕대", (220, 216, 200), (120, 160, 120)),
    "pill": ("피폭 억제제", (70, 150, 90), (200, 240, 200)),
    "can": ("통조림", (150, 150, 158), (190, 120, 60)),
}
USE_KEYS = {"bandage": "1", "pill": "2"}
PILL_EFFECT = 30.0


class Supply:
    def __init__(self, x, y, kind):
        self.x, self.y, self.kind = float(x), float(y), kind
        self.taken = False

    @property
    def name(self):
        return KINDS[self.kind][0]

    def draw(self, cx, cy, near=False):
        _, body, band = KINDS[self.kind]
        x, y = self.x - cx, self.y - cy
        pico2d.draw_rectangle(x - 6, y - 2, x + 6, y + 6, 14, 14, 18, filled=True)        # shadow / outline
        pico2d.draw_rectangle(x - 5, y - 1, x + 5, y + 5, *body, filled=True)
        pico2d.draw_rectangle(x - 5, y + 1, x + 5, y + 3, *band, filled=True)
        if near:
            ui.text_center(x, y - 12, f"E {self.name}", (240, 230, 190), 12)   # under it, clear of the body


def with_object_particle(word):
    """'붕대를', '통조림을': 을 after a final consonant, 를 otherwise."""
    last = word[-1]
    has_final = "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0
    return word + ("을" if has_final else "를")


def nearest(supplies, x, y):
    best, best_d = None, PICK_RANGE
    for s in supplies:
        if not s.taken:
            d = ((s.x - x) ** 2 + (s.y - y) ** 2) ** 0.5
            if d <= best_d:
                best, best_d = s, d
    return best
