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
import urllib.error
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
    keyfile = Path.home() / "busan_ai" / "pixellab_secret.txt"   # or the user saves it in this file
    if not value and keyfile.exists():
        value = keyfile.read_text(encoding="utf-8").strip()
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


# PixelLab label -> the Blender joint whose movement it follows (face points follow the head)
FOLLOW = {"NECK": "neck", "RIGHT SHOULDER": "shoulder_r", "RIGHT ELBOW": "elbow_r", "RIGHT ARM": "wrist_r",
          "LEFT SHOULDER": "shoulder_l", "LEFT ELBOW": "elbow_l", "LEFT ARM": "wrist_l",
          "RIGHT HIP": "hip_r", "RIGHT KNEE": "knee_r", "RIGHT LEG": "ankle_r",
          "LEFT HIP": "hip_l", "LEFT KNEE": "knee_l", "LEFT LEG": "ankle_l",
          "NOSE": "head_top", "RIGHT EYE": "head_top", "LEFT EYE": "head_top",
          "RIGHT EAR": "head_top", "LEFT EAR": "head_top"}


ARMS = {"RIGHT ELBOW", "RIGHT ARM", "LEFT ELBOW", "LEFT ARM"}


def keypoints(base, idle, pose, k, arm_boost=1.0):
    """One frame: PixelLab's own skeleton of the standing picture (estimate-skeleton, 0..1 of the
    canvas, with depth), each point moved by how far its Blender joint moved from the idle pose.
    k = canvas fraction per Blender metre."""
    out = []
    for p in base:
        j = FOLLOW.get(p["label"])
        boost = arm_boost if p["label"] in ARMS else 1.0          # pose to read at 36 px: bigger arm moves
        dx, dy = ((pose[j][0] - idle[j][0]) * k * boost, (pose[j][1] - idle[j][1]) * k * boost) if j else (0.0, 0.0)
        out.append({"x": round(min(1, max(0, p["x"] + dx)), 4), "y": round(min(1, max(0, p["y"] + dy)), 4),
                    "label": p["label"], "z_index": int(round(p.get("z_index", 0)))})
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
    ap.add_argument("--guidance", type=float, default=6.0)
    ap.add_argument("--arm-boost", type=float, default=1.0, help="exaggerate arm moves (small sprites read better)")
    ap.add_argument("--tag", default="", help="suffix for the output names, to keep earlier tries")
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
    out = ROOT / a.out / a.action / a.direction
    out.mkdir(parents=True, exist_ok=True)
    est = char / "rig" / f"pixellab_skeleton_{a.direction}.json"      # PixelLab's skeleton of the still (0.1 use, once)
    if not est.exists():
        est.write_text(json.dumps(call("POST", "/estimate-skeleton", {"image": b64(ref)})["keypoints"]), encoding="utf-8")
    base = json.loads(est.read_text(encoding="utf-8"))
    J = rig["joints"]
    k = abs(J["head_top"][1] - J["ankle_r"][1]) / (abs(idle["head_top"][1] - idle["ankle_r"][1]) or 1) / CANVAS
    frames = [keypoints(base, idle, poses[a.action][i], k, a.arm_boost) for i in a.frames]
    (out / "keypoints.json").write_text(json.dumps(frames, indent=1), encoding="utf-8")
    if a.dry:
        from PIL import ImageDraw
        sheet = Image.new("RGBA", (CANVAS * 3 * 6, CANVAS * 6), (40, 40, 44, 255))
        for f, kps in enumerate(frames):
            sheet.alpha_composite(ref.resize((CANVAS * 6, CANVAS * 6), Image.NEAREST), (f * CANVAS * 6, 0))
            d = ImageDraw.Draw(sheet)
            for p in kps:
                x, y = f * CANVAS * 6 + p["x"] * CANVAS * 6, p["y"] * CANVAS * 6
                d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 80, 80))
        sheet.save(out / "keypoints_preview.png")
        print("dry run ->", out / "keypoints_preview.png")
        return
    # The account's free monthly generations are used first; dollars only after them, and the
    # account has no dollars or card, so nothing can be charged. If PixelLab refuses (no free use
    # left), stop and say so (2026-11-19 "그냥 실행하고 무료 끝났다고 하면 그만두면 되잖아").
    # "Freeze 1 -> generate 2": the first frame is the standing picture as it is (black mask = keep),
    # the other two are drawn in the poses (white mask = draw).
    black, white = Image.new("RGB", ref.size, (0, 0, 0)), Image.new("RGB", ref.size, (255, 255, 255))
    body = {"image_size": {"width": CANVAS, "height": CANVAS}, "view": "high top-down", "direction": a.direction,
            "reference_image": b64(ref), "skeleton_keypoints": frames, "guidance_scale": a.guidance,
            "inpainting_images": [b64(ref), None, None], "mask_images": [b64(black), b64(white), b64(white)]}
    try:
        res = call("POST", "/animate-with-skeleton", body)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"PixelLab refused ({e.code}): {e.read().decode(errors='replace')[:300]} - stopped, nothing paid")
    for i, img in enumerate(res.get("images", [])):
        Image.open(io.BytesIO(base64.b64decode(img["base64"]))).save(out / f"{a.frames[min(i, 2)]}_{i}{a.tag}.png")
    print("usage:", res.get("usage"), "->", out)


if __name__ == "__main__":
    main()
