"""Plan B2 (2026-11-20): our hero drawn in a Blender pose by Stable Diffusion that has learned him.

    C:\\Users\\doboh\\busan_ai\\.venv\\Scripts\\python.exe tools/ai/lora_pose.py --frames 1 2 --seeds 1 2 3

- The LoRA (C:\\Users\\doboh\\busan_ai\\lora_out) was trained on ~50 of the hero's own PixelLab
  pictures, each cropped to the figure and blown up to 512 px with the word "busanhero".
- The pose is the same Blender joints PixelLab got (pixellab_skeleton.py keypoints.json, 0..1 of
  the 64 px canvas), drawn as an OpenPose stick figure in the SAME framing as the training
  pictures (the standing figure's box plus a margin, made square), so the learned size fits.
- Back to dots: grey background off, shrunk to the figure's box, every pixel snapped to the
  standing picture's own colours, a 1 px outline closed, put back on the 64 px canvas.
Free models only (Stable Diffusion 1.5, ControlNet OpenPose), run on this computer.
"""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
CANVAS = 64
ORDER = ["NOSE", "NECK", "RIGHT SHOULDER", "RIGHT ELBOW", "RIGHT ARM", "LEFT SHOULDER", "LEFT ELBOW", "LEFT ARM",
         "RIGHT HIP", "RIGHT KNEE", "RIGHT LEG", "LEFT HIP", "LEFT KNEE", "LEFT LEG"]
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13), (1, 0)]
COLOURS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
           (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255)]
PROMPT = ("pixel art game sprite of busanhero, a young man with messy black hair, open ochre brown work jacket with "
          "rolled sleeves, white t-shirt, slate blue jeans, brown boots, high top-down view, plain grey background, "
          "two-handed overhead strike pose, facing {d}")
NEGATIVE = "blurry, photo, realistic, gradient, extra limbs, extra arms, text, watermark, frame, weapon, sword"


def frame_box(still, ox, oy, kps=()):
    """The training crop on the 64 px canvas: the figure's box plus 4 px, made square; widened to
    take in the pose's joints too (a raised weapon arm goes above the standing head)."""
    l, t, r, b = still.getchannel("A").getbbox()
    l, t, r, b = l + ox, t + oy, r + ox, b + oy
    for p in kps:
        x, y = p["x"] * CANVAS, p["y"] * CANVAS
        l, t, r, b = min(l, x - 2), min(t, y - 2), max(r, x + 2), max(b, y + 2)
    s = max(r - l, b - t) + 8
    cx, cy = (l + r) / 2, (t + b) / 2
    return cx - s / 2, cy - s / 2, s


def pose_picture(kps, box, size=512):
    bx, by, s = box
    img = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(img)
    at = {p["label"]: ((p["x"] * CANVAS - bx) / s * size, (p["y"] * CANVAS - by) / s * size) for p in kps}
    pts = [at.get(n) for n in ORDER]
    for i, (a, b) in enumerate(LIMBS):
        if pts[a] and pts[b]:
            d.line([pts[a], pts[b]], fill=COLOURS[i], width=10)
    for i, p in enumerate(pts):
        if p:
            d.ellipse((p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6), fill=COLOURS[i])
    return img


def to_dots(big, box, pal, outline):
    bx, by, s = box
    s_i = round(s)
    small = big.resize((s_i, s_i), Image.BOX).convert("RGB")
    out = Image.new("RGBA", (CANVAS, CANVAS))
    sp, op = small.load(), out.load()

    def snap(c):
        return min(pal, key=lambda p: (p[0] - c[0]) ** 2 * .3 + (p[1] - c[1]) ** 2 * .59 + (p[2] - c[2]) ** 2 * .11)
    for y in range(s_i):
        for x in range(s_i):
            r, g, b = sp[x, y]
            if abs(r - 128) < 22 and abs(g - 128) < 22 and abs(b - 128) < 22:       # the grey ground
                continue
            X, Y = round(bx) + x, round(by) + y
            if 0 <= X < CANVAS and 0 <= Y < CANVAS:
                op[X, Y] = snap((r, g, b)) + (255,)
    edge = []
    for y in range(CANVAS):
        for x in range(CANVAS):
            if not op[x, y][3] and any(0 <= x + dx < CANVAS and 0 <= y + dy < CANVAS and op[x + dx, y + dy][3]
                                       and op[x + dx, y + dy][:3] != outline for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge.append((x, y))
    for x, y in edge:
        op[x, y] = outline + (255,)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="hero_px40")
    ap.add_argument("--direction", default="south-east")
    ap.add_argument("--frames", type=int, nargs="+", default=[1, 2], help="indexes into keypoints.json")
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--lora", default="C:/Users/doboh/busan_ai/lora_out")
    ap.add_argument("--lora-scale", type=float, default=0.9)
    ap.add_argument("--pose", type=float, default=1.0)
    ap.add_argument("--steps", type=int, default=30)
    a = ap.parse_args()
    import torch
    from diffusers import ControlNetModel, StableDiffusionControlNetPipeline

    char = ROOT / "assets" / "characters" / a.character
    kps = json.loads((ROOT / "assets/characters/pixellab_downloads/hero_workjacket_40/Skeleton/chop" / a.direction
                      / "keypoints.json").read_text(encoding="utf-8"))
    still = Image.open(char / "Idle" / "rotations" / f"{a.direction}.png").convert("RGBA")
    ox, oy = (CANVAS - still.width) // 2, CANVAS - still.height - 6
    cnt = {}
    for p in still.getdata():
        if p[3] > 200:
            cnt[p[:3]] = cnt.get(p[:3], 0) + 1
    pal = [c for c, n in cnt.items() if n >= 3]
    outline = min(pal, key=sum)
    cn = ControlNetModel.from_pretrained("lllyasviel/control_v11p_sd15_openpose", torch_dtype=torch.float16)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5", controlnet=cn, torch_dtype=torch.float16,
        safety_checker=None, requires_safety_checker=False).to("cuda")
    pipe.load_lora_weights(a.lora)
    pipe.set_progress_bar_config(disable=True)
    out_dir = char / "LoRA_chop" / a.direction
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in a.frames:
        box = frame_box(still, ox, oy, kps[f])
        pose = pose_picture(kps[f], box)
        pose.save(out_dir / f"pose_{f}.png")
        for seed in a.seeds:
            big = pipe(PROMPT.format(d=a.direction.replace("-", " ")), negative_prompt=NEGATIVE, image=pose,
                       num_inference_steps=a.steps, guidance_scale=7.0, controlnet_conditioning_scale=a.pose,
                       cross_attention_kwargs={"scale": a.lora_scale},
                       generator=torch.Generator("cuda").manual_seed(seed)).images[0]
            big.save(out_dir / f"big_{f}_s{seed}.png")
            to_dots(big, box, pal, outline).save(out_dir / f"{f}_s{seed}.png")
            print("saved", f, seed)


if __name__ == "__main__":
    main()
