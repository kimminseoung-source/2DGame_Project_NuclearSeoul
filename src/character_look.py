"""How a character looks: draws a named pose at a point in time, whatever sprite sheets it uses.

Units ask for a pose ("idle", "walk", "sneak", "swing", "pickup", "hurt", "down", "crawl") and a
time; the look picks the frame. Looping poses take seconds, one-shot poses take
progress from 0 to 1. Every unit (hero, companions, zombies, hostile survivors) can use
the same calls, so swapping a character's art never touches the unit's code.

SheetLook reads the rendered sheets in assets/characters/<name>/ (see CHARACTER_SPEC.md):
one row per action, 96x64 cells facing right, feet 4 px above the cell bottom.
An optional look.json beside the sheets holds per-pose facts:
- "stride_m": metres the legs cover in one cycle of a walking pose. Given the distance the
  unit has walked, the leg cycle follows the ground, so feet never slide at any speed.
- "impact": the frame of an attack where the blow lands: {"swing": {"impact": 3}}. Given the attack's contact progress, the frames
before the impact play until the hit and the impact frame shows exactly when it lands
(and stays during the hit-stop); the rest play after. Any attack of any unit uses this.
  "hold": share of the time after the hit that the impact frame stays (default 0), so a fast
  blow is still seen landing: {"swing": {"impact": 2, "hold": 0.35}}.
  "windup": relative time of each frame before the impact (default even), so a big blow
  can hold its raised frame and then snap: {"swing3": {"impact": 4, "windup": [1, 1, 3, 0.5]}}.
  "trail_from": how many frames before the impact the swing trail starts (default 1).
An optional blade.json (written by tools/sprites/paint_clothes.py) holds the weapon in every
frame as [grip x, grip y, tip x, tip y] in cell pixels, so swing trails follow the blade.

LegacyLook wraps the first hand-drawn hero sheets so the old art keeps working.
"""

import json
from math import atan2, cos, sin
from pathlib import Path

import pico2d
import sdl2

from nav import PX_PER_M_X


LOOPING = {"idle", "walk", "sneak", "sneak_idle", "run", "crawl"}
# A pose a character's sheets lack falls back to a close one: (pose, fixed frame or None).
FALLBACK = {"sneak_idle": ("sneak", 0), "run": ("walk", None), "crawl": ("down", 4)}


