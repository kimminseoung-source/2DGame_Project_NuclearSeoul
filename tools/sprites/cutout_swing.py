"""Our own skeleton animation tool (2026-11-19): pose a character picture's cut-out parts
with joint angles from a Blender action and shrink to game size, in the same folder layout as
a PixelLab export, so DirLook and find_hands read it unchanged.

    python tools/sprites/cutout_swing.py --rig assets/characters/rigs/hero_workjacket.json
        --poses assets/characters/hero_dot/_passes/poses_0.json --action chop
        --direction south-east --height 36 --out assets/characters/hero_concept/cutout_swing

Unlike tools/sprites/cutout_rig.py (the 2026-11-11 test it reuses: Part, split_limb, angle)
there is no backpack or held bat: weapons are drawn by the game at the hand (paper doll), so
this writes the hand of every frame too (<out>/hands.json, the grip joint) and the weapon's
direction from the action ("bat_dir") as <out>/weapon_dir.json.
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from cutout_rig import Part, angle, split_limb  # noqa: E402
import clean_concept as cc  # noqa: E402

FRAME = 64                       # output canvas, like PixelLab's animation frames


def load_sheet(root, rig):
    sheet = Image.open(root / rig["sheet"]).convert("RGBA")
    cut = rig.get("white_out")
    if cut:                                            # a white background becomes transparent
        px = sheet.load()
        for y in range(sheet.height):
            for x in range(sheet.width):
                r, g, b, a = px[x, y]
                if r > cut and g > cut and b > cut:
                    px[x, y] = (0, 0, 0, 0)
    return sheet


def build(rig, sheet):
    parts = {}
    for name, spec in rig["parts"].items():
        darken = spec.get("darken", 1.0)
        if "chain" in spec:
            parts[name + "_upper"], parts[name + "_lower"] = split_limb(sheet, spec, darken)
        else:
            parts[name] = Part(sheet, spec["box"], spec["joints"], darken)
    return parts


def pose_frame(parts, rig, pose, scale, size=2400):
    """Forward kinematics from the hips: (canvas, hip point, grip point)."""
    canvas = Image.new("RGBA", (size, size))
    hip = (size / 2 + pose["hip"][0] * scale, size * 0.75 + pose["hip"][1] * scale)
    torso = parts["torso"]
    a_torso = angle(pose["hip"], pose["neck"]) - angle(torso.joints["hip"], torso.joints["neck"])
    neck = torso.joint_at("neck", "hip", hip, a_torso)
    shoulder = torso.joint_at("shoulder", "hip", hip, a_torso)
    back_shoulder = torso.joint_at("back_shoulder", "hip", hip, a_torso)

    def limb(name, top, mid_j, low, start, side):
        up, lo = parts[name + "_upper"], parts[name + "_lower"]
        a_up = angle(pose[f"{top}_{side}"], pose[f"{mid_j}_{side}"]) - angle(up.joints[top], up.joints[mid_j])
        mid = up.joint_at(mid_j, top, start, a_up)
        a_lo = angle(pose[f"{mid_j}_{side}"], pose[f"{low}_{side}"]) - angle(lo.joints[mid_j], lo.joints[low])
        return (up, top, start, a_up), (lo, mid_j, mid, a_lo)

    back_arm = limb("back_arm", "shoulder", "elbow", "wrist", back_shoulder, "l")
    back_leg = limb("back_leg", "hip", "knee", "ankle", (hip[0] + rig["hip_spread"], hip[1]), "l")
    front_leg = limb("front_leg", "hip", "knee", "ankle", (hip[0] - rig["hip_spread"], hip[1]), "r")
    front_arm = limb("front_arm", "shoulder", "elbow", "wrist", shoulder, "r")
    head = parts["head"]
    a_head = angle(pose["neck"], pose["head_top"]) - angle(head.joints["neck"], head.joints["top"])
    fore, fj, fstart, fa = front_arm[1]
    grip = fore.joint_at("grip", fj, fstart, fa)

    for p, j, at, a in (*back_arm, *back_leg):
        p.draw(canvas, j, at, a)
    torso.draw(canvas, "hip", hip, a_torso)
    for p, j, at, a in front_leg:
        p.draw(canvas, j, at, a)
    head.draw(canvas, "neck", neck, a_head)
    for p, j, at, a in front_arm:
        p.draw(canvas, j, at, a)
    return canvas, hip, grip


def shrink(canvas, hip, grip, factor, feet_row):
    """Game-size frame on a FRAME x FRAME canvas, feet on feet_row; returns (frame, grip in frame px)."""
    box = canvas.getbbox()
    fig = canvas.crop(box)
    small = fig.resize((max(1, round(fig.width * factor)), max(1, round(fig.height * factor))), Image.BOX)
    small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    pad = Image.new("RGBA", (small.width + 2, small.height + 2))
    pad.paste(small, (1, 1), small)
    sprite = cc.outline(pad)
    frame = Image.new("RGBA", (FRAME, FRAME))
    hip_x = (hip[0] - box[0]) * factor + 1
    ox, oy = round(FRAME / 2 - hip_x), feet_row - sprite.height
    frame.alpha_composite(sprite, (ox, oy))
    gx = ox + 1 + (grip[0] - box[0]) * factor
    gy = oy + 1 + (grip[1] - box[1]) * factor
    return frame, [round(gx, 1), round(gy, 1)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rig", required=True)
    ap.add_argument("--poses", nargs="+", required=True)
    ap.add_argument("--action", default="chop")
    ap.add_argument("--direction", default="south-east")
    ap.add_argument("--height", type=int, default=36)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    rig = json.loads(Path(args.rig).read_text(encoding="utf-8"))
    parts = build(rig, load_sheet(root, rig))
    poses = {}
    for path in args.poses:
        poses.update(json.loads(Path(path).read_text(encoding="utf-8")))
    scale = rig["px_per_m"]
    idle, _, _ = pose_frame(parts, rig, poses["idle"][0], scale)
    ib = idle.getbbox()
    factor = (args.height - 2) / (ib[3] - ib[1])
    out = Path(args.out) / args.action / args.direction
    out.mkdir(parents=True, exist_ok=True)
    hands, dirs = [], []
    for i, pose in enumerate(poses[args.action]):
        canvas, hip, grip = pose_frame(parts, rig, pose, scale)
        frame, hand = shrink(canvas, hip, grip, factor, FRAME - 10)
        frame.save(out / f"{i}.png")
        hands.append(hand)
        bd = pose.get("bat_dir")
        dirs.append(round(math.degrees(math.atan2(-bd[1], bd[0])), 1) if bd else None)   # y up
    meta = Path(args.out)
    (meta / "hands.json").write_text(json.dumps({args.action: {args.direction: hands}}), encoding="utf-8")
    (meta / "weapon_dir.json").write_text(json.dumps({args.action: {args.direction: dirs}}), encoding="utf-8")
    print(f"{len(hands)} frames -> {out}")


if __name__ == "__main__":
    main()
