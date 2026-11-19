"""Key poses from Blender joints, redrawn by PixelLab's "animate with skeleton" (2026-11-19, plan A).

    .venv\\Scripts\\python.exe tools/sprites/pixellab_skeleton.py balance
    .venv\\Scripts\\python.exe tools/sprites/pixellab_skeleton.py make --action chop --frames 0 2 4 \\
        --direction south-east --out assets/characters/pixellab_downloads/hero_workjacket_40/Skeleton

Blender gives where each joint is in every frame (tools/blender/export_pose2d.py, seen from the
direction's camera). This turns three frames of that into PixelLab skeleton keypoints, fitted
onto our hero's standing picture (the joints marked in tools/animator: rig/<direction>.json),
and asks PixelLab to draw the hero in those poses. The pixels come from PixelLab, the motion
from Blender.

The API token is read from the user's PIXELLAB_SECRET environment variable; this script never
prints or stores it. Only free use: `balance` shows what the account has, and `make` stops when
it is zero (no paid use, 2026-11-19 "절대로 유료는 하지 마세요").
"""

import argparse
import base64
import io
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.pixellab.ai/v1"
CANVAS = 64
# Blender joint -> PixelLab label (OpenPose-like). "ARM" is the wrist, "LEG" the ankle.
LABELS = {"neck": "NECK", "shoulder_r": "RIGHT SHOULDER", "elbow_r": "RIGHT ELBOW", "wrist_r": "RIGHT ARM",
          "shoulder_l": "LEFT SHOULDER", "elbow_l": "LEFT ELBOW", "wrist_l": "LEFT ARM",
          "hip_r": "RIGHT HIP", "knee_r": "RIGHT KNEE", "ankle_r": "RIGHT LEG",
          "hip_l": "LEFT HIP", "knee_l": "LEFT KNEE", "ankle_l": "LEFT LEG"}


def secret():
    value = os.environ.get("PIXELLAB_SECRET")
    if not value and sys.platform == "win32":          # set with setx / user variables, not in this shell yet
        value = subprocess.run(["powershell", "-NoProfile", "-Command",
                                "[Environment]::GetEnvironmentVariable('PIXELLAB_SECRET','User')"],
                               capture_output=True, text=True).stdout.strip()
    if not value:
        raise SystemExit("PIXELLAB_SECRET is not set (the user sets it; this script never asks for it)")
    return value


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": "Bearer " + secret(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def b64(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return {"type": "base64", "base64": base64.b64encode(buf.getvalue()).decode()}


def keypoints(rig, idle, pose, ox, oy):
    """One frame's keypoints on the CANVAS: each joint = its place on the standing picture moved by
    how far the Blender joint moved from the idle pose (scaled from metres to picture px)."""
    J = rig["joints"]
    height_m = abs(idle["head_top"][1] - idle["ankle_r"][1]) or 1
    height_px = abs(J["head_top"][1] - J["ankle_r"][1]) or 1
    k = height_px / height_m
    out = []
    for joint, label in LABELS.items():
        x = J[joint][0] + (pose[joint][0] - idle[joint][0]) * k + ox
        y = J[joint][1] + (pose[joint][1] - idle[joint][1]) * k + oy
        out.append({"x": round(x, 1), "y": round(y, 1), "label": label, "z_index": 0})
    head = [J["head_top"][0] + (pose["head_top"][0] - idle["head_top"][0]) * k + ox,
            (J["head_top"][1] + J["neck"][1]) / 2 + (pose["head_top"][1] - idle["head_top"][1]) * k + oy]
    out.append({"x": round(head[0] + 2, 1), "y": round(head[1], 1), "label": "NOSE", "z_index": 0})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["balance", "make"])
    ap.add_argument("--character", default="hero_px40")
    ap.add_argument("--direction", default="south-east")
    ap.add_argument("--action", default="chop")
    ap.add_argument("--frames", type=int, nargs=3, default=[0, 2, 4])
    ap.add_argument("--out", default="assets/characters/pixellab_downloads/hero_workjacket_40/Skeleton")
    ap.add_argument("--dry", action="store_true", help="only write the keypoints and a picture of them")
    a = ap.parse_args()
    if a.what == "balance":
        print("balance:", call("GET", "/balance"))
        return
    char = ROOT / "assets" / "characters" / a.character
    rig = json.loads((char / "rig" / f"{a.direction}.json").read_text(encoding="utf-8"))
    poses = json.loads((char / "_passes" / f"poses_{a.direction}.json").read_text(encoding="utf-8"))
    still = Image.open(char / "Idle" / "rotations" / f"{a.direction}.png").convert("RGBA")
    ox, oy = (CANVAS - still.width) // 2, CANVAS - still.height - 6
    ref = Image.new("RGBA", (CANVAS, CANVAS))
    ref.alpha_composite(still, (ox, oy))
    idle = poses["idle"][0]
    frames = [keypoints(rig, idle, poses[a.action][i], ox, oy) for i in a.frames]
    out = ROOT / a.out / a.action / a.direction
    out.mkdir(parents=True, exist_ok=True)
    (out / "keypoints.json").write_text(json.dumps(frames, indent=1), encoding="utf-8")
    if a.dry:
        from PIL import ImageDraw
        sheet = Image.new("RGBA", (CANVAS * 3 * 6, CANVAS * 6), (40, 40, 44, 255))
        for f, kps in enumerate(frames):
            sheet.alpha_composite(ref.resize((CANVAS * 6, CANVAS * 6), Image.NEAREST), (f * CANVAS * 6, 0))
            d = ImageDraw.Draw(sheet)
            for p in kps:
                x, y = f * CANVAS * 6 + p["x"] * 6, p["y"] * 6
                d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 80, 80))
        sheet.save(out / "keypoints_preview.png")
        print("dry run ->", out / "keypoints_preview.png")
        return
    money = call("GET", "/balance")
    if not money or float(money.get("usd", 0)) <= 0:
        raise SystemExit(f"no free balance ({money}); stopping (no paid use)")
    body = {"image_size": {"width": CANVAS, "height": CANVAS}, "view": "high top-down", "direction": a.direction,
            "reference_image": b64(ref), "skeleton_keypoints": frames, "guidance_scale": 4.0}
    res = call("POST", "/animate-with-skeleton", body)
    for i, img in enumerate(res.get("images", [])):
        Image.open(io.BytesIO(base64.b64decode(img["base64"]))).save(out / f"{a.frames[min(i, 2)]}_{i}.png")
    print("usage:", res.get("usage"), "->", out)


if __name__ == "__main__":
    main()