class SheetLook:
    CELL_W, CELL_H = 96, 64
    SPRITE_PX_PER_M = 54 / 1.8       # render scale: a 1.8 m person is 54 px (CHARACTER_SPEC.md)
    FEET_FROM_BOTTOM = 4
    # Seconds per frame for looping poses.
    # Seconds per frame for looping poses that are not driven by distance (breathing idles).
    FRAME_TIME = {"idle": 0.55, "sneak_idle": 0.6, "walk": 0.13, "sneak": 0.17, "crawl": 0.17}
    # Head and torso of the first idle frame: (left, bottom, width, height) in the cell.
    PORTRAIT = (25, 23, 46, 36)

    def __init__(self, folder):
        self.sheets = {}
        for path in Path(folder).glob("*.png"):
            self.sheets[path.stem] = pico2d.load_image(str(path))
        meta = Path(folder) / "look.json"
        self.meta = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
        # Sheets drawn at another size (the 32 px dot look: "_size" in look.json, written by
        # render_character.py --size dot): its cells are shown at the world size of the 54 px
        # person, so on the dot canvas (settings.DOT) one sprite pixel is one canvas pixel.
        size = self.meta.get("_size")
        if size:
            k = size["person_px"] / 54                  # sprite px per world unit
            self.CELL_W, self.CELL_H = size["cell"]
            self.FEET_FROM_BOTTOM = size["feet"]
        else:
            k = 1.0
        self.k = k
        self.draw_w, self.draw_h = self.CELL_W / k, self.CELL_H / k
        blades = Path(folder) / "blade.json"
        self.blades = json.loads(blades.read_text(encoding="utf-8")) if blades.exists() else {}

    def has(self, pose):
        return pose in self.sheets

    def frame_count(self, pose):
        return self.sheets[pose].w // self.CELL_W

    def frame_of(self, pose, time, contact=None, distance=None):
        count = self.frame_count(pose)
        stride = self.meta.get(pose, {}).get("stride_m")
        if stride and distance is not None:
            # stride_m is measured on the model; the world uses PX_PER_M_X, the sheet its own
            # scale, so compare in pixels to keep the planted foot exactly still.
            cycles = distance * PX_PER_M_X / (stride * self.SPRITE_PX_PER_M)
            return int(cycles * count) % count
        if pose in LOOPING:
            return int(time / self.FRAME_TIME.get(pose, 0.12)) % count
        impact = self.meta.get(pose, {}).get("impact")
        if impact is not None and contact:
            # Wind-up frames fill the time before the hit, the rest the time after it.
            if time < contact:
                weights = self.meta.get(pose, {}).get("windup")
                if not weights or len(weights) != impact:
                    return min(impact - 1, int(time / contact * impact))
                left = time / contact * sum(weights)
                for index, weight in enumerate(weights):
                    left -= weight
                    if left < 0:
                        return index
                return impact - 1
            after = (time - contact) / max(1e-6, 1 - contact)
            hold = self.meta.get(pose, {}).get("hold", 0)
            if after < hold or impact + 1 >= count:
                return impact
            rest = (after - hold) / (1 - hold)
            return min(count - 1, impact + 1 + int(rest * (count - impact - 1)))
        return min(count - 1, max(0, int(time * count)))

    def blade_lines(self, pose, x, feet_y, facing):
        """The weapon in every frame of a pose as (grip, tip) screen points (None where the
        frame shows no weapon), or None when the sheets have no blade data for the pose."""
        lines = self.blades.get(pose)
        if not lines:
            return None
        k = self.k
        centre_y = feet_y - self.FEET_FROM_BOTTOM / k + self.draw_h / 2

        def screen(px, py):
            return x + (px - self.CELL_W / 2) / k * facing, centre_y + self.draw_h / 2 - py / k

        return [(screen(*line[:2]), screen(*line[2:])) if line else None for line in lines]

    def impact_of(self, pose):
        return self.meta.get(pose, {}).get("impact")

    def trail_from(self, pose):
        return self.meta.get(pose, {}).get("trail_from", 1)

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1.0, held=None, tint=None):
        """`held`: a weapon image (lying along +x, grip 2 px from its left end, middle row) drawn
        in the hand on the hand's line of this frame (blade.json), so any weapon fits any sheet.
        `tint`: (r, g, b) multiplied into the sprite (survivors borrow the hero's sheets)."""
        fixed = None
        if pose not in self.sheets:
            pose, fixed = FALLBACK.get(pose, ("idle", None))
            if pose not in self.sheets:
                pose, fixed = "idle", None
        image = self.sheets[pose]
        frame = self.frame_of(pose, time, contact, distance) if fixed is None else fixed
        y = feet_y - self.FEET_FROM_BOTTOM / self.k + self.draw_h / 2
        flip = "" if facing > 0 else "h"
        if alpha < 1:
            image.opacify(alpha)
        if tint is not None:
            sdl2.SDL_SetTextureColorMod(image.texture, *tint)
        image.clip_composite_draw(
            frame * self.CELL_W, 0, self.CELL_W, self.CELL_H, 0, flip,
            x, y, self.draw_w, self.draw_h,
        )
        if tint is not None:
            sdl2.SDL_SetTextureColorMod(image.texture, 255, 255, 255)
        if alpha < 1:
            image.opacify(1.0)
        if held is not None:
            self.draw_held(held, pose, frame, x, feet_y, facing)

    def draw_held(self, held, pose, frame, x, feet_y, facing):
        lines = self.blade_lines(pose, x, feet_y, facing)
        if not lines or frame >= len(lines) or lines[frame] is None:
            return
        (gx, gy), (tx, ty) = lines[frame]
        ang = atan2(ty - gy, tx - gx)
        w, h = held.w / self.k, held.h / self.k                 # its pixels are canvas pixels
        off = (held.w / 2 - 2) / self.k                         # image centre from the grip
        held.composite_draw(ang, "v" if cos(ang) < 0 else "", gx + cos(ang) * off, gy + sin(ang) * off, w, h)

    def portrait_clip(self):
        return (self.sheets["idle"], *self.PORTRAIT)


class LegacyLook:
    """The first hand-drawn hero: walk/sneak/action sheets with a left row and a right row."""

    MOVE_W, ACTION_W, FRAME_H = 77, 97, 58
    WALK_CYCLE = (1, 2, 3, 2)
    FRAME_TIME = {"walk": 0.12, "sneak": 0.15}
    SWING_EDGES = (0.5, 0.67, 0.8)     # wind-up, strike, follow-through, recovery as swing progress

    def __init__(self, sprites):
        self.sprites = sprites    # {"walk", "sneak", "action"} images

    def pick(self, pose, time):
        if pose == "sneak_idle":
            return "sneak", 0
        if pose == "run":
            pose = "walk"                       # the old art has no run; walk faster instead
        if pose in ("walk", "sneak"):
            step = int(time / self.FRAME_TIME[pose]) % len(self.WALK_CYCLE)
            return pose, self.WALK_CYCLE[step]
        if pose == "swing":
            # The bat's contact, follow-through and recovery frames.
            return "action", 1 + sum(time >= edge for edge in self.SWING_EDGES)
        if pose in ("pickup", "hurt", "down"):
            return "action", 0
        return "walk", 0

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1.0):
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
