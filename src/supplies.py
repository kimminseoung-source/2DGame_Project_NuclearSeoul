"""Supplies on the ground and the bag (1차 발표 단계 01 "탐색 기반": find supplies, reach the exit).

E picks up the nearest supply within reach - rummaging makes a little noise the infected can
hear. 1 uses a bandage (stops the worst bleeding, +15% health), 2 a suppressant (exposure -30). Cans are carried for the
journey (stage 03). Each kind is just data here, so new supplies need only a new entry.
"""

import pico2d

import ui

PICK_RANGE = 28            # px from the hero's feet
PICK_NOISE = 100           # px the rummaging carries

KINDS = {
    # kind: (name, body colour, band colour, description shown in the bag, weight)
    "bandage": ("붕대", (220, 216, 200), (120, 160, 120), "가장 심한 상처의 피를 멈추고 체력 +15%", 0.1),
    "pill": ("피폭 억제제", (70, 150, 90), (200, 240, 200), "피폭을 늦춘다. 피폭 -30", 0.1),
    "can": ("통조림", (150, 150, 158), (190, 120, 60), "오래 버티는 식량. 다음 구역 여정에 쓴다", 0.4),
}
BAG_CAPACITY = 2.0          # the bag holds this much weight (Zomboid: weight, not slots)


def weight_of(kind):
    import weapons
    key = weapons.key_of(kind)
    return weapons.WEIGHT[key] if key else KINDS[kind][4]


def item_name(kind):
    import weapons
    key = weapons.key_of(kind)
    return weapons.WEAPONS[key]["name"] if key else KINDS[kind][0]


def item_text(kind):
    """The line shown for a bag item: what a supply does, or a weapon's way of hitting."""
    import weapons
    key = weapons.key_of(kind)
    if not key:
        return KINDS[kind][3]
    w = weapons.WEAPONS[key]
    return f"속도 {weapons.speed_word(w)} · + {w['good']} · - {w['bad']}"


def bag_weight(bag):
    return sum(weight_of(kind) * n for kind, n in bag.items())
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
        _, body, band = KINDS[self.kind][:3]
        x, y = self.x - cx, self.y - cy
        pico2d.draw_rectangle(x - 6, y - 2, x + 6, y + 6, 14, 14, 18, filled=True)        # shadow / outline
        pico2d.draw_rectangle(x - 5, y - 1, x + 5, y + 5, *body, filled=True)
        pico2d.draw_rectangle(x - 5, y + 1, x + 5, y + 3, *band, filled=True)
        if near:
            ui.world_text_center(x, y - 12, f"E {self.name}", (240, 230, 190), 12)   # under it, clear of the body


def has_final_consonant(word):
    last = word[-1]
    return "가" <= last <= "힣" and (ord(last) - ord("가")) % 28 != 0


def with_object_particle(word):
    """'붕대를', '통조림을': 을 after a final consonant, 를 otherwise."""
    return word + ("을" if has_final_consonant(word) else "를")


def with_subject_particle(word):
    """'붕대가', '통조림이'."""
    return word + ("이" if has_final_consonant(word) else "가")


def nearest(supplies, x, y):
    best, best_d = None, PICK_RANGE
    for s in supplies:
        if not s.taken:
            d = ((s.x - x) ** 2 + (s.y - y) ** 2) ** 0.5
            if d <= best_d:
                best, best_d = s, d
    return best
