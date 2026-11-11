"""How a character looks: draws a named pose at a point in time, whatever sprite sheets it uses.

Units ask for a pose ("idle", "walk", "sneak", "swing", "pickup", "hurt", "down") and a
time; the look picks the frame. Looping poses take seconds, one-shot poses take
progress from 0 to 1. Every unit (hero, companions, zombies, hostile survivors) can use
the same calls, so swapping a character's art never touches the unit's code.

SheetLook reads the rendered sheets in assets/characters/<name>/ (see CHARACTER_SPEC.md):
one row per action, 96x64 cells facing right, feet 4 px above the cell bottom.
LegacyLook wraps the first hand-drawn hero sheets so the old art keeps working.
"""

from pathlib import Path

import pico2d


LOOPING = {"idle", "walk", "sneak", "sneak_idle"}
# A pose a character's sheets lack falls back to a close one: (pose, fixed frame or None).
FALLBACK = {"sneak_idle": ("sneak", 0)}


class SheetLook:
    CELL_W, CELL_H = 96, 64
    FEET_FROM_BOTTOM = 4
    # Seconds per frame for looping poses.
    FRAME_TIME = {"idle": 0.22, "sneak_idle": 0.22, "walk": 0.09, "sneak": 0.13}
    # Head and torso of the first idle frame: (left, bottom, width, height) in the cell.
    PORTRAIT = (25, 23, 46, 36)

    def __init__(self, folder):
        self.sheets = {}
        for path in Path(folder).glob("*.png"):
            self.sheets[path.stem] = pico2d.load_image(str(path))

    def frame_count(self, pose):
        return self.sheets[pose].w // self.CELL_W

    def frame_of(self, pose, time):
        count = self.frame_count(pose)
        if pose in LOOPING:
            return int(time / self.FRAME_TIME.get(pose, 0.12)) % count
        return min(count - 1, max(0, int(time * count)))

    def draw(self, pose, time, x, feet_y, facing):
        fixed = None
        if pose not in self.sheets:
            pose, fixed = FALLBACK.get(pose, ("idle", None))
            if pose not in self.sheets:
                pose, fixed = "idle", None
        image = self.sheets[pose]
        frame = self.frame_of(pose, time) if fixed is None else fixed
        y = feet_y - self.FEET_FROM_BOTTOM + self.CELL_H / 2
        flip = "" if facing > 0 else "h"
        image.clip_composite_draw(
            frame * self.CELL_W, 0, self.CELL_W, self.CELL_H, 0, flip,
            x, y, self.CELL_W, self.CELL_H,
        )

    def portrait_clip(self):
        return (self.sheets["idle"], *self.PORTRAIT)


class LegacyLook:
    """The first hand-drawn hero: walk/sneak/action sheets with a left row and a right row."""

    MOVE_W, ACTION_W, FRAME_H = 77, 97, 58
    WALK_CYCLE = (1, 2, 3, 2)
    FRAME_TIME = {"walk": 0.12, "sneak": 0.15}
    SWING_EDGES = (0.41, 0.59, 0.79)   # bat contact, follow-through, recovery as swing progress

    def __init__(self, sprites):
        self.sprites = sprites    # {"walk", "sneak", "action"} images

    def pick(self, pose, time):
        if pose == "sneak_idle":
            return "sneak", 0
        if pose in ("walk", "sneak"):
            step = int(time / self.FRAME_TIME[pose]) % len(self.WALK_CYCLE)
            return pose, self.WALK_CYCLE[step]
        if pose == "swing":
            # The bat's contact, follow-through and recovery frames.
            return "action", 1 + sum(time >= edge for edge in self.SWING_EDGES)
        if pose in ("pickup", "hurt", "down"):
            return "action", 0
        return "walk", 0

    def draw(self, pose, time, x, feet_y, facing):
        sheet, frame = self.pick(pose, time)
        image = self.sprites[sheet]
        width = self.ACTION_W if sheet == "action" else self.MOVE_W
        row = int(facing > 0)
        image.clip_draw(
            frame * width, image.h - (row + 1) * self.FRAME_H, width, self.FRAME_H,
            x, feet_y + self.FRAME_H / 2,
        )

    def portrait_clip(self):
        image = self.sprites["walk"]
        return image, 16, image.h - 2 * self.FRAME_H + 20, 46, 38
