"""Pose the concept art's cut-out parts with joint angles taken from Blender actions.

    .venv\\Scripts\\python.exe tools/sprites/cutout_rig.py --rig assets/characters/rigs/hero_a.json
        --poses poses_lib1.json poses_lib2.json --out <dir> [--height 56]

The rig file names the parts sheet and, for every part, its box on the sheet and its joints
(sheet pixels): the art keeps its own proportions. The pose files (tools/blender/
export_pose2d.py) give, per frame, where the 3D body's joints land on screen; only the
ANGLES of each limb are used: torso hip->neck, head neck->top, upper arm shoulder->elbow,
forearm elbow->wrist, thigh hip->knee, shin knee->ankle, bat direction. Arms and legs are
split at the elbow / knee (with a little overlap so joints never open). Back limbs are drawn
behind and slightly darker. Each frame is shrunk to game size, outlined and stood on the
floor line of a 96x64 cell, like every other sheet (CHARACTER_SPEC.md).
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent))
import clean_concept as cc  # noqa: E402

CELL_W, CELL_H, FEET = 96, 64, 4
OVERLAP = 4                                          # px of the upper segment kept past the joint


def angle(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def rotate(v, rad):
    c, s = math.cos(rad), math.sin(rad)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


class Part:
    """One piece of art with named joints, cropped from the sheet (coordinates local to the crop)."""

    def __init__(self, sheet, box, joints, darken=1.0, keep=None):
        self.img = sheet.crop(box)
        if keep is not None:                               # keep only pixels where keep(x, y) is true
            px = self.img.load()
            for y in range(self.img.height):
                for x in range(self.img.width):
                    if not keep(x + box[0], y + box[1]):
                        px[x, y] = (0, 0, 0, 0)
        if darken != 1.0:
            alpha = self.img.getchannel("A")
            self.img = ImageEnhance.Brightness(self.img.convert("RGB")).enhance(darken).convert("RGBA")
            self.img.putalpha(alpha)
        self.joints = {k: (v[0] - box[0], v[1] - box[1]) for k, v in joints.items()}

    def draw(self, canvas, pivot, target, rad):
        """Rotate by rad (screen, clockwise positive) around joint pivot and put it at target."""
        # A square canvas big enough for any turn: a long part (the bat) is not clipped.
        w, h = self.img.size
        side = 2 * (w + h)
        big = Image.new("RGBA", (side, side))
        ox, oy = side // 2 - self.joints[pivot][0], side // 2 - self.joints[pivot][1]
        big.paste(self.img, (ox, oy))
        p = self.joints[pivot]
        centre = (p[0] + ox, p[1] + oy)
        rotated = big.rotate(-math.degrees(rad), resample=Image.NEAREST, center=centre)
        canvas.alpha_composite(rotated, (round(target[0] - centre[0]), round(target[1] - centre[1])))

    def joint_at(self, name, pivot, target, rad):
        off = (self.joints[name][0] - self.joints[pivot][0], self.joints[name][1] - self.joints[pivot][1])
        r = rotate(off, rad)
        return (target[0] + r[0], target[1] + r[1])


def split_limb(sheet, spec, darken):
    """Upper segment (to the middle joint, plus overlap) and lower segment of an arm or leg."""
    j = spec["joints"]
    top, mid, low = j[spec["chain"][0]], j[spec["chain"][1]], j[spec["chain"][2]]
    axis = (mid[0] - top[0], mid[1] - top[1])
    length = math.hypot(*axis)
    ux, uy = axis[0] / length, axis[1] / length

    def along(x, y):
        return (x - top[0]) * ux + (y - top[1]) * uy

    upper = Part(sheet, spec["box"], j, darken, keep=lambda x, y: along(x, y) <= length + OVERLAP)
    lower = Part(sheet, spec["box"], j, darken, keep=lambda x, y: along(x, y) > length - 1)
    return upper, lower


def build(rig, root):
    sheet = cc.key_out(Image.open(root / rig["sheet"]).convert("RGBA"), [255, 0, 255], 150)
    parts = {}
    for name, spec in rig["parts"].items():
        darken = spec.get("darken", 1.0)
        if "chain" in spec:
            parts[name + "_upper"], parts[name + "_lower"] = split_limb(sheet, spec, darken)
        else:
            parts[name] = Part(sheet, spec["box"], spec["joints"], darken)
    return parts


def pose_frame(parts, rig, pose, scale):
    """Forward kinematics from the hips; returns a big canvas and the hip position on it."""
    canvas = Image.new("RGBA", (900, 900))
    hip = (450 + pose["hip"][0] * scale, 600 + pose["hip"][1] * scale)
    torso = parts["torso"]
    a_torso = angle(pose["hip"], pose["neck"]) - angle(torso.joints["hip"], torso.joints["neck"])
    neck = torso.joint_at("neck", "hip", hip, a_torso)
    shoulder = torso.joint_at("shoulder", "hip", hip, a_torso)
    back_shoulder = torso.joint_at("back_shoulder", "hip", hip, a_torso)
    pack_at = torso.joint_at("pack", "hip", hip, a_torso)

    def limb(name, top_joint, mid_joint, low_joint, start, side):
        up, lo = parts[name + "_upper"], parts[name + "_lower"]
        a_up = angle(pose[f"{top_joint}_{side}"], pose[f"{mid_joint}_{side}"]) - angle(up.joints[top_joint], up.joints[mid_joint])
        mid = up.joint_at(mid_joint, top_joint, start, a_up)
        a_lo = angle(pose[f"{mid_joint}_{side}"], pose[f"{low_joint}_{side}"]) - angle(lo.joints[mid_joint], lo.joints[low_joint])
        return (up, top_joint, start, a_up), (lo, mid_joint, mid, a_lo)

    back_arm = limb("back_arm", "shoulder", "elbow", "wrist", back_shoulder, "l")
    back_leg = limb("back_leg", "hip", "knee", "ankle", (hip[0] - rig["hip_spread"], hip[1]), "l")
    front_leg = limb("front_leg", "hip", "knee", "ankle", (hip[0] + rig["hip_spread"], hip[1]), "r")
    front_arm = limb("front_arm", "shoulder", "elbow", "wrist", shoulder, "r")
    head = parts["head"]
    a_head = angle(pose["neck"], pose["head_top"]) - angle(head.joints["neck"], head.joints["top"])
    fore, fj, fstart, fa = front_arm[1]
    grip = fore.joint_at("grip", fj, fstart, fa)
    bat = parts["bat"]
    a_bat = math.atan2(pose["bat_dir"][1], pose["bat_dir"][0]) - angle(bat.joints["grip"], bat.joints["tip"])

    for p, j, at, a in (*back_arm, *back_leg):
        p.draw(canvas, j, at, a)
    parts["backpack"].draw(canvas, "attach", pack_at, a_torso)
    torso.draw(canvas, "hip", hip, a_torso)
    for p, j, at, a in front_leg:
        p.draw(canvas, j, at, a)
    head.draw(canvas, "neck", neck, a_torso * 0.0 + a_head)
    up, uj, ustart, ua = front_arm[0]
    up.draw(canvas, uj, ustart, ua)
    bat.draw(canvas, "grip", grip, a_bat)
    fore.draw(canvas, fj, fstart, fa)
    return canvas, hip


def to_cell(canvas, hip, scale_px):
    fig = canvas.crop(canvas.getbbox())
    bx, by = canvas.getbbox()[:2]
    small = fig.resize((max(1, round(fig.width * scale_px)), max(1, round(fig.height * scale_px))), Image.NEAREST)
    small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    pad = Image.new("RGBA", (small.width + 2, small.height + 2))
    pad.paste(small, (1, 1), small)
    sprite = cc.outline(pad)
    cell = Image.new("RGBA", (CELL_W, CELL_H))
    hip_x = (hip[0] - bx) * scale_px + 1
    cell.alpha_composite(sprite, (round(CELL_W / 2 - hip_x), CELL_H - FEET - sprite.height))
    return cell


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rig", required=True)
    ap.add_argument("--poses", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--height", type=int, default=56)
    ap.add_argument("--sheets", nargs="*", default=None)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    rig = json.loads(Path(args.rig).read_text(encoding="utf-8"))
    parts = build(rig, root)
    poses = {}
    for path in args.poses:
        poses.update(json.loads(Path(path).read_text(encoding="utf-8")))
    scale = rig["px_per_m"]
    # One shrink factor for every sheet: the first idle frame stands args.height px tall.
    idle, _ = pose_frame(parts, rig, poses["idle"][0], scale)
    shrink = (args.height - 2) / (idle.getbbox()[3] - idle.getbbox()[1])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for sheet, frames in poses.items():
        if args.sheets and sheet not in args.sheets:
            continue
        strip = Image.new("RGBA", (CELL_W * len(frames), CELL_H))
        for i, pose in enumerate(frames):
            canvas, hip = pose_frame(parts, rig, pose, scale)
            strip.alpha_composite(to_cell(canvas, hip, shrink), (i * CELL_W, 0))
        strip.save(out / f"{sheet}.png")
        print("saved", out / f"{sheet}.png", len(frames), "frames")


if __name__ == "__main__":
    main()
