"""Make realistic ambient sounds and infected voices with Stable Audio Open (local, on the GPU).

Runs in its own environment (PyTorch + diffusers, about 4.4 GB, outside the project):

    C:\\Users\\doboh\\ai_tools\\stable_audio\\.venv\\Scripts\\python.exe tools/sounds/make_ambient_ai.py [name ...]

Needs a one-time Hugging Face login with the model's licence accepted
(https://huggingface.co/stabilityai/stable-audio-open-1.0). Writes assets/sounds/ai_<name>.wav
(44.1 kHz). Each recipe is a text prompt, a length and a fixed seed, so the same file comes back.
The game's short effects stay synthesized (make_sfx.py); this is for what synthesis can't do:
voices, wind with debris, distant crowds.
"""

import sys
from pathlib import Path

import soundfile
import torch
from diffusers import StableAudioPipeline

OUT = Path(__file__).resolve().parents[2] / "assets" / "sounds"
NEGATIVE = "music, melody, singing, speech, low quality, distortion"

RECIPES = {
    # name: (prompt, seconds, seed)
    "wind_ruins": ("cold wind blowing through a ruined empty city street, loose sheet metal rattling, "
                   "distant debris, desolate ambience", 20.0, 11),
    "siren_far": ("a single civil defense siren wailing very far away in an empty city, echoing", 15.0, 12),
    "subway_tunnel": ("dark empty subway tunnel ambience, low rumble, dripping water, distant metal creaks",
                      20.0, 13),
    "infected_groan_1": ("a sick zombie groaning and wheezing, raspy throat, close, horror creature", 3.0, 21),
    "infected_groan_2": ("a hoarse undead creature growling low and breathing heavily, horror", 3.0, 22),
    "infected_scream": ("a zombie shrieking as it spots its prey, short distorted scream, horror", 2.0, 23),
}


def main(names):
    pipe = StableAudioPipeline.from_pretrained("stabilityai/stable-audio-open-1.0", torch_dtype=torch.float16)
    pipe = pipe.to("cuda")
    OUT.mkdir(parents=True, exist_ok=True)
    for name in names or RECIPES:
        prompt, seconds, seed = RECIPES[name]
        audio = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=100, audio_end_in_s=seconds,
                     num_waveforms_per_prompt=1,
                     generator=torch.Generator("cuda").manual_seed(seed)).audios[0]
        soundfile.write(OUT / f"ai_{name}.wav", audio.T.float().cpu().numpy(), pipe.vae.sampling_rate)
        print("saved", f"ai_{name}", f"{seconds:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
