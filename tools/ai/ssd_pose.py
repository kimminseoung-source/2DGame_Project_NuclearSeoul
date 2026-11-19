"""Sprite Sheet Diffusion try (2026-11-20): our hero's standing picture + a Blender pose -> one frame.

    C:\\Users\\doboh\\busan_ai\\ssd\\.venv\\Scripts\\python.exe tools/ai/ssd_pose.py --frames 1 2 --seeds 1 2

Sprite Sheet Diffusion (MIT, github.com/chenganhsieh/Sprite-Sheet-Diffusion) is AnimateAnyone
fine-tuned on game sprites: a reference picture (who) and a pose picture (how) give a new frame of
the same character. Code: C:\\Users\\doboh\\busan_ai\\ssd\\code, weights: ...\\ssd\\weights.
The authors did not publish their pose module, so the original AnimateAnyone one (pose_guider.pth)
feeds the first layer and the deeper pose inputs get zeros.
Frames go back to dots the same way as lora_pose.py (same crop, the standing picture's colours).
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SSD = Path("C:/Users/doboh/busan_ai/ssd")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lora_pose as L  # noqa: E402  (pose picture, crop box, back to dots)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="hero_px40")
    ap.add_argument("--direction", default="south-east")
    ap.add_argument("--frames", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--steps", type=int, default=25)
    ap.add_argument("--cfg", type=float, default=3.5)
    a = ap.parse_args()

    sys.path.insert(0, str(SSD / "code" / "ModelTraining"))
    import torch
    from diffusers import AutoencoderKL, DDIMScheduler
    from omegaconf import OmegaConf
    from transformers import CLIPVisionModelWithProjection
    from models.pose_guider_org import PoseGuiderOrg
    from models.unet_2d_condition import UNet2DConditionModel
    from models.unet_3d import UNet3DConditionModel
    from pipelines.pipeline_pose2img import Pose2ImagePipeline

    W = SSD / "weights"
    from huggingface_hub import snapshot_download     # the local copy (from_pretrained_2d needs a folder)
    base = snapshot_download("stable-diffusion-v1-5/stable-diffusion-v1-5", allow_patterns=["unet/*", "*.json"])
    dt = torch.float16
    vae = AutoencoderKL.from_pretrained(W / "sd-vae-ft-mse").to("cuda", dtype=dt)
    ref_unet = UNet2DConditionModel.from_pretrained(base, subfolder="unet").to("cuda", dtype=dt)
    den_unet = UNet3DConditionModel.from_pretrained_2d(
        base, "", subfolder="unet",
        unet_additional_kwargs={"use_motion_module": False, "unet_use_temporal_attention": False}).to("cuda", dtype=dt)
    den_unet.load_state_dict(torch.load(W / "drive/denoising_unet-30000.pth", map_location="cpu", weights_only=True), strict=False)
    ref_unet.load_state_dict(torch.load(W / "drive/reference_unet-30000.pth", map_location="cpu", weights_only=True), strict=True)
    org = PoseGuiderOrg(conditioning_embedding_channels=320, block_out_channels=(16, 32, 96, 256))
    org.load_state_dict(torch.load(W / "pose_guider.pth", map_location="cpu", weights_only=True), strict=True)

    class Guider(torch.nn.Module):            # their unet wants a list: first layer + one per down block
        def __init__(self, g):
            super().__init__()
            self.g = g

        @property
        def dtype(self):
            return next(self.g.parameters()).dtype

        @property
        def device(self):                     # diffusers asks every part where it lives
            return next(self.g.parameters()).device

        def forward(self, x, ref=None):
            z = torch.zeros((1, 1, 1, 1, 1), device=x.device, dtype=x.dtype)
            return [self.g(x)] + [z] * 4

    guider = Guider(org).to("cuda", dtype=dt)
    enc = CLIPVisionModelWithProjection.from_pretrained(W / "image_encoder").to("cuda", dtype=dt)
    infer = OmegaConf.load(SSD / "code/ModelTraining/configs/inference/inference_v2.yaml")
    sched = DDIMScheduler(**OmegaConf.to_container(infer.noise_scheduler_kwargs))
    pipe = Pose2ImagePipeline(vae=vae, image_encoder=enc, reference_unet=ref_unet, denoising_unet=den_unet,
                              pose_guider=guider, scheduler=sched).to("cuda", dtype=dt)

    char = ROOT / "assets" / "characters" / a.character
    kps = json.loads((ROOT / "assets/characters/pixellab_downloads/hero_workjacket_40/Skeleton/chop" / a.direction
                      / "keypoints.json").read_text(encoding="utf-8"))
    still = Image.open(char / "Idle" / "rotations" / f"{a.direction}.png").convert("RGBA")
    ox, oy = (L.CANVAS - still.width) // 2, L.CANVAS - still.height - 6
    canvas = Image.new("RGBA", (L.CANVAS, L.CANVAS))
    canvas.alpha_composite(still, (ox, oy))
    cnt = {}
    for p in still.getdata():
        if p[3] > 200:
            cnt[p[:3]] = cnt.get(p[:3], 0) + 1
    pal = [c for c, n in cnt.items() if n >= 3]
    outline = min(pal, key=sum)
    out_dir = char / "SSD_chop" / a.direction
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in a.frames:
        box = L.frame_box(still, ox, oy, kps[f])
        bx, by, s = box
        crop = Image.new("RGBA", canvas.size, (128, 128, 128, 255))   # grey ground, like lora_pose
        crop.alpha_composite(canvas)
        ref = crop.crop((round(bx), round(by), round(bx) + round(s), round(by) + round(s))).convert("RGB")
        ref = ref.resize((512, 512), Image.NEAREST)
        pose = L.pose_picture(kps[f], box)
        ref_pose = L.pose_picture(kps[0], box)
        pose.save(out_dir / f"pose_{f}.png")
        for seed in a.seeds:
            img = pipe(ref, pose, ref_pose, 512, 512, a.steps, a.cfg,
                       generator=torch.manual_seed(seed)).images
            arr = (img[0, :, 0].permute(1, 2, 0).float().cpu().numpy() * 255).clip(0, 255).astype("uint8")
            big = Image.fromarray(arr)
            big.save(out_dir / f"big_{f}_s{seed}.png")
            L.to_dots(big, box, pal, outline).save(out_dir / f"{f}_s{seed}.png")
            print("saved", f, seed, flush=True)


if __name__ == "__main__":
    main()
