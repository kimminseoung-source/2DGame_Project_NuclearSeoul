"""Plan B (2026-11-19): redraw a key pose on this computer with free models, then back to dots.

Runs in its own environment (C:\\Users\\doboh\\busan_ai\\.venv: PyTorch CUDA, diffusers), not the
game's .venv:

    C:\\Users\\doboh\\busan_ai\\.venv\\Scripts\\python.exe tools/ai/redraw_pose.py --frames 2 4

For each frame:
1. init  = our animator's frame (tools/animator: the PixelLab hero's own pixels turned along
           the Blender pose, Tool_chop/<dir>/<n>.png), blown up 8x on a grey ground;
2. pose  = an OpenPose picture of the same Blender joints (pixellab_skeleton.py keypoints);
3. Stable Diffusion 1.5 + ControlNet OpenPose redraws it at low strength: the joints and seams
   the cut-out left are painted over while the colours and shape stay;
4. back to dots: shrunk to 64 px, every pixel snapped to the hero's own palette (the colours of
   the standing PixelLab picture), the cut-out's silhouette kept, a 1 px outline closed.
Models (free, downloaded once to the Hugging Face cache): stable-diffusion-v1-5 (CreativeML
OpenRAIL-M) and lllyasviel/control_v11p_sd15_openpose (Apache-2.0 / OpenRAIL).
"""

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
SCALE = 8
# COCO-18 order used by OpenPose pictures, from our keypoint labels (NOSE..LEFT LEG)
ORDER = ["NOSE", "NECK", "RIGHT SHOULDER", "RIGHT ELBOW", "RIGHT ARM", "LEFT SHOULDER", "LEFT ELBOW", "LEFT ARM",
         "RIGHT HIP", "RIGHT KNEE", "RIGHT LEG", "LEFT HIP", "LEFT KNEE", "LEFT LEG"]
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13), (1, 0)]
COLOURS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
           (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255)]
PROMPT = ("pixel art game sprite, young man with short black hair, open ochre brown canvas work jacket, white t-shirt, "
          "slate blue jeans, brown boots, swinging overhead with both hands, high top-down view, clean shapes, "
          "flat colours, plain grey background")
NEGATIVE = "blurry, photo, realistic, gradient, noise, extra limbs, extra arms, text, watermark, frame, weapon"


def pose_picture(kps, size):
    """OpenPose-style stick figure (black ground, coloured limbs) at `size` px."""
    img = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(img)
    at = {p["label"]: (p["x"] * SCALE, p["y"] * SCALE) for p in kps}
    pts = [at.get(name) for name in ORDER]
    for i, (a, b) in enumerate(LIMBS):
        if pts[a] and pts[b]:
            d.line([pts[a], pts[b]], fill=COLOURS[i % len(COLOURS)], width=12)
    for i, p in enumerate(pts):
        if p:
            d.ellipse((p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7), fill=COLOURS[i % len(COLOURS)])
    return img


def palette_of(img):
    cols = {}
    for r, g, b, a in img.getdata():
        if a > 200:
            cols[(r, g, b)] = cols.get((r, g, b), 0) + 1
    # only colours the picture really uses (3+ pixels): rare in-between shades let noise through
    return [c for c, n in sorted(cols.items(), key=lambda kv: -kv[1]) if n >= 3]


def snap(c, pal):
    return min(pal, key=lambda p: (p[0] - c[0]) ** 2 * 0.3 + (p[1] - c[1]) ** 2 * 0.59 + (p[2] - c[2]) ** 2 * 0.11)


def to_dots(big, shape, pal, outline):
    """Shrink the redrawn picture to the frame, keep the cut-out's silhouette, snap to the palette."""
    small = big.resize(shape.size, Image.BOX).convert("RGB")
    out = Image.new("RGBA", shape.size)
    sp, op, mp = small.load(), out.load(), shape.load()
    w, h = shape.size
    for y in range(h):
        for x in range(w):
            if mp[x, y][3] > 0:
                op[x, y] = snap(sp[x, y], pal) + (255,)
    for y in range(h):                                   # close the outline on the silhouette's edge
        for x in range(w):
            if op[x, y][3] and any(not (0 <= x + dx < w and 0 <= y + dy < h) or not op[x + dx, y + dy][3]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                if mp[x, y][:3] == outline:
                    op[x, y] = outline + (255,)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="hero_px40")
    ap.add_argument("--direction", default="south-east")
    ap.add_argument("--action", default="chop")
    ap.add_argument("--frames", type=int, nargs="+", default=[2, 4])
    ap.add_argument("--strength", type=float, default=0.3)
    ap.add_argument("--steps", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--pose", type=float, default=0.6, help="how strongly the pose picture steers (ControlNet)")
    a = ap.parse_args()
    import torch
    from diffusers import ControlNetModel, StableDiffusionControlNetImg2ImgPipeline

    char = ROOT / "assets" / "characters" / a.character
    kp_all = json.loads((ROOT / "assets/characters/pixellab_downloads/hero_workjacket_40/Skeleton" / a.action
                         / a.direction / "keypoints.json").read_text(encoding="utf-8"))
    kp_frames = {0: kp_all[0], 2: kp_all[1], 4: kp_all[2]}           # pixellab_skeleton.py --frames 0 2 4
    still = Image.open(char / "Idle" / "rotations" / f"{a.direction}.png").convert("RGBA")
    pal = palette_of(still)
    outline = pal[0] if sum(pal[0]) < 120 else min(pal, key=sum)
    cn = ControlNetModel.from_pretrained("lllyasviel/control_v11p_sd15_openpose", torch_dtype=torch.float16)
    pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5", controlnet=cn, torch_dtype=torch.float16,
        safety_checker=None, requires_safety_checker=False).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    out_dir = char / f"AI_{a.action}" / a.direction
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in a.frames:
        frame = Image.open(char / f"Tool_{a.action}" / a.direction / f"{n}.png").convert("RGBA")
        size = frame.width * SCALE
        ground = Image.new("RGBA", frame.size, (128, 128, 128, 255))
        ground.alpha_composite(frame)
        init = ground.convert("RGB").resize((size, size), Image.NEAREST)
        pose = pose_picture(kp_frames[n], size)
        g = torch.Generator("cuda").manual_seed(a.seed)
        big = pipe(PROMPT, negative_prompt=NEGATIVE, image=init, control_image=pose, strength=a.strength,
                   num_inference_steps=a.steps, guidance_scale=7.0, controlnet_conditioning_scale=a.pose,
                   generator=g).images[0]
        big.save(out_dir / f"{n}_big.png")
        pose.save(out_dir / f"{n}_pose.png")
        to_dots(big, frame, pal, outline).save(out_dir / f"{n}.png")
        print("saved", out_dir / f"{n}.png")


if __name__ == "__main__":
    main()
