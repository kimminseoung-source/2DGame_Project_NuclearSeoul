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
from math import atan2, cos, pi, radians, sin
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

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1.0, held=None, tint=None,
             angle=None):
        """`angle` is for 8-direction looks (DirLook); side sheets only turn left or right.
        `held`: a weapon image (lying along +x, grip 2 px from its left end, middle row) drawn
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
        if getattr(self, "flash", 0) > 0:                # struck: the same frame again, added on top (white)
            sdl2.SDL_SetTextureBlendMode(image.texture, sdl2.SDL_BLENDMODE_ADD)
            image.opacify(min(1.0, self.flash))
            image.clip_composite_draw(frame * self.CELL_W, 0, self.CELL_W, self.CELL_H, 0, flip, x, y, self.draw_w, self.draw_h)
            image.opacify(1.0)
            sdl2.SDL_SetTextureBlendMode(image.texture, sdl2.SDL_BLENDMODE_BLEND)
        if alpha < 1:
            image.opacify(1.0)
        if held is not None:
            self.draw_held(held, pose, frame, x, feet_y, facing)

    def draw_held(self, held, pose, frame, x, feet_y, facing):
        lines = self.blade_lines(pose, x, feet_y, facing)
        if not lines or frame >= len(lines) or lines[frame] is None:
            return
        (gx, gy), (tx, ty) = lines[frame]
        draw_weapon(held, gx, gy, atan2(ty - gy, tx - gx), self.k)

    def portrait_clip(self):
        return (self.sheets["idle"], *self.PORTRAIT)


def draw_weapon(held, gx, gy, ang, k):
    """A weapon picture (lying along +x, grip 2 px from its left end, middle row) with its grip at
    (gx, gy), pointing at `ang` (radians, y up). Its pixels are canvas pixels (k per world unit).
    Kept upright: turned past straight up or down it is flipped instead of shown upside down."""
    off = (held.w / 2 - 2) / k                                  # image centre from the grip
    held.composite_draw(ang, "v" if cos(ang) < 0 else "", gx + cos(ang) * off, gy + sin(ang) * off,
                        held.w / k, held.h / k)


DIRS = ("east", "north-east", "north", "north-west", "west", "south-west", "south", "south-east")
MOVING = ("walk", "run", "sneak")
BEHIND = {"north", "north-east", "north-west"}         # facing away: the weapon is behind the body
LEFT_HAND = {"south", "south-east", "south-west"}      # the weapon hand is on the picture's left


class DirLook:
    """An 8-direction character from a PixelLab export (2026-11-19, high top-down):
    <folder>/**/rotations/<dir>.png stills and <folder>/**/<animation>/<dir>/*.png frames.
    Standing and walking poses are drawn facing `angle` (world radians, 0 = east, y up); any
    pose it lacks (hurt, down, ...) is drawn by `base`, the older side sheets, so a character
    can move to the new art one animation at a time. No left/right mirroring: the hero's right
    arm becomes a blade, so all 8 directions are real pictures.

    Weapons are layered (paper doll): the body is empty-handed and the held weapon picture is
    stuck to the hand point of each frame (<folder>/hands.json, tools/sprites/find_hands.py),
    so one body serves every weapon. Until the body has its own swing frames, a blow keeps the
    standing picture and turns the weapon about the hand: a chop sweeps SWING_ARC either side of
    the aim, reaching its end at the hit; a stab thrusts THRUST px along the aim and back."""

    on = True                       # F4 "새 주인공 그림": off shows the old sheets for comparison
    FRAME_TIME = 0.1                # seconds per walking frame (until a stride is measured)
    BREATH_TIME = 0.6               # seconds per standing (breathing) picture, <folder>/Breath/<dir>/
    ONCE = ("hurt", "down", "pickup", "push", "roll")   # poses drawn by progress 0..1, not looped
    SWING_ARC = 1.05                # radians either side of the aim a chop sweeps (60 degrees)
    THRUST = 6                      # picture px a stab pushes the weapon forward
    HANG_OUT = 0.3                  # radians a carried weapon leans out from straight down

    def __init__(self, folder, base):
        from PIL import Image                          # only to find where the feet are
        self.base = base
        self.k = base.k                                # same pixel size as the rest of the world
        self.stills, self.anims = {}, {}
        for path in Path(folder).rglob("*.png"):
            d, parent = path.stem, path.parent
            if parent.name == "rotations" and d in DIRS:
                self.stills[d] = self._load(path, Image)
            elif parent.name in DIRS:
                pose = "walk" if "walk" in parent.parent.name.lower() else parent.parent.name.lower()
                self.anims.setdefault(pose, {}).setdefault(parent.name, []).append(path)
        self.named = {}                                # (animation, direction, frame name) -> picture
        for pose, by_dir in self.anims.items():
            for d, paths in by_dir.items():
                order = sorted(paths, key=lambda p: (0, int(p.stem), "") if p.stem.isdigit() else (1, 0, p.stem))
                by_dir[d] = [self._load(p, Image) for p in order]
                self.named.update({(pose, d, p.stem): pic for p, pic in zip(order, by_dir[d])})
        hands = Path(folder) / "hands.json"
        self.hands = json.loads(hands.read_text(encoding="utf-8")) if hands.exists() else {}
        keys = Path(folder) / "keyframes.json"
        self.keys = json.loads(keys.read_text(encoding="utf-8")) if keys.exists() else {}

    @staticmethod
    def _load(path, Image):
        alpha = Image.open(path).convert("RGBA").getchannel("A")
        box = alpha.getbbox() or (0, 0, alpha.width, alpha.height)
        return pico2d.load_image(str(path)), alpha.height - box[3]      # image, empty rows under the feet

    def __getattr__(self, name):                      # has, blade_lines, impact_of, ... come from the old sheets
        return getattr(self.base, name)

    def has(self, pose):
        """Aiming pictures (2026-11-20): "ready_stand_<style>" = Aim/, "ready_<style>" (stepping
        with the weapon raised) = AimStep/, for the weapon styles in keyframes.json "aim_styles"
        (a knife is not held like a bat). With the new pictures on, an aim it has no picture for
        is not taken from the old side sheets (they are another drawing); the hero then keeps
        its standing aim."""
        if self.on and self.stills and pose.startswith("ready_"):
            style = pose.rsplit("_", 1)[1]
            if style not in self.keys.get("aim_styles", []):
                return False
            return ("aim" if pose.startswith("ready_stand_") else "aimstep") in self.anims
        return self.base.has(pose)

    def has_dir(self, pose, angle):
        """Pictures of this pose (its own folder) for the direction `angle` faces."""
        return bool(self.on and self.anims.get(pose, {}).get(DIRS[round(angle / (pi / 4)) % 8]))

    def picture(self, pose, time, angle, contact=None):
        """(image, rows under the feet, hands key, direction, frame), or None for the old sheets."""
        if not self.on or angle is None or not self.stills:
            return None
        d = DIRS[round(angle / (pi / 4)) % 8]
        if pose.startswith("ready_"):                  # aiming: standing, or stepping with it raised
            key = "aim" if pose.startswith("ready_stand_") else "aimstep"
            frames = self.anims.get(key, {}).get(d)
            if frames:
                i = int(time / self.FRAME_TIME) % len(frames)
                return (*frames[i], key, d, i)
        own = self.anims.get(pose, {}).get(d)          # a folder named after the pose (Hurt/, Sneak/ ...)
        if own and pose not in ("walk", "run"):
            if pose in self.ONCE:                      # one-off: `time` is its progress 0..1
                i = min(len(own) - 1, int(time * len(own)))
            else:
                i = int(time / self.FRAME_TIME) % len(own)
            return (*own[i], pose, d, i)
        if pose in MOVING:
            frames = self.anims.get("walk", {}).get(d)
            if frames:
                i = int(time / self.FRAME_TIME) % len(frames)
                return (*frames[i], "walk", d, i)
        standing = pose in MOVING or pose in ("idle", "sneak_idle")
        breath = self.anims.get("breath", {}).get(d) if pose in ("idle", "sneak_idle") else None
        if breath:                                     # standing still: two breathing pictures in turn
            i = int(time / self.BREATH_TIME) % len(breath)
            return (*breath[i], "breath", d, i)
        if (standing or (contact is not None and self.hands)) and d in self.stills:
            return (*self.stills[d], "idle", d, 0)     # no walk yet: the standing picture glides
        return None

    key_poses = True                # F4: key-pose attacks on/off (off: standing picture + turning weapon)
    HIT_HOLD = 0.3                  # share of the time after the hit that the hit picture stays
    variant = None                  # F4 "공격 동작": a name in keyframes.json "variants" (None = the attack's own)
    key_count = 3                   # F4 "공격 장수": 2 (wind-up, hit), 3 (+ recover), 0 = every picture in turn

    def attack_table(self, pose):
        """Per-direction specs of this attack: the chosen variant's (to try motions in the game,
        docs/plans/2026-11-20_공격동작_바꿔가며_시연.md) or the attack's own."""
        name = self.variant or self.keys.get("default_variant")   # F4 choice, else the folder's own
        if pose == "chop" and name:
            table = self.keys.get("variants", {}).get(name)
            if table:
                return table
        return self.keys.get(pose, {})

    def variants(self):
        return list(self.keys.get("variants", {}))

    def key_pose(self, pose, time, contact, angle):
        """A key-pose attack (keyframes.json): the wind-up picture until the hit, the hit picture
        for HIT_HOLD of the rest, then the "recover" picture if the attack has one (3 key poses,
        2026-11-20), else None (back to standing). Returns (picture, hand, weapon
        radians) or None. Two pictures per direction: the slash trail, hit-stop, shake and flash
        carry the motion between them (docs/planning/MOTION_FEW_SPRITES_2026-11-19.md)."""
        if not (self.on and self.key_poses) or contact is None or angle is None:
            return None
        d = DIRS[round(angle / (pi / 4)) % 8]
        table = self.attack_table(pose)
        spec = table.get(d)
        if not spec:                                     # attacks have fewer directions: the nearest one
            i = DIRS.index(d)
            near = sorted((DIRS[(i + s) % 8] for s in (-1, 1)),
                          key=lambda n: abs((DIRS.index(n) * pi / 4 - angle + pi) % (2 * pi) - pi))
            d = next((n for n in near if n in table), None)
            if d is None:
                return None
            spec = table[d]
        after = (time - contact) / max(1e-6, 1 - contact)
        if self.key_count == 0 and "all" in spec:        # every picture: rest .. hit by the contact, then on
            seq, hit = spec["all"], spec.get("all_hit", spec["hit"]["frame"])
            i = round(time / contact * hit) if time < contact else hit + round(after * (len(seq) - 1 - hit))
            step = seq[max(0, min(i, len(seq) - 1))]
        elif time < contact:
            step = spec["windup"]
        elif after < self.HIT_HOLD:
            step = spec["hit"]
        elif "recover" in spec and self.key_count >= 3:  # third key pose: the weapon comes back
            step = spec["recover"]
        else:
            return None
        pic = self.named.get((step.get("anim", spec["anim"]), step.get("dir", d), str(step["frame"])))
        return (pic, step["hand"], radians(step["weapon"]), d) if pic else None

    def hand(self, key, d, i):
        points = self.hands.get(key, {}).get(d)
        return points[min(i, len(points) - 1)] if points else None

    def hang(self, d):
        """A carried weapon points down, leaning a little out to the side its hand is on."""
        if d == "east":
            out = 1
        elif d == "west":
            out = -1
        else:
            out = -1 if d in LEFT_HAND else 1
        return -pi / 2 + out * self.HANG_OUT

    def weapon_angle(self, pose, time, contact, angle, d):
        """Where the weapon points (radians, y up) and how far it is pushed along it (picture px)."""
        rest = self.hang(d)
        if contact is None or pose not in ("chop", "stab"):
            return rest, 0.0
        if pose == "stab":
            if time < contact:
                reach = time / contact
            else:
                reach = max(0.0, 1 - (time - contact) / max(1e-6, 1 - contact))
            return angle, self.THRUST * reach
        if time < contact:                               # sweep across the aim, ending at the hit
            return angle + self.SWING_ARC - 2 * self.SWING_ARC * (time / contact), 0.0
        after = (time - contact) / max(1e-6, 1 - contact)
        end = angle - self.SWING_ARC
        back = (rest - end + pi) % (2 * pi) - pi         # the short way back to hanging
        return end + back * min(1.0, after * 1.5), 0.0

    def draw(self, pose, time, x, feet_y, facing, contact=None, distance=None, alpha=1.0, held=None, tint=None,
             angle=None):
        keyed = self.key_pose(pose, time, contact, angle)
        if keyed:
            (image, under), point, fixed_ang, d = keyed
        else:
            pic = self.picture(pose, time, angle, contact)
            if pic is None:
                self.base.flash = getattr(self, "flash", 0)
                self.base.draw(pose, time, x, feet_y, facing, contact, distance, alpha, held, tint)
                return
            image, under, key, d, i = pic
            point, fixed_ang = self.hand(key, d, i), None
            held_at = self.keys.get("held_angles", {}).get(key, {}).get(d)
            if held_at:                                # the weapon's direction measured in Blender
                fixed_ang = radians(held_at[min(i, len(held_at) - 1)])
        w, h = image.w / self.k, image.h / self.k
        cy = feet_y - under / self.k + h / 2
        weapon, hand = None, None
        if point is not None:
            gx = x + (point[0] + 0.5 - image.w / 2) / self.k
            gy = cy + (image.h / 2 - point[1] - 0.5) / self.k
            hand = (gx, gy)
            if held is not None:
                if fixed_ang is not None:
                    ang, push = fixed_ang, 0.0
                else:
                    ang, push = self.weapon_angle(pose, time, contact, angle, d)
                weapon = (gx + cos(ang) * push / self.k, gy + sin(ang) * push / self.k, ang)
        if weapon and d in BEHIND:
            draw_weapon(held, *weapon, self.k)
        if alpha < 1:
            image.opacify(alpha)
        if tint is not None:
            sdl2.SDL_SetTextureColorMod(image.texture, *tint)
        image.draw(x, cy, w, h)
        if tint is not None:
            sdl2.SDL_SetTextureColorMod(image.texture, 255, 255, 255)
        if alpha < 1:
            image.opacify(1.0)
        if weapon and d not in BEHIND:
            draw_weapon(held, *weapon, self.k)
        return hand


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
